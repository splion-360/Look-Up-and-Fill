import glob
import io
import os
import statistics
import time

import pytest
import requests

from app.services.cache_service import test_cache
from app.utils import setup_logger


NGROK_TUNNEL_URL = os.getenv("NGROK_TUNNEL_URL")

logger = setup_logger(__name__)


@pytest.fixture
def base_url():
    return NGROK_TUNNEL_URL


@pytest.fixture
def headers():
    return {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true",
    }


def clear_rate_limits(base_url: str, headers: dict):
    try:
        response = requests.post(
            f"{base_url}/api/v1/documents/_private/rl/reset",
            headers=headers,
            timeout=10,
        )
        if response.status_code == 200:
            logger.info("Rate limits cleared successfully", "GREEN")
        else:
            logger.warning(
                f"Failed to clear rate limits: {response.status_code}", "YELLOW"
            )
    except Exception as e:
        logger.warning(f"Error clearing rate limits: {e}", "YELLOW")


class AssetTestMetrics:
    def __init__(self):
        self.upload_times = []
        self.lookup_times = []
        self.upload_success = 0
        self.upload_failures = 0
        self.lookup_success = 0
        self.lookup_failures = 0
        self.enrichment_stats = []

    def add_upload_result(self, response_time, success, enriched_count=0):
        self.upload_times.append(response_time)
        if success:
            self.upload_success += 1
            self.enrichment_stats.append(enriched_count)
        else:
            self.upload_failures += 1

    def add_lookup_result(self, response_time, success):
        self.lookup_times.append(response_time)
        if success:
            self.lookup_success += 1
        else:
            self.lookup_failures += 1

    def get_summary(self):
        upload_times = self.upload_times if self.upload_times else [0]
        lookup_times = self.lookup_times if self.lookup_times else [0]

        return {
            "upload_stats": {
                "total_tests": len(self.upload_times),
                "success_rate": (
                    (self.upload_success / len(self.upload_times) * 100)
                    if self.upload_times
                    else 0
                ),
                "avg_time_ms": statistics.mean(upload_times) * 1000,
                "p95_time_ms": (
                    statistics.quantiles(upload_times, n=20)[18] * 1000
                    if len(upload_times) > 1
                    else upload_times[0] * 1000
                ),
                "total_enrichments": sum(self.enrichment_stats),
            },
            "lookup_stats": {
                "total_tests": len(self.lookup_times),
                "success_rate": (
                    (self.lookup_success / len(self.lookup_times) * 100)
                    if self.lookup_times
                    else 0
                ),
                "avg_time_ms": statistics.mean(lookup_times) * 1000,
                "p95_time_ms": (
                    statistics.quantiles(lookup_times, n=20)[18] * 1000
                    if len(lookup_times) > 1
                    else lookup_times[0] * 1000
                ),
            },
        }


class TestAssetsPerformance:
    def test_multi_file_uploads(self, base_url):
        clear_rate_limits(base_url, {"ngrok-skip-browser-warning": "true"})

        metrics = AssetTestMetrics()
        csv_files = glob.glob("tests/examples/*.csv")

        logger.info(
            f"Testing {len(csv_files)} CSV files for upload performance", "CYAN"
        )

        for csv_file in csv_files:
            filename = os.path.basename(csv_file)
            logger.info(f"Testing upload: {filename}", "BLUE")

            try:
                with open(csv_file) as f:
                    csv_content = f.read()

                files = {
                    "file": (
                        filename,
                        io.BytesIO(csv_content.encode()),
                        "text/csv",
                    )
                }

                start_time = time.time()
                response = requests.post(
                    f"{base_url}/api/v1/documents/upload",
                    files=files,
                    headers={"ngrok-skip-browser-warning": "true"},
                    timeout=60,
                )
                end_time = time.time()

                success = response.status_code == 200
                enriched_count = 0

                if success:
                    data = response.json()
                    enriched_count = data.get("total_rows", 0)
                    logger.info(
                        f"{filename}: {response.status_code} - {enriched_count} rows",
                        "GREEN",
                    )
                else:
                    logger.info(f"{filename}: {response.status_code}", "RED")

                metrics.add_upload_result(
                    end_time - start_time, success, enriched_count
                )
                time.sleep(1)

            except Exception as e:
                logger.error(f"Error testing {filename}: {e}", "RED")
                metrics.add_upload_result(0, False)

        summary = metrics.get_summary()
        upload_stats = summary["upload_stats"]

        logger.info(
            f"Total Files Tested: {upload_stats['total_tests']}", "GREEN"
        )
        logger.info(
            f"Success Rate: {upload_stats['success_rate']:.1f}%", "GREEN"
        )
        logger.info(
            f"Average Upload Time: {upload_stats['avg_time_ms']:.2f}ms", "BLUE"
        )
        logger.info(
            f"P95 Upload Time: {upload_stats['p95_time_ms']:.2f}ms", "BLUE"
        )
        logger.info(
            f"Total Rows Processed: {upload_stats['total_enrichments']}",
            "MAGENTA",
        )

        assert len(csv_files) > 0
        assert upload_stats["total_tests"] == len(csv_files)

    def test_mutli_file_lookup(self, base_url, headers):
        clear_rate_limits(base_url, headers)

        metrics = AssetTestMetrics()
        csv_files = glob.glob("tests/examples/*.csv")

        logger.info(
            f"Testing {len(csv_files)} CSV files for lookup performance", "CYAN"
        )

        for csv_file in csv_files:
            filename = os.path.basename(csv_file)

            if filename in ["empty_file.csv", "headers_only.csv"]:
                logger.info(
                    f"Skipping {filename} - no data for lookup test", "YELLOW"
                )
                continue

            logger.info(f"Testing lookup: {filename}", "BLUE")

            try:
                import pandas as pd

                df = pd.read_csv(csv_file)

                if df.empty:
                    logger.info(
                        f"Skipping {filename} - empty dataframe", "YELLOW"
                    )
                    continue

                df = df.fillna("")
                test_data = {"data": df.head(5).to_dict("records")}

                start_time = time.time()
                response = requests.post(
                    f"{base_url}/api/v1/documents/lookup/full",
                    json=test_data,
                    headers=headers,
                    timeout=120,
                )
                end_time = time.time()

                success = response.status_code in [200, 429]

                if response.status_code == 200:
                    data = response.json()
                    enriched = data.get("enriched_count", 0)
                    logger.info(
                        f"{filename}: {response.status_code} - {enriched} enriched",
                        "GREEN",
                    )
                elif response.status_code == 429:
                    logger.info(f"{filename}: Rate limited", "YELLOW")
                else:
                    logger.info(f"{filename}: {response.status_code}", "RED")

                metrics.add_lookup_result(end_time - start_time, success)
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error testing lookup for {filename}: {e}", "RED")
                metrics.add_lookup_result(0, False)

        summary = metrics.get_summary()
        lookup_stats = summary["lookup_stats"]

        logger.info(
            f"Total Files Tested: {lookup_stats['total_tests']}", "GREEN"
        )
        logger.info(
            f"Success Rate: {lookup_stats['success_rate']:.1f}%", "GREEN"
        )
        logger.info(
            f"Average Lookup Time: {lookup_stats['avg_time_ms']:.2f}ms", "BLUE"
        )
        logger.info(
            f"P95 Lookup Time: {lookup_stats['p95_time_ms']:.2f}ms", "BLUE"
        )

        assert lookup_stats["total_tests"] > 0

    def test_special_cases(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        time.sleep(1)

        special_files = [
            "special_characters.csv",
            "international_companies.csv",
            "mixed_case_names.csv",
            "mixed_valid_invalid.csv",
        ]

        logger.info("Testing special case datasets", "CYAN")

        results = {}

        for filename in special_files:
            filepath = f"tests/examples/{filename}"
            if not os.path.exists(filepath):
                continue

            try:
                import pandas as pd

                df = pd.read_csv(filepath)
                df = df.fillna("")
                test_data = {"data": df.head(3).to_dict("records")}

                start_time = time.time()
                response = requests.post(
                    f"{base_url}/api/v1/documents/lookup/full",
                    json=test_data,
                    headers=headers,
                    timeout=90,
                )
                end_time = time.time()

                response_time = (end_time - start_time) * 1000

                if response.status_code == 200:
                    data = response.json()
                    enriched = data.get("enriched_count", 0)
                    results[filename] = {
                        "status": 200,
                        "time_ms": response_time,
                        "enriched": enriched,
                    }
                    logger.info(
                        f"{filename}: {enriched} enriched in {response_time:.2f}ms",
                        "GREEN",
                    )
                else:
                    results[filename] = {
                        "status": response.status_code,
                        "time_ms": response_time,
                        "enriched": 0,
                    }
                    logger.info(
                        f"{filename}: Status {response.status_code}", "YELLOW"
                    )

                time.sleep(2)

            except Exception as e:
                logger.error(f"Error testing {filename}: {e}", "RED")
                results[filename] = {"status": 0, "time_ms": 0, "enriched": 0}

        total_enriched = sum(r["enriched"] for r in results.values())
        avg_time = (
            statistics.mean(
                [r["time_ms"] for r in results.values() if r["time_ms"] > 0]
            )
            if results
            else 0
        )

        logger.info(f"Total Enrichments: {total_enriched}", "MAGENTA")
        logger.info(f"Average Response Time: {avg_time:.2f}ms", "BLUE")

        assert len(results) > 0


class TestCache:
    def test_cache_symbol_to_name(self):
        test_cache.clear_cache()

        test_cache.set_symbol_to_name("AAPL", "Apple Inc.")
        cached_name = test_cache.get_name_from_symbol("AAPL")

        assert cached_name == "Apple Inc."

        cached_name_lower = test_cache.get_name_from_symbol("aapl")
        assert cached_name_lower == "Apple Inc."

        non_existent = test_cache.get_name_from_symbol("NONEXISTENT")
        assert non_existent is None

        test_cache.clear_cache()

    def test_cache_name_to_symbols(self):
        test_cache.clear_cache()

        search_results = [
            {"symbol": "AAPL", "description": "Apple Inc."},
            {"symbol": "AAPL.SW", "description": "Apple Swiss"},
            {"symbol": "AAPL.MX", "description": "Apple Mexico"},
            {"symbol": "AAPL.DE", "description": "Apple German Xetra"},
            {"symbol": "AAPL.BA", "description": "Apple Buenos Aires"},
            {"symbol": "AAPL.F", "description": "Apple Frankfurt"},
            {"symbol": "AAPL.MI", "description": "Apple Milan"},
            {"symbol": "AAPL.TI", "description": "Apple Italian Exchange"},
            {"symbol": "AAPL.BE", "description": "Apple Berlin"},
            {"symbol": "AAPL.VI", "description": "Apple Vienna"},
            {"symbol": "AAPL.L", "description": "Apple London"},
            {"symbol": "AAPL.PA", "description": "Apple Paris"},
            {"symbol": "AAPL.AS", "description": "Apple Amsterdam"},
            {"symbol": "AAPL.TRT", "description": "Apple Turkey"},
        ]

        test_cache.set_name_to_symbols("Apple Inc.", search_results)
        cached_symbol = test_cache.get_symbol_from_name("apple")

        assert cached_symbol == "AAPL"

        cached_symbol_lower = test_cache.get_symbol_from_name("apple turkey")
        assert cached_symbol_lower == "AAPL.TRT"

        test_cache.clear_cache()

    def test_cache_stats(self):
        test_cache.clear_cache()

        stats = test_cache.get_cache_stats()
        assert stats["symbol_to_name_cache_size"] == 0
        assert stats["name_to_results_cache_size"] == 0
        assert stats["bk_tree_size"] == 0

        test_cache.set_symbol_to_name("TSLA", "Tesla Inc.")
        test_cache.set_name_to_symbols(
            "Tesla Inc.", [{"symbol": "TSLA", "description": "Tesla Inc."}]
        )

        stats = test_cache.get_cache_stats()
        assert stats["symbol_to_name_cache_size"] == 1
        assert stats["name_to_results_cache_size"] == 1
        assert stats["bk_tree_size"] == 1

        test_cache.clear_cache()

    def test_cache_clear(self):
        test_cache.set_symbol_to_name("TEST", "Test Company")
        test_cache.set_name_to_symbols(
            "Test Company", [{"symbol": "TEST", "description": "Test Company"}]
        )

        stats_before = test_cache.get_cache_stats()
        assert stats_before["symbol_to_name_cache_size"] > 0

        test_cache.clear_cache()

        stats_after = test_cache.get_cache_stats()
        assert stats_after["symbol_to_name_cache_size"] == 0
        assert stats_after["name_to_results_cache_size"] == 0
        assert stats_after["bk_tree_size"] == 0

    def test_cache_multiple_results(self):
        test_cache.clear_cache()

        search_results = [
            {"symbol": "GOOGL", "description": "Alphabet Inc. Class A"},
            {"symbol": "GOOG", "description": "Alphabet Inc. Class C"},
        ]

        test_cache.set_name_to_symbols("Alphabet Inc.", search_results)
        cached_symbol = test_cache.get_symbol_from_name("Alphabet Inc.")

        assert cached_symbol in ["GOOGL", "GOOG"]

        test_cache.clear_cache()

    def test_cache_edge_cases(self):
        test_cache.clear_cache()

        empty_result = test_cache.get_symbol_from_name("")
        assert empty_result is None

        none_result = test_cache.get_name_from_symbol("")
        assert none_result is None

        test_cache.set_name_to_symbols("Test", [])
        empty_cache_result = test_cache.get_symbol_from_name("Test")
        assert empty_cache_result is None

        test_cache.clear_cache()
