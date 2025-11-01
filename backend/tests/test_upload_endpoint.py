import io
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def valid_csv():
    return """name,symbol,shares,price
Apple Inc.,AAPL,100,150.00
,GOOGL,50,2500.00"""


class TestUploadEndpoint:
    def test_upload_success(self, client, valid_csv):
        file = io.BytesIO(valid_csv.encode())
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.csv", file, "text/csv")}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_rows"] == 2

    def test_upload_invalid_file(self, client):
        file = io.BytesIO(b"invalid content")
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.txt", file, "text/plain")}
        )
        assert response.status_code == 400

    def test_upload_empty_file(self, client):
        file = io.BytesIO(b"")
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("empty.csv", file, "text/csv")}
        )
        assert response.status_code == 400

    def test_upload_no_file(self, client):
        response = client.post("/api/v1/documents/upload")
        assert response.status_code == 422

    @patch('app.services.document_processing_service.process_csv_file')
    def test_upload_processing_error(self, mock_process, client):
        mock_process.side_effect = HTTPException(status_code=500, detail="Processing failed")
        file = io.BytesIO(b"name,symbol\nTest,TEST")
        response = client.post(
            "/api/v1/documents/upload",
            files={"file": ("test.csv", file, "text/csv")}
        )
        assert response.status_code == 500