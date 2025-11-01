import asyncio
import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class StressTestResults:
    def __init__(self):
        self.results = []
        self.start_time = None
        self.end_time = None
    
    def add_result(self, response_time, status_code, timestamp):
        self.results.append({
            "response_time": response_time,
            "status_code": status_code,
            "timestamp": timestamp
        })
    
    def calculate_stress_metrics(self):
        if not self.results:
            return {}
        
        response_times = [r["response_time"] for r in self.results]
        status_codes = [r["status_code"] for r in self.results]
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        return {
            "total_requests": len(self.results),
            "total_duration_seconds": total_duration,
            "requests_per_second": len(self.results) / total_duration if total_duration > 0 else 0,
            "successful_requests": sum(1 for code in status_codes if code == 200),
            "rate_limited_requests": sum(1 for code in status_codes if code == 429),
            "server_errors": sum(1 for code in status_codes if code >= 500),
            "client_errors": sum(1 for code in status_codes if 400 <= code < 500 and code != 429),
            "success_rate_percent": (sum(1 for code in status_codes if code == 200) / len(status_codes)) * 100,
            "avg_response_time_ms": statistics.mean(response_times) * 1000,
            "min_response_time_ms": min(response_times) * 1000,
            "max_response_time_ms": max(response_times) * 1000,
            "p50_response_time_ms": statistics.median(response_times) * 1000,
            "p95_response_time_ms": self._percentile(sorted(response_times), 95) * 1000,
            "p99_response_time_ms": self._percentile(sorted(response_times), 99) * 1000
        }
    
    def _percentile(self, sorted_times, percentile):
        if not sorted_times:
            return 0
        index = int((percentile / 100) * len(sorted_times))
        if index >= len(sorted_times):
            return sorted_times[-1]
        return sorted_times[index]


class TestStressTesting:
    @patch('app.services.document_processing_service.lookup_missing_data')
    def test_high_load_stress_test_200_requests(self, mock_lookup, client):
        mock_lookup.return_value = {"data": [], "enriched_count": 0}
        
        stress_results = StressTestResults()
        test_data = {"data": [{"name": "Apple", "symbol": ""}]}
        
        def make_request():
            start_time = time.time()
            response = client.post("/api/v1/documents/lookup/full", json=test_data)
            end_time = time.time()
            return end_time - start_time, response.status_code, end_time
        
        stress_results.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(make_request) for _ in range(200)]
            
            for future in as_completed(futures):
                response_time, status_code, timestamp = future.result()
                stress_results.add_result(response_time, status_code, timestamp)
        
        stress_results.end_time = time.time()
        metrics = stress_results.calculate_stress_metrics()
        
        print(f"\nStress Test Results (200 requests, 50 concurrent):")
        print(f"Total Requests: {metrics['total_requests']}")
        print(f"Duration: {metrics['total_duration_seconds']:.2f}s")
        print(f"Throughput: {metrics['requests_per_second']:.2f} req/s")
        print(f"Success Rate: {metrics['success_rate_percent']:.1f}%")
        print(f"Rate Limited: {metrics['rate_limited_requests']}")
        print(f"Server Errors: {metrics['server_errors']}")
        print(f"P50 Latency: {metrics['p50_response_time_ms']:.2f}ms")
        print(f"P95 Latency: {metrics['p95_response_time_ms']:.2f}ms")
        print(f"P99 Latency: {metrics['p99_response_time_ms']:.2f}ms")
        
        assert metrics["total_requests"] == 200
        assert metrics["requests_per_second"] > 0
        assert metrics["rate_limited_requests"] > 0

    def test_sustained_load_stress_test(self, client):
        stress_results = StressTestResults()
        csv_data = "name,symbol\nApple,AAPL"
        
        def make_upload_request():
            import io
            file = io.BytesIO(csv_data.encode())
            start_time = time.time()
            response = client.post(
                "/api/v1/documents/upload",
                files={"file": ("test.csv", file, "text/csv")}
            )
            end_time = time.time()
            return end_time - start_time, response.status_code, end_time
        
        stress_results.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_upload_request) for _ in range(50)]
            
            for future in as_completed(futures):
                response_time, status_code, timestamp = future.result()
                stress_results.add_result(response_time, status_code, timestamp)
        
        stress_results.end_time = time.time()
        metrics = stress_results.calculate_stress_metrics()
        
        print(f"\nSustained Load Test Results (Upload endpoint):")
        print(f"Throughput: {metrics['requests_per_second']:.2f} req/s")
        print(f"Success Rate: {metrics['success_rate_percent']:.1f}%")
        print(f"Avg Response Time: {metrics['avg_response_time_ms']:.2f}ms")
        
        assert metrics["total_requests"] == 50
        assert metrics["success_rate_percent"] > 80

    @patch('app.services.document_processing_service.search_with_query')
    def test_burst_load_with_api_simulation(self, mock_search, client):
        mock_search.return_value = [{"symbol": "AAPL", "description": "Apple Inc."}]
        
        stress_results = StressTestResults()
        test_data = {"data": [{"name": "Apple Inc.", "symbol": ""}]}
        
        def make_burst_request():
            start_time = time.time()
            response = client.post("/api/v1/documents/lookup/single", json=test_data)
            end_time = time.time()
            return end_time - start_time, response.status_code, end_time
        
        stress_results.start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=30) as executor:
            futures = [executor.submit(make_burst_request) for _ in range(100)]
            
            for future in as_completed(futures):
                response_time, status_code, timestamp = future.result()
                stress_results.add_result(response_time, status_code, timestamp)
        
        stress_results.end_time = time.time()
        metrics = stress_results.calculate_stress_metrics()
        
        print(f"\nBurst Load Test Results:")
        print(f"Peak Throughput: {metrics['requests_per_second']:.2f} req/s")
        print(f"Rate Limiting Effectiveness: {metrics['rate_limited_requests']} requests limited")
        print(f"Max Response Time: {metrics['max_response_time_ms']:.2f}ms")
        print(f"P99 Response Time: {metrics['p99_response_time_ms']:.2f}ms")
        
        assert metrics["total_requests"] == 100
        assert metrics["rate_limited_requests"] > 0

    def test_gradual_load_increase(self, client):
        all_metrics = []
        
        for load_level in [10, 25, 50]:
            stress_results = StressTestResults()
            
            def make_request():
                start_time = time.time()
                response = client.get("/")
                end_time = time.time()
                return end_time - start_time, response.status_code, end_time
            
            stress_results.start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=load_level) as executor:
                futures = [executor.submit(make_request) for _ in range(load_level)]
                
                for future in as_completed(futures):
                    response_time, status_code, timestamp = future.result()
                    stress_results.add_result(response_time, status_code, timestamp)
            
            stress_results.end_time = time.time()
            metrics = stress_results.calculate_stress_metrics()
            metrics["load_level"] = load_level
            all_metrics.append(metrics)
        
        print(f"\nGradual Load Increase Results:")
        for metrics in all_metrics:
            print(f"Load {metrics['load_level']}: {metrics['requests_per_second']:.2f} req/s, "
                  f"P95: {metrics['p95_response_time_ms']:.2f}ms")
        
        assert len(all_metrics) == 3
        assert all(m["success_rate_percent"] > 95 for m in all_metrics)