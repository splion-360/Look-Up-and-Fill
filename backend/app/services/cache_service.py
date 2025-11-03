import pickle
from typing import Any

import redis
from pybktree import BKTree

from app.utils import (
    CACHE_TTL,
    DIST_THRESH,
    levenshtein_distance,
    setup_logger,
)


logger = setup_logger(__name__)


class Cache:
    def __init__(self, ttl_seconds: int = CACHE_TTL, test_mode: bool = False):
        self.ttl_seconds = ttl_seconds if not test_mode else 180
        self.test_mode = test_mode
        self.redis_client = redis.Redis(host="localhost", port=6379)
        self.bk_tree = None
        self.description_to_symbol = {}
        self._load_bk_tree_data()

    def _load_bk_tree_data(self):
        try:
            data = self.redis_client.get("bk_tree_descriptions")
            if data:
                self.description_to_symbol = pickle.loads(data)
                self._rebuild_bk_tree()
        except Exception:
            self.description_to_symbol = {}
            self._rebuild_bk_tree()

    def _rebuild_bk_tree(self):
        if self.description_to_symbol:
            self.bk_tree = BKTree(levenshtein_distance)
            for description in self.description_to_symbol.keys():
                self.bk_tree.add(description)
        else:
            self.bk_tree = BKTree(levenshtein_distance)

    def _save_bk_tree_data(self):
        try:
            data = pickle.dumps(self.description_to_symbol)
            self.redis_client.setex(
                "bk_tree_descriptions", self.ttl_seconds, data
            )
        except Exception as e:
            logger.error(f"Failed to save BK-tree data: {e}", "RED")

    def get_symbol_from_name(self, name: str) -> str | None:
        normalized_name = name.lower().strip()

        try:
            data = self.redis_client.get(f"name_results:{normalized_name}")
            if data:
                cached_results = pickle.loads(data)
                if cached_results:
                    return cached_results[0].get("symbol")
        except Exception:
            pass

        if self.bk_tree and len(self.description_to_symbol) > 0:
            matches = list(self.bk_tree.find(normalized_name, n=DIST_THRESH))
            if not matches:
                return

            best_match = min(matches, key=lambda x: x[0])
            distance, matched_description = best_match

            symbol = self.description_to_symbol.get(matched_description)
            if not symbol:
                return

            logger.info(
                f"Cache hit: {name} -> {matched_description} -> {symbol} (distance: {distance})",
                "WHITE",
            )

            try:
                cache_result = [
                    {
                        "symbol": symbol,
                        "description": matched_description,
                    }
                ]
                data = pickle.dumps(cache_result)
                self.redis_client.setex(
                    f"name_results:{normalized_name}",
                    self.ttl_seconds,
                    data,
                )
                logger.info(
                    f"Cached fuzzy match: {name} -> {symbol}",
                    "WHITE",
                )
            except Exception:
                pass

            return symbol

        return

    def get_name_from_symbol(self, symbol: str) -> str | None:
        normalized_symbol = symbol.upper().strip()
        try:
            data = self.redis_client.get(f"symbol_name:{normalized_symbol}")
            if data:
                return data.decode("utf-8")
        except Exception:
            pass
        return None

    def set_symbol_to_name(self, symbol: str, name: str):
        normalized_symbol = symbol.upper().strip()
        try:
            self.redis_client.setex(
                f"symbol_name:{normalized_symbol}",
                self.ttl_seconds,
                name.encode("utf-8"),
            )
            logger.info(f"Cached symbol->name: {symbol} -> {name}", "WHITE")
        except Exception as e:
            logger.error(f"Failed to cache symbol->name: {e}")

    def set_name_to_symbols(
        self, name: str, search_results: list[dict[str, Any]]
    ):
        normalized_name = name.lower().strip()

        try:
            data = pickle.dumps(search_results)
            self.redis_client.setex(
                f"name_results:{normalized_name}", self.ttl_seconds, data
            )

            for result in search_results:
                description = result.get("description", "").lower().strip()
                symbol = result.get("symbol", "")
                if description and symbol:
                    self.description_to_symbol[description] = symbol

            self._rebuild_bk_tree()
            self._save_bk_tree_data()
            logger.info(
                f"Cached name->symbols: {name} -> {len(search_results)} results",
                "WHITE",
            )
        except Exception as e:
            logger.error(f"Failed to cache name->symbols: {e}")

    def get_cache_stats(self) -> dict[str, Any]:
        try:
            symbol_keys = len(
                list(self.redis_client.scan_iter(match="symbol_name:*"))
            )
            name_keys = len(
                list(self.redis_client.scan_iter(match="name_results:*"))
            )
            return {
                "symbol_to_name_cache_size": symbol_keys,
                "name_to_results_cache_size": name_keys,
                "bk_tree_size": len(self.description_to_symbol),
                "ttl_seconds": self.ttl_seconds,
            }
        except Exception:
            return {
                "symbol_to_name_cache_size": 0,
                "name_to_results_cache_size": 0,
                "bk_tree_size": len(self.description_to_symbol),
                "ttl_seconds": self.ttl_seconds,
            }

    def clear_cache(self):
        try:
            symbol_keys = list(
                self.redis_client.scan_iter(match="symbol_name:*")
            )
            name_keys = list(
                self.redis_client.scan_iter(match="name_results:*")
            )
            bk_keys = ["bk_tree_descriptions"]

            all_keys = symbol_keys + name_keys + bk_keys
            if all_keys:
                self.redis_client.delete(*all_keys)

            self.description_to_symbol.clear()
            self._rebuild_bk_tree()
            logger.info("All caches cleared", "YELLOW")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")


company_cache = Cache()
test_cache = Cache(test_mode=True)
