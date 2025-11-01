import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def sample_csv_data():
    return """name,symbol,shares,price,market
Apple Inc.,AAPL,100,150.00,NASDAQ
,GOOGL,50,2500.00,NASDAQ
Microsoft Corp.,,75,300.00,NASDAQ"""


@pytest.fixture
def sample_lookup_data():
    return [
        {"name": "Apple Inc.", "symbol": "", "shares": 100, "price": 150.00},
        {"name": "", "symbol": "GOOGL", "shares": 50, "price": 2500.00},
        {
            "name": "Microsoft Corp.",
            "symbol": "",
            "shares": 75,
            "price": 300.00,
        },
    ]
