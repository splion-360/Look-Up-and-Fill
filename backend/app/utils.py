import asyncio
import logging
import os
import pickle
import string
from functools import wraps
from typing import Literal

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException
from pybktree import BKTree
from pybloom_live import BloomFilter


load_dotenv()

#######################################################
############# GLOBAL CONSTANTS ########################
#######################################################

ENVIRONMENT = os.environ.get("ENVIRONMENT", "production")
FINNHUB_API_KEY = os.environ.get("FINNHUB_API_KEY")
CONCURRENCY_LIMIT = 5  # Number of thread-safe-non-blocking operations
BUCKET_CLEANUP_FREQ = 3600  # s Every hour
PORT = 8000  # Backend port
MAX_RETRIES = 3  # Number of times to hit the 3rd party API before yielding
REQUEST_PER_MINUTE = 30
CACHE_TTL = 300  # s 5 minutes
MAX_CACHE_CAPACITY = 1000
DIST_THRESH = 3  # Edit distance boundary for bk-tree to select candidates

LOG_COLORS = {
    "RED": "\033[31m",
    "GREEN": "\033[32m",
    "YELLOW": "\033[33m",
    "BLUE": "\033[34m",
    "MAGENTA": "\033[35m",
    "CYAN": "\033[36m",
    "WHITE": "\033[37m",
    "BRIGHT_RED": "\033[91m",
    "BRIGHT_GREEN": "\033[92m",
    "BRIGHT_YELLOW": "\033[93m",
    "RESET": "\033[0m",
}


#######################################################
############ LOGGING UTILITIES ########################
#######################################################

ColorType = Literal[
    "RED",
    "GREEN",
    "YELLOW",
    "BLUE",
    "MAGENTA",
    "CYAN",
    "WHITE",
    "BRIGHT_RED",
    "BRIGHT_GREEN",
    "BRIGHT_YELLOW",
]


class ColoredFormatter(logging.Formatter):
    def __init__(self, fmt: str):
        super().__init__(fmt)
        self.colors = {
            logging.DEBUG: "BRIGHT_YELLOW",
            logging.INFO: "GREEN",
            logging.WARNING: "YELLOW",
            logging.ERROR: "RED",
            logging.CRITICAL: "BRIGHT_RED",
        }

    def format(self, record):
        message = super().format(record)
        if hasattr(record, "custom_color") and record.custom_color:
            color = record.custom_color
        else:
            color = self.colors.get(record.levelno, "WHITE")
        return f"{LOG_COLORS[color]}{message}{LOG_COLORS['RESET']}"


class ColoredLogger:
    def __init__(self, logger: logging.Logger):
        self._logger = logger

    def info(self, message: str, color: ColorType = None):
        record = self._logger.makeRecord(
            self._logger.name, logging.INFO, "", 0, message, (), None
        )
        if color:
            record.custom_color = color
        self._logger.handle(record)

    def debug(self, message: str, color: ColorType = None):
        record = self._logger.makeRecord(
            self._logger.name, logging.DEBUG, "", 0, message, (), None
        )
        if color:
            record.custom_color = color
        self._logger.handle(record)

    def warning(self, message: str, color: ColorType = None):
        record = self._logger.makeRecord(
            self._logger.name, logging.WARNING, "", 0, message, (), None
        )
        if color:
            record.custom_color = color
        self._logger.handle(record)

    def error(self, message: str, color: ColorType = None):
        record = self._logger.makeRecord(
            self._logger.name, logging.ERROR, "", 0, message, (), None
        )
        if color:
            record.custom_color = color
        self._logger.handle(record)

    def __getattr__(self, name):
        return getattr(self._logger, name)


def setup_logger(name: str = __name__) -> ColoredLogger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return ColoredLogger(logger)

    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    formatter = ColoredFormatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.propagate = False

    return ColoredLogger(logger)


logger = setup_logger(__name__)

#######################################################
############ DOCUMENT SERVICE UTILITIES ###############
#######################################################


def get_header() -> dict[any]:
    if not FINNHUB_API_KEY:
        raise ValueError("Invalid API Key")

    headers = {}
    headers["X-Finnhub-Token"] = FINNHUB_API_KEY

    return headers


def retry_handler(max_retries: int = MAX_RETRIES):

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attepmt in range(max_retries + 1):
                try:
                    response = await func(*args, **kwargs)
                    return response

                except HTTPException as e:
                    if e.status_code == 429:
                        if attepmt > max_retries:
                            raise HTTPException(
                                500,
                                detail="Max retry limit reached. Unable to fetch data",
                            ) from e

                        wait_time = (2**attepmt) + 0.5
                        logger.warning(
                            f"Rate limit hit, retrying in {wait_time}s (attempt {attepmt + 1}/{max_retries + 1})"
                        )
                        await asyncio.sleep(wait_time)
                        continue

                except Exception as e:
                    raise HTTPException(500, detail="Retry failed") from e
            return

        return wrapper

    return decorator


def is_valid(text: str):
    """
    Check whether the given text is a valid ticker
    """
    if len(text) < 10 and text.isupper():
        return True

    return False


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Damerau-Levenshtein distance: minimum edits (insertions, deletions,
    substitutions, and transpositions) to convert one string to another.
    """
    len1, len2 = len(s1), len(s2)

    h = {}
    for char in s1 + s2:
        if char not in h:
            h[char] = 0

    maxdist = len1 + len2
    H = [[maxdist for _ in range(len2 + 2)] for _ in range(len1 + 2)]

    H[0][0] = maxdist
    for i in range(0, len1 + 1):
        H[i + 1][0] = maxdist
        H[i + 1][1] = i
    for j in range(0, len2 + 1):
        H[0][j + 1] = maxdist
        H[1][j + 1] = j

    for i in range(1, len1 + 1):
        db = 0
        for j in range(1, len2 + 1):
            k = h[s2[j - 1]]
            l = db
            if s1[i - 1] == s2[j - 1]:
                cost = 0
                db = j
            else:
                cost = 1
            H[i + 1][j + 1] = min(
                H[i][j] + cost,
                H[i + 1][j] + 1,
                H[i][j + 1] + 1,
                H[k][l] + (i - k - 1) + 1 + (j - l - 1),
            )
        h[s1[i - 1]] = i

    return H[len1 + 1][len2 + 1]


#######################################################
############ TYPO CORRECTION UTILITIES ###############
#######################################################


class Corpus:
    def __init__(self, file_dir: str = "data"):

        # Only going with US stock exchange as all other exchanges are limited for premium
        self.url = "https://finnhub.io/api/v1/stock/symbol?exchange=US"
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)

        self.filepath = os.path.join(file_dir, "company.txt")

    def is_built(self) -> bool:
        return os.path.exists(self.filepath)

    @staticmethod
    def _normalize(name: str) -> str | None:
        if not name:
            return ""

        translator = str.maketrans("", "", string.punctuation)
        normalized = name.lower().strip().translate(translator)
        normalized = " ".join(normalized.split())

        return normalized

    async def _fetch_all_companies(self) -> list[dict]:
        all_companies = []
        headers = get_header()

        try:
            async with httpx.AsyncClient(
                headers=headers, timeout=30.0
            ) as client:
                response = await client.get(self.url)
                response.raise_for_status()
                companies = response.json()
                all_companies.extend(companies)
        except Exception as e:
            logger.error(f"Failed to fetch companies: {e}")
            return []

        return all_companies

    async def build_corpus(self, force: bool = False) -> None:

        if not force and os.path.exists(self.filepath):
            logger.info("Corpus already exists. Skipping build.")
            return

        logger.info(f"Building company corpus and saving to {self.filepath}...")
        companies = await self._fetch_all_companies()

        if not companies:
            logger.error("No companies fetched. Cannot build corpus.")
            return

        valid_companies = 0

        with open(self.filepath, "w") as f:
            for company in companies:
                description = company.get("description", "")

                if description:
                    valid_companies += 1

                normalized = self._normalize(description)
                f.write(f"{normalized}\n")

        self._is_built = True
        logger.info(f"Corpus built with {valid_companies} companies")

    @staticmethod
    def load_corpus(filepath: str):
        if not os.path.exists(filepath):
            logger.error(f"File not found at {filepath}")

        with open(filepath, "r+") as f:
            companies = [line.strip() for line in f if line.strip()]

        return companies


class TypoChecker:
    def __init__(
        self,
        filepath: str = "data/company.txt",
        dist_thresh: float = DIST_THRESH,
    ):
        self.bk_tree = None
        self.bloom_filter = None
        self.map = {}
        self.bk_tree_file = "data/bk_tree.pkl"
        self.dist_thresh = dist_thresh

        self._load_corpus(filepath)

        if not self._load_from_cache():
            self._build_tree()
            self._save_to_cache()

    @staticmethod
    def _normalize_concatenate(name: str) -> str | None:
        if not name:
            return ""

        translator = str.maketrans("", "", string.punctuation)
        normalized = name.lower().strip().translate(translator)
        normalized = "".join(normalized.split())

        return normalized

    def _load_corpus(self, filepath: str):
        companies = Corpus.load_corpus(filepath)
        capacity = max(100_000, len(companies))

        self.bloom_filter = BloomFilter(capacity, error_rate=0.001)

        for company in companies:
            concatenated = self._normalize_concatenate(company)
            self.bloom_filter.add(concatenated)
            self.map[concatenated] = company

        logger.info(f"Loaded {len(companies)} companies into spell checker")

    def _load_from_cache(self) -> bool:

        if os.path.exists(self.bk_tree_file):
            try:
                with open(self.bk_tree_file, "rb") as f:
                    self.bk_tree = pickle.load(f)
                logger.info("BK-tree loaded from cache")
                return True
            except Exception as e:
                logger.error(f"Failed to load from cache: {e}")
                return False
        return False

    def _save_to_cache(self):

        try:
            with open(self.bk_tree_file, "wb") as f:
                pickle.dump(self.bk_tree, f)
            logger.info("BK-tree saved to cache")
        except Exception as e:
            logger.error(f"Failed to save to cache: {e}")

    def clear_cache(self):

        if os.path.exists(self.bk_tree_file):
            os.remove(self.bk_tree_file)

        logger.info("Cache file cleared")

    def _build_tree(self):
        if not self.map:
            logger.info("Corpus not loaded")
            return

        self.bk_tree = BKTree(levenshtein_distance)
        for key in self.map.keys():
            self.bk_tree.add(key)

    def requires_check(
        self, query: str, max_suggestions=5
    ) -> list[tuple[str, int]]:

        modified_query = self._normalize_concatenate(query)

        if self.bloom_filter and (modified_query in self.bloom_filter):
            logger.info("Query found. Not proceeding with the check", "BLUE")
            return []

        logger.info(f"Typo in {query}", "BRIGHT_YELLOW")
        if self.bk_tree and len(self.map) > 0:
            candidates = list(
                self.bk_tree.find(modified_query, n=self.dist_thresh)
            )
            if not candidates:
                return []

            suggestions = []
            for distance, name in candidates:
                original_name = self.map.get(name, name)
                suggestions.append((original_name, distance))

            suggestions.sort(key=lambda x: x[1])

            sliced_suggestions = suggestions[:max_suggestions]
            logger.info(f"Suggestions: {sliced_suggestions}", "BRIGHT_YELLOW")
            return sliced_suggestions

        return []


# Build corpus if it doesnt exist
corpus = Corpus("data")
if not corpus.is_built():
    logger.info("Corpus already exists. Not building again")
    asyncio.run(corpus.build_corpus())


typo_checker = TypoChecker()
