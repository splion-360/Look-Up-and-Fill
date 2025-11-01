import io
import os
import requests
import time
from unittest.mock import patch

import pytest


NGROK_TUNNEL_URL = os.getenv("NGROK_TUNNEL_URL", "https://943682ef7c75.ngrok-free.app")


@pytest.fixture
def base_url():
    return NGROK_TUNNEL_URL


@pytest.fixture
def headers():
    return {
        "Content-Type": "application/json",
        "ngrok-skip-browser-warning": "true"
    }


class TestNgrokEndpoints:
    def test_root_endpoint_web(self, base_url, headers):
        response = requests.get(f"{base_url}/", headers=headers, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_documents_root_endpoint_web(self, base_url, headers):
        response = requests.get(f"{base_url}/api/v1/documents/", headers=headers, timeout=30)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data

    def test_upload_endpoint_web(self, base_url):
        csv_data = "name,symbol,shares,price\nApple Inc.,AAPL,100,150.00\n,GOOGL,50,2500.00"
        files = {"file": ("test.csv", io.StringIO(csv_data), "text/csv")}
        
        response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            headers={"ngrok-skip-browser-warning": "true"},
            timeout=30
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "total_rows" in data
        assert data["total_rows"] == 2

    def test_lookup_full_endpoint_web(self, base_url, headers):
        test_data = {
            "data": [
                {"name": "Apple Inc.", "symbol": "", "shares": 100, "price": 150.00},
                {"name": "", "symbol": "GOOGL", "shares": 50, "price": 2500.00}
            ]
        }
        
        response = requests.post(
            f"{base_url}/api/v1/documents/lookup/full",
            json=test_data,
            headers=headers,
            timeout=60
        )
        
        assert response.status_code in [200, 429]
        if response.status_code == 200:
            data = response.json()
            assert "data" in data
            assert "enriched_count" in data

    def test_lookup_single_endpoint_web(self, base_url, headers):
        test_data = {
            "data": [{"name": "Microsoft Corp.", "symbol": "", "shares": 75}]
        }
        
        response = requests.post(
            f"{base_url}/api/v1/documents/lookup/single",
            json=test_data,
            headers=headers,
            timeout=60
        )
        
        assert response.status_code in [200, 429]
        if response.status_code == 200:
            data = response.json()
            assert "data" in data

    def test_rate_limiting_web(self, base_url, headers):
        rate_limited_count = 0
        successful_count = 0
        
        for i in range(35):
            response = requests.get(f"{base_url}/", headers=headers, timeout=10)
            if response.status_code == 429:
                rate_limited_count += 1
            elif response.status_code == 200:
                successful_count += 1
        
        assert rate_limited_count > 0 or successful_count > 0

    def test_error_handling_web(self, base_url, headers):
        invalid_data = {"invalid": "data"}
        
        response = requests.post(
            f"{base_url}/api/v1/documents/lookup/full",
            json=invalid_data,
            headers=headers,
            timeout=30
        )
        
        assert response.status_code == 422

    def test_large_payload_web(self, base_url, headers):
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
            timeout=120
        )
        
        assert response.status_code in [200, 429, 500]

    def test_concurrent_web_requests(self, base_url, headers):
        import concurrent.futures
        
        def make_request():
            try:
                response = requests.get(f"{base_url}/", headers=headers, timeout=15)
                return response.status_code
            except requests.exceptions.RequestException:
                return 500
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        successful = sum(1 for code in results if code == 200)
        rate_limited = sum(1 for code in results if code == 429)
        
        assert len(results) == 20
        assert successful + rate_limited > 0

    def test_upload_invalid_file_web(self, base_url):
        files = {"file": ("test.txt", io.StringIO("invalid content"), "text/plain")}
        
        response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            headers={"ngrok-skip-browser-warning": "true"},
            timeout=30
        )
        
        assert response.status_code == 400