from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_data():
    return [
        {"name": "Apple Inc.", "symbol": "", "shares": 100},
        {"name": "", "symbol": "GOOGL", "shares": 50}
    ]


class TestLookupEndpoints:
    @patch('app.services.document_processing_service.lookup_missing_data')
    def test_lookup_full_success(self, mock_lookup, client, sample_data):
        mock_lookup.return_value = {"data": sample_data, "enriched_count": 2}
        response = client.post("/api/v1/documents/lookup/full", json={"data": sample_data})
        assert response.status_code == 200
        assert response.json()["enriched_count"] == 2

    @patch('app.services.document_processing_service.lookup_missing_data')
    def test_lookup_single_success(self, mock_lookup, client, sample_data):
        mock_lookup.return_value = {"data": sample_data, "enriched_count": 1}
        response = client.post("/api/v1/documents/lookup/single", json={"data": sample_data})
        assert response.status_code == 200

    def test_lookup_invalid_data(self, client):
        response = client.post("/api/v1/documents/lookup/full", json={"invalid": "data"})
        assert response.status_code == 422

    @patch('app.services.document_processing_service.lookup_missing_data')
    def test_lookup_service_error(self, mock_lookup, client, sample_data):
        mock_lookup.side_effect = HTTPException(status_code=500, detail="Internal Server Error")
        response = client.post("/api/v1/documents/lookup/full", json={"data": sample_data})
        assert response.status_code == 500

    @patch('app.services.document_processing_service.lookup_missing_data')
    def test_lookup_rate_limit_error(self, mock_lookup, client, sample_data):
        mock_lookup.side_effect = HTTPException(status_code=429, detail="Rate limit exceeded")
        response = client.post("/api/v1/documents/lookup/full", json={"data": sample_data})
        assert response.status_code == 429