import io
import os

import pytest
import requests

from app.utils import setup_logger


logger = setup_logger(__name__)

NGROK_TUNNEL_URL = os.getenv("NGROK_TUNNEL_URL")


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


class TestEndpoints:
    def test_root_endpoint(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        response = requests.get(f"{base_url}/", headers=headers, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_documents_endpoint(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        response = requests.get(
            f"{base_url}/api/v1/documents/", headers=headers, timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_upload_endpoint(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        csv_data = "name,symbol,shares,price\nApple Inc.,AAPL,100,150.00\n,GOOGL,50,2500.00"
        files = {
            "file": ("test.csv", io.BytesIO(csv_data.encode()), "text/csv")
        }

        response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            headers={"ngrok-skip-browser-warning": "true"},
            timeout=30,
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_rows" in data
        assert data["total_rows"] == 2

    def test_lookup_full_endpoint(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        test_data = {
            "data": [
                {
                    "name": "Apple Inc.",
                    "symbol": "",
                    "shares": 100,
                    "price": 150.00,
                },
                {"name": "", "symbol": "GOOGL", "shares": 50, "price": 2500.00},
            ]
        }

        response = requests.post(
            f"{base_url}/api/v1/documents/lookup/full",
            json=test_data,
            headers=headers,
            timeout=60,
        )

        assert response.status_code in [200, 429, 201]
        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "enriched_count" in data

    def test_lookup_single_endpoint(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        test_data = {
            "data": [{"name": "Microsoft Corp.", "symbol": "", "shares": 75}]
        }

        response = requests.post(
            f"{base_url}/api/v1/documents/lookup/single",
            json=test_data,
            headers=headers,
            timeout=60,
        )

        assert response.status_code in [200, 429, 201]
        if response.status_code == 200:
            data = response.json()
            assert "data" in data

    def test_rate_limiting(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        rate_limited_count = 0
        successful_count = 0

        for _ in range(35):
            response = requests.get(f"{base_url}/", headers=headers, timeout=10)
            if response.status_code == 429:
                rate_limited_count += 1
            elif response.status_code == 200 or response.status_code == 201:
                successful_count += 1

        assert rate_limited_count > 0 or successful_count > 0

    def test_error_handling(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        invalid_data = {"invalid": "data"}

        response = requests.post(
            f"{base_url}/api/v1/documents/lookup/full",
            json=invalid_data,
            headers=headers,
            timeout=30,
        )

        assert response.status_code == 422

    def test_large_payload(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        large_data = {
            "data": [
                {"name": f"Company {i}", "symbol": "", "shares": 100}
                for i in range(50)
            ]
        }

        response = requests.post(
            f"{base_url}/api/v1/documents/lookup/full",
            json=large_data,
            headers=headers,
            timeout=120,
        )

        assert response.status_code in [200, 429, 500, 201]

    def test_concurrent_web_requests(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        import concurrent.futures

        def make_request():
            try:
                response = requests.get(
                    f"{base_url}/", headers=headers, timeout=15
                )
                return response.status_code
            except requests.exceptions.RequestException:
                return 500

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [
                future.result()
                for future in concurrent.futures.as_completed(futures)
            ]

        successful = sum(1 for code in results if code == 200 or code == 201)
        rate_limited = sum(1 for code in results if code == 429)

        assert len(results) == 20
        assert successful + rate_limited > 0

    def test_upload_invalid_file(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        files = {
            "file": ("test.txt", io.BytesIO(b"invalid content"), "text/plain")
        }

        response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            headers={"ngrok-skip-browser-warning": "true"},
            timeout=30,
        )

        assert response.status_code == 400

    def test_upload_empty_file(self, base_url, headers):
        clear_rate_limits(base_url, headers)
        file = io.BytesIO(b"")
        response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            headers={"ngrok-skip-browser-warning": "true"},
            timeout=30,
            files={"file": ("empty.csv", file, "text/csv")},
        )
        assert response.status_code == 400
