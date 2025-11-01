import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.middleware.rate_limit import RateLimitMiddleware, TokenBucket


@pytest.fixture
def client():
    return TestClient(app)


class TestTokenBucket:
    def test_token_bucket_creation(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.capacity == 10
        assert bucket.tokens == 10

    def test_token_consumption_success(self):
        bucket = TokenBucket(capacity=10, refill_rate=1.0)
        assert bucket.consume(5) == True
        assert bucket.tokens == 5

    def test_token_consumption_failure(self):
        bucket = TokenBucket(capacity=5, refill_rate=1.0)
        bucket.consume(5)
        assert bucket.consume(1) == False

    def test_token_refill(self):
        bucket = TokenBucket(capacity=10, refill_rate=10.0)
        bucket.consume(10)
        import time
        time.sleep(0.1)
        bucket._refill()
        assert bucket.tokens > 0


class TestRateLimitMiddleware:
    @patch('app.services.document_processing_service.lookup_missing_data')
    async def test_concurrent_requests_rate_limiting(self, mock_lookup, client):
        mock_lookup.return_value = {"data": [], "enriched_count": 0}
        
        async def make_request():
            return client.post("/api/v1/documents/lookup/full", json={"data": []})
        
        tasks = [make_request() for _ in range(100)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        status_codes = [r.status_code for r in responses if hasattr(r, 'status_code')]
        rate_limited = sum(1 for code in status_codes if code == 429)
        successful = sum(1 for code in status_codes if code == 200)
        
        assert rate_limited > 0
        assert successful > 0
        assert len(status_codes) == 100

    def test_rate_limit_response_format(self, client):
        for _ in range(35):
            client.get("/")
        
        response = client.get("/")
        if response.status_code == 429:
            assert "Rate limit exceeded" in response.json()["detail"]

    @patch('app.services.document_processing_service.search_with_query')
    async def test_rate_limiting_with_mocked_api(self, mock_search):
        mock_search.return_value = [{"symbol": "AAPL", "description": "Apple Inc."}]
        
        middleware = RateLimitMiddleware(requests_per_minute=5)
        
        from fastapi import Request
        from unittest.mock import Mock
        
        mock_request = Mock(spec=Request)
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"
        mock_request.headers = {}
        
        async def mock_call_next(request):
            return {"status": "success"}
        
        responses = []
        for _ in range(10):
            response = await middleware(mock_request, mock_call_next)
            responses.append(response)
        
        rate_limited = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 429)
        assert rate_limited > 0