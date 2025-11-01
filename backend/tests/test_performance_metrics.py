import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class PerformanceMetrics:
    def __init__(self):
        self.response_times = []
        self.status_codes = []
        self.errors = []
        
    def add_result(self, response_time, status_code, error=None):
        self.response_times.append(response_time)
        self.status_codes.append(status_code)
        if error:
            self.errors.append(error)
    
    def calculate_stats(self):
        if not self.response_times:
            return {}
        
        sorted_times = sorted(self.response_times)
        return {
            "total_requests": len(self.response_times),
            "successful_requests": sum(1 for code in self.status_codes if code == 200),
            "rate_limited_requests": sum(1 for code in self.status_codes if code == 429),
            "error_requests": sum(1 for code in self.status_codes if code >= 400 and code != 429),
            "min_latency_ms": min(self.response_times) * 1000,
            "max_latency_ms": max(self.response_times) * 1000,
            "mean_latency_ms": statistics.mean(self.response_times) * 1000,
            "median_latency_ms": statistics.median(self.response_times) * 1000,
            "p50_latency_ms": self._percentile(sorted_times, 50) * 1000,
            "p90_latency_ms": self._percentile(sorted_times, 90) * 1000,
            "p95_latency_ms": self._percentile(sorted_times, 95) * 1000,
            "p99_latency_ms": self._percentile(sorted_times, 99) * 1000,
            "error_rate": len(self.errors) / len(self.response_times) * 100
        }
    
    def _percentile(self, sorted_times, percentile):
        if not sorted_times:
            return 0
        index = int((percentile / 100) * len(sorted_times))
        if index >= len(sorted_times):
            return sorted_times[-1]
        return sorted_times[index]


class TestPerformanceMetrics:
    @patch('app.services.document_processing_service.lookup_missing_data')
    def test_latency_metrics_lookup_endpoint(self, mock_lookup, client):
        mock_lookup.return_value = {"data": [], "enriched_count": 0}
        
        metrics = PerformanceMetrics()
        test_data = {"data": [{"name": "Apple", "symbol": ""}]}
        
        for _ in range(50):
            start_time = time.time()
            response = client.post("/api/v1/documents/lookup/full", json=test_data)
            end_time = time.time()
            
            metrics.add_result(
                response_time=end_time - start_time,
                status_code=response.status_code
            )
        
        stats = metrics.calculate_stats()
        
        assert stats["total_requests"] == 50
        assert "p50_latency_ms" in stats
        assert "p99_latency_ms" in stats
        assert stats["p50_latency_ms"] > 0
        assert stats["p99_latency_ms"] >= stats["p50_latency_ms"]
        
        print(f"\nLatency Metrics for Lookup Endpoint:")
        print(f"P50 Latency: {stats['p50_latency_ms']:.2f}ms")
        print(f"P90 Latency: {stats['p90_latency_ms']:.2f}ms")
        print(f"P95 Latency: {stats['p95_latency_ms']:.2f}ms")
        print(f"P99 Latency: {stats['p99_latency_ms']:.2f}ms")
        print(f"Mean Latency: {stats['mean_latency_ms']:.2f}ms")

    def test_latency_metrics_upload_endpoint(self, client):
        metrics = PerformanceMetrics()
        csv_data = "name,symbol\nApple,AAPL\nGoogle,GOOGL"
        
        for _ in range(30):
            import io
            file = io.BytesIO(csv_data.encode())
            
            start_time = time.time()
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.csv", file, "text/csv")}
            )
            end_time = time.time()
            
            metrics.add_result(
                response_time=end_time - start_time,
                status_code=response.status_code
            )
        
        stats = metrics.calculate_stats()
        
        print(f"\nLatency Metrics for Upload Endpoint:")
        print(f"P50 Latency: {stats['p50_latency_ms']:.2f}ms")
        print(f"P99 Latency: {stats['p99_latency_ms']:.2f}ms")
        print(f"Success Rate: {(stats['successful_requests']/stats['total_requests'])*100:.1f}%")

    @patch('app.services.document_processing_service.lookup_missing_data')
    def test_concurrent_throughput_analysis(self, mock_lookup, client):
        mock_lookup.return_value = {"data": [], "enriched_count": 0}
        
        metrics = PerformanceMetrics()
        test_data = {"data": [{"name": "Apple", "symbol": ""}]}
        
        def make_request():
            start_time = time.time()
            try:
                response = client.post("/api/v1/documents/lookup/full", json=test_data)
                end_time = time.time()
                return end_time - start_time, response.status_code, None
            except Exception as e:
                end_time = time.time()
                return end_time - start_time, 500, str(e)
        
        start_test = time.time()
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(100)]
            results = [future.result() for future in futures]
        end_test = time.time()
        
        for response_time, status_code, error in results:
            metrics.add_result(response_time, status_code, error)
        
        stats = metrics.calculate_stats()
        total_time = end_test - start_test
        throughput = stats["total_requests"] / total_time
        
        print(f"\nThroughput Analysis (100 concurrent requests):")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Requests/Second: {throughput:.2f}")
        print(f"Successful Requests: {stats['successful_requests']}")
        print(f"Rate Limited: {stats['rate_limited_requests']}")
        print(f"P50 Latency: {stats['p50_latency_ms']:.2f}ms")
        print(f"P99 Latency: {stats['p99_latency_ms']:.2f}ms")
        
        assert stats["total_requests"] == 100
        assert throughput > 0