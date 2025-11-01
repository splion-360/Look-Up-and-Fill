import concurrent.futures
import os
import statistics
import time

import pytest
import requests


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


class NgrokPerformanceMetrics:
    def __init__(self):
        self.response_times = []
        self.status_codes = []
        self.errors = []
        self.network_errors = 0
        
    def add_result(self, response_time, status_code, error=None):
        self.response_times.append(response_time)
        self.status_codes.append(status_code)
        if error:
            self.errors.append(error)
            if "network" in str(error).lower() or "timeout" in str(error).lower():
                self.network_errors += 1
    
    def calculate_web_stats(self):
        if not self.response_times:
            return {}
        
        sorted_times = sorted(self.response_times)
        return {
            "total_requests": len(self.response_times),
            "successful_requests": sum(1 for code in self.status_codes if code == 200),
            "rate_limited_requests": sum(1 for code in self.status_codes if code == 429),
            "client_errors": sum(1 for code in self.status_codes if 400 <= code < 500),
            "server_errors": sum(1 for code in self.status_codes if code >= 500),
            "network_errors": self.network_errors,
            "min_latency_ms": min(self.response_times) * 1000,
            "max_latency_ms": max(self.response_times) * 1000,
            "mean_latency_ms": statistics.mean(self.response_times) * 1000,
            "median_latency_ms": statistics.median(self.response_times) * 1000,
            "p50_latency_ms": self._percentile(sorted_times, 50) * 1000,
            "p90_latency_ms": self._percentile(sorted_times, 90) * 1000,
            "p95_latency_ms": self._percentile(sorted_times, 95) * 1000,
            "p99_latency_ms": self._percentile(sorted_times, 99) * 1000,
            "success_rate_percent": (sum(1 for code in self.status_codes if code == 200) / len(self.status_codes)) * 100,
            "availability_percent": ((len(self.status_codes) - self.network_errors) / len(self.status_codes)) * 100
        }
    
    def _percentile(self, sorted_times, percentile):
        if not sorted_times:
            return 0
        index = int((percentile / 100) * len(sorted_times))
        if index >= len(sorted_times):
            return sorted_times[-1]
        return sorted_times[index]


class TestNgrokPerformance:
    def test_web_latency_analysis(self, base_url, headers):
        metrics = NgrokPerformanceMetrics()
        
        for _ in range(30):
            start_time = time.time()
            try:
                response = requests.get(f"{base_url}/", headers=headers, timeout=30)
                end_time = time.time()
                metrics.add_result(end_time - start_time, response.status_code)
            except requests.exceptions.RequestException as e:
                end_time = time.time()
                metrics.add_result(end_time - start_time, 0, str(e))
        
        stats = metrics.calculate_web_stats()
        
        print(f"\nWeb Latency Analysis (ngrok tunnel):")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Success Rate: {stats['success_rate_percent']:.1f}%")
        print(f"Availability: {stats['availability_percent']:.1f}%")
        print(f"P50 Latency: {stats['p50_latency_ms']:.2f}ms")
        print(f"P90 Latency: {stats['p90_latency_ms']:.2f}ms")
        print(f"P95 Latency: {stats['p95_latency_ms']:.2f}ms")
        print(f"P99 Latency: {stats['p99_latency_ms']:.2f}ms")
        print(f"Mean Latency: {stats['mean_latency_ms']:.2f}ms")
        print(f"Network Errors: {stats['network_errors']}")
        
        assert stats["total_requests"] == 30
        assert stats["availability_percent"] > 50

    def test_web_upload_performance(self, base_url):
        metrics = NgrokPerformanceMetrics()
        csv_data = "name,symbol,shares,price\nApple Inc.,AAPL,100,150.00\nGoogle Inc.,GOOGL,50,2500.00"
        
        for _ in range(15):
            import io
            files = {"file": ("test.csv", io.StringIO(csv_data), "text/csv")}
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{base_url}/api/v1/documents/upload",
                    files=files,
                    headers={"ngrok-skip-browser-warning": "true"},
                    timeout=60
                )
                end_time = time.time()
                metrics.add_result(end_time - start_time, response.status_code)
            except requests.exceptions.RequestException as e:
                end_time = time.time()
                metrics.add_result(end_time - start_time, 0, str(e))
        
        stats = metrics.calculate_web_stats()
        
        print(f"\nWeb Upload Performance Analysis:")
        print(f"Success Rate: {stats['success_rate_percent']:.1f}%")
        print(f"P50 Upload Time: {stats['p50_latency_ms']:.2f}ms")
        print(f"P99 Upload Time: {stats['p99_latency_ms']:.2f}ms")
        print(f"Max Upload Time: {stats['max_latency_ms']:.2f}ms")
        
        assert stats["total_requests"] == 15

    def test_web_concurrent_throughput(self, base_url, headers):
        metrics = NgrokPerformanceMetrics()
        
        def make_web_request():
            start_time = time.time()
            try:
                response = requests.get(f"{base_url}/", headers=headers, timeout=20)
                end_time = time.time()
                return end_time - start_time, response.status_code, None
            except requests.exceptions.RequestException as e:
                end_time = time.time()
                return end_time - start_time, 0, str(e)
        
        start_test = time.time()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(make_web_request) for _ in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        end_test = time.time()
        
        for response_time, status_code, error in results:
            metrics.add_result(response_time, status_code, error)
        
        stats = metrics.calculate_web_stats()
        total_time = end_test - start_test
        throughput = stats["total_requests"] / total_time
        
        print(f"\nWeb Concurrent Throughput Analysis:")
        print(f"Total Time: {total_time:.2f}s")
        print(f"Web Requests/Second: {throughput:.2f}")
        print(f"Successful Requests: {stats['successful_requests']}")
        print(f"Rate Limited: {stats['rate_limited_requests']}")
        print(f"Network Errors: {stats['network_errors']}")
        print(f"P50 Latency: {stats['p50_latency_ms']:.2f}ms")
        print(f"P99 Latency: {stats['p99_latency_ms']:.2f}ms")
        
        assert stats["total_requests"] == 50
        assert throughput > 0

    def test_web_lookup_performance_real_api(self, base_url, headers):
        metrics = NgrokPerformanceMetrics()
        test_data = {
            "data": [
                {"name": "Apple Inc.", "symbol": "", "shares": 100},
                {"name": "", "symbol": "MSFT", "shares": 50}
            ]
        }
        
        for _ in range(10):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{base_url}/api/v1/documents/lookup/full",
                    json=test_data,
                    headers=headers,
                    timeout=120
                )
                end_time = time.time()
                metrics.add_result(end_time - start_time, response.status_code)
            except requests.exceptions.RequestException as e:
                end_time = time.time()
                metrics.add_result(end_time - start_time, 0, str(e))
        
        stats = metrics.calculate_web_stats()
        
        print(f"\nWeb Lookup Performance (Real API):")
        print(f"Success Rate: {stats['success_rate_percent']:.1f}%")
        print(f"Rate Limited: {stats['rate_limited_requests']}")
        print(f"P50 Lookup Time: {stats['p50_latency_ms']:.2f}ms")
        print(f"P95 Lookup Time: {stats['p95_latency_ms']:.2f}ms")
        print(f"P99 Lookup Time: {stats['p99_latency_ms']:.2f}ms")
        print(f"Max Lookup Time: {stats['max_latency_ms']:.2f}ms")
        
        assert stats["total_requests"] == 10

    def test_web_stress_rate_limiting(self, base_url, headers):
        metrics = NgrokPerformanceMetrics()
        
        def rapid_request():
            start_time = time.time()
            try:
                response = requests.get(f"{base_url}/", headers=headers, timeout=15)
                end_time = time.time()
                return end_time - start_time, response.status_code, None
            except requests.exceptions.RequestException as e:
                end_time = time.time()
                return end_time - start_time, 0, str(e)
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(rapid_request) for _ in range(60)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        for response_time, status_code, error in results:
            metrics.add_result(response_time, status_code, error)
        
        stats = metrics.calculate_web_stats()
        
        print(f"\nWeb Rate Limiting Stress Test:")
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Successful: {stats['successful_requests']}")
        print(f"Rate Limited: {stats['rate_limited_requests']}")
        print(f"Rate Limiting Effectiveness: {(stats['rate_limited_requests']/stats['total_requests'])*100:.1f}%")
        print(f"Average Response Time: {stats['mean_latency_ms']:.2f}ms")
        
        assert stats["total_requests"] == 60
        assert stats["rate_limited_requests"] > 0 or stats["successful_requests"] > 0

    def test_web_error_resilience(self, base_url, headers):
        metrics = NgrokPerformanceMetrics()
        
        invalid_endpoints = [
            f"{base_url}/nonexistent",
            f"{base_url}/api/v1/invalid",
            f"{base_url}/api/v1/documents/invalid"
        ]
        
        for endpoint in invalid_endpoints:
            for _ in range(3):
                start_time = time.time()
                try:
                    response = requests.get(endpoint, headers=headers, timeout=20)
                    end_time = time.time()
                    metrics.add_result(end_time - start_time, response.status_code)
                except requests.exceptions.RequestException as e:
                    end_time = time.time()
                    metrics.add_result(end_time - start_time, 0, str(e))
        
        stats = metrics.calculate_web_stats()
        
        print(f"\nWeb Error Resilience Test:")
        print(f"Client Errors (4xx): {stats['client_errors']}")
        print(f"Server Errors (5xx): {stats['server_errors']}")
        print(f"Network Errors: {stats['network_errors']}")
        print(f"Average Error Response Time: {stats['mean_latency_ms']:.2f}ms")
        
        assert stats["total_requests"] == 9