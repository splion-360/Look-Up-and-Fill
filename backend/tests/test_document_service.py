from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException

from app.services.document_processing_service import (
    get_name_from_symbol,
    get_symbol_from_name,
    search_with_query,
)


class TestDocumentService:
    @patch('app.services.document_processing_service.httpx.AsyncClient')
    async def test_search_with_query_success(self, mock_client):
        mock_response = AsyncMock()
        mock_response.json.return_value = {"result": [{"symbol": "AAPL", "description": "Apple Inc."}]}
        mock_response.raise_for_status = AsyncMock()
        
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await search_with_query("Apple")
        assert len(result) == 1
        assert result[0]["symbol"] == "AAPL"

    @patch('app.services.document_processing_service.httpx.AsyncClient')
    async def test_search_with_query_rate_limit(self, mock_client):
        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.text = "Rate limit exceeded"
        
        from httpx import HTTPStatusError
        mock_client.return_value.__aenter__.return_value.get.side_effect = HTTPStatusError(
            "Rate limit", request=None, response=mock_response
        )
        
        with pytest.raises(HTTPException) as exc_info:
            await search_with_query("Apple")
        assert exc_info.value.status_code == 429

    @patch('app.services.document_processing_service.search_with_query')
    async def test_get_symbol_from_name_success(self, mock_search):
        mock_search.return_value = [{"symbol": "AAPL", "description": "Apple Inc."}]
        result = await get_symbol_from_name("Apple Inc.")
        assert result == "AAPL"

    @patch('app.services.document_processing_service.search_with_query')
    async def test_get_symbol_from_name_not_found(self, mock_search):
        mock_search.return_value = []
        result = await get_symbol_from_name("NonExistent Company")
        assert result is None

    @patch('app.services.document_processing_service.get_profile_for_symbol')
    async def test_get_name_from_symbol_success(self, mock_profile):
        mock_profile.return_value = {"name": "Apple Inc."}
        result = await get_name_from_symbol("AAPL")
        assert result == "Apple Inc."

    @patch('app.services.document_processing_service.get_profile_for_symbol')
    async def test_get_name_from_symbol_not_found(self, mock_profile):
        mock_profile.return_value = {}
        result = await get_name_from_symbol("INVALID")
        assert result is None

    async def test_get_symbol_from_name_invalid_input(self):
        result = await get_symbol_from_name("")
        assert result is None
        
        result = await get_symbol_from_name(None)
        assert result is None

    @patch('app.services.document_processing_service.httpx.AsyncClient')
    async def test_api_timeout_error(self, mock_client):
        import httpx
        mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException("Timeout")
        
        with pytest.raises(HTTPException) as exc_info:
            await search_with_query("Apple")
        assert exc_info.value.status_code == 500