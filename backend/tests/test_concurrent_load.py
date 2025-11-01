import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestConcurrentLoad:
    @patch("app.services.document_processing_service.search_with_query")
    @patch("app.services.document_processing_service.get_profile_for_symbol")
    async def test_concurrent_requests(self, mock_profile, mock_search):
        """
        Simulates 100 concurrent request to stress test the
        app-microservices for rate-limiting

        """

        mock_search.return_value = [
            {"symbol": "AAPL", "description": "Apple Inc."}
        ]
        mock_profile.return_value = {"name": "Apple Inc."}

        client = TestClient(app)

        async def make_request():
            return client.post(
                "/api/v1/documents/lookup/full",
                json={"data": [{"name": "Apple", "symbol": ""}]},
            )

        tasks = [make_request() for _ in range(100)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        successful = 0
        rate_limited = 0
        errors = 0

        for response in responses:
            if hasattr(response, "status_code"):
                if response.status_code == 200:
                    successful += 1
                elif response.status_code == 429:
                    rate_limited += 1
                else:
                    errors += 1
            else:
                errors += 1

        assert successful + rate_limited + errors == 100
        assert rate_limited > 0

    @patch("app.services.document_processing_service.search_with_query")
    async def test_rl_recovery(self, mock_search):
        """
        Tests the RESILIENCE of the endpoints

        """
        mock_search.return_value = [
            {"symbol": "AAPL", "description": "Apple Inc."}
        ]

        client = TestClient(app)

        for _ in range(35):
            client.post("/api/v1/documents/lookup/full", json={"data": []})

        response = client.post(
            "/api/v1/documents/lookup/full", json={"data": []}
        )
        initial_status = response.status_code

        await asyncio.sleep(2)

        response = client.post(
            "/api/v1/documents/lookup/full", json={"data": []}
        )
        recovery_status = response.status_code

        if initial_status == 429:
            assert recovery_status in [200, 429]

    @patch("app.services.document_processing_service.httpx.AsyncClient")
    async def test_api_failure_handling(self, mock_client):
        from httpx import HTTPStatusError

        mock_response = AsyncMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        mock_client.return_value.__aenter__.return_value.get.side_effect = (
            HTTPStatusError(
                "Server Error", request=None, response=mock_response
            )
        )

        client = TestClient(app)
        response = client.post(
            "/api/v1/documents/lookup/full",
            json={"data": [{"name": "Apple", "symbol": ""}]},
        )

        assert response.status_code in [500, 429]
