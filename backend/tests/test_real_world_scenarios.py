import concurrent.futures
import json
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


class RealWorldScenarioResults:
    def __init__(self, scenario_name):
        self.scenario_name = scenario_name
        self.results = []
        self.start_time = None
        self.end_time = None
        
    def add_result(self, operation, response_time, status_code, payload_size=0):
        self.results.append({
            "operation": operation,
            "response_time": response_time,
            "status_code": status_code,
            "payload_size": payload_size,
            "timestamp": time.time()
        })
    
    def generate_scenario_report(self):
        if not self.results:
            return {}
        
        response_times = [r["response_time"] for r in self.results]
        status_codes = [r["status_code"] for r in self.results]
        
        operations = {}
        for result in self.results:
            op = result["operation"]
            if op not in operations:
                operations[op] = {"times": [], "codes": []}
            operations[op]["times"].append(result["response_time"])
            operations[op]["codes"].append(result["status_code"])
        
        total_duration = self.end_time - self.start_time if self.end_time and self.start_time else 0
        
        report = {
            "scenario_name": self.scenario_name,
            "execution_summary": {
                "total_operations": len(self.results),
                "total_duration_seconds": total_duration,
                "operations_per_second": len(self.results) / total_duration if total_duration > 0 else 0,
                "success_rate_percent": (sum(1 for code in status_codes if code == 200) / len(status_codes)) * 100,
                "error_rate_percent": (sum(1 for code in status_codes if code >= 400) / len(status_codes)) * 100
            },
            "latency_metrics": {
                "p50_ms": self._percentile(sorted(response_times), 50) * 1000,
                "p90_ms": self._percentile(sorted(response_times), 90) * 1000,
                "p95_ms": self._percentile(sorted(response_times), 95) * 1000,
                "p99_ms": self._percentile(sorted(response_times), 99) * 1000,
                "mean_ms": statistics.mean(response_times) * 1000,
                "max_ms": max(response_times) * 1000,
                "min_ms": min(response_times) * 1000
            },
            "operations_breakdown": {}
        }
        
        for op_name, op_data in operations.items():
            if op_data["times"]:
                report["operations_breakdown"][op_name] = {
                    "count": len(op_data["times"]),
                    "avg_latency_ms": statistics.mean(op_data["times"]) * 1000,
                    "success_rate": (sum(1 for code in op_data["codes"] if code == 200) / len(op_data["codes"])) * 100
                }
        
        return report
    
    def _percentile(self, sorted_times, percentile):
        if not sorted_times:
            return 0
        index = int((percentile / 100) * len(sorted_times))
        if index >= len(sorted_times):
            return sorted_times[-1]
        return sorted_times[index]
    
    def print_report(self):
        report = self.generate_scenario_report()
        
        print(f"\n{'='*60}")
        print(f"REAL-WORLD SCENARIO: {report['scenario_name']}")
        print(f"{'='*60}")
        
        exec_summary = report["execution_summary"]
        print(f"Total Operations: {exec_summary['total_operations']}")
        print(f"Duration: {exec_summary['total_duration_seconds']:.2f}s")
        print(f"Throughput: {exec_summary['operations_per_second']:.2f} ops/sec")
        print(f"Success Rate: {exec_summary['success_rate_percent']:.1f}%")
        print(f"Error Rate: {exec_summary['error_rate_percent']:.1f}%")
        
        latency = report["latency_metrics"]
        print(f"\nLatency Metrics:")
        print(f"  P50: {latency['p50_ms']:.2f}ms")
        print(f"  P90: {latency['p90_ms']:.2f}ms")
        print(f"  P95: {latency['p95_ms']:.2f}ms")
        print(f"  P99: {latency['p99_ms']:.2f}ms")
        print(f"  Mean: {latency['mean_ms']:.2f}ms")
        print(f"  Max: {latency['max_ms']:.2f}ms")
        
        print(f"\nOperations Breakdown:")
        for op_name, op_stats in report["operations_breakdown"].items():
            print(f"  {op_name}: {op_stats['count']} ops, "
                  f"{op_stats['avg_latency_ms']:.2f}ms avg, "
                  f"{op_stats['success_rate']:.1f}% success")


class TestRealWorldScenarios:
    def test_typical_user_workflow(self, base_url, headers):
        scenario = RealWorldScenarioResults("Typical User Workflow")
        scenario.start_time = time.time()
        
        # Step 1: Check service health
        start_time = time.time()
        try:
            response = requests.get(f"{base_url}/", headers=headers, timeout=30)
            scenario.add_result("health_check", time.time() - start_time, response.status_code)
        except requests.exceptions.RequestException:
            scenario.add_result("health_check", time.time() - start_time, 0)
        
        # Step 2: Upload CSV file
        csv_data = """name,symbol,shares,price
Apple Inc.,,100,150.00
,GOOGL,50,2500.00
Microsoft Corp.,,75,300.00
Tesla Inc.,,25,800.00
,AMZN,30,3200.00"""
        
        import io
        files = {"file": ("portfolio.csv", io.StringIO(csv_data), "text/csv")}
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{base_url}/api/v1/documents/upload",
                files=files,
                headers={"ngrok-skip-browser-warning": "true"},
                timeout=60
            )
            scenario.add_result("file_upload", time.time() - start_time, response.status_code, len(csv_data))
            upload_data = response.json() if response.status_code == 200 else None
        except requests.exceptions.RequestException:
            scenario.add_result("file_upload", time.time() - start_time, 0)
            upload_data = None
        
        # Step 3: Lookup missing data
        if upload_data:
            lookup_payload = {"data": upload_data.get("data", [])}
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{base_url}/api/v1/documents/lookup/full",
                    json=lookup_payload,
                    headers=headers,
                    timeout=120
                )
                scenario.add_result("data_lookup", time.time() - start_time, response.status_code, 
                                  len(json.dumps(lookup_payload)))
            except requests.exceptions.RequestException:
                scenario.add_result("data_lookup", time.time() - start_time, 0)
        
        scenario.end_time = time.time()
        scenario.print_report()
        
        assert len(scenario.results) >= 2

    def test_high_frequency_trading_simulation(self, base_url, headers):
        scenario = RealWorldScenarioResults("High Frequency Trading Simulation")
        scenario.start_time = time.time()
        
        symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA", "META", "NFLX"]
        
        def lookup_symbol(symbol):
            start_time = time.time()
            try:
                response = requests.post(
                    f"{base_url}/api/v1/documents/lookup/single",
                    json={"data": [{"name": "", "symbol": symbol, "shares": 100}]},
                    headers=headers,
                    timeout=30
                )
                return time.time() - start_time, response.status_code
            except requests.exceptions.RequestException:
                return time.time() - start_time, 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            for _ in range(3):
                futures = [executor.submit(lookup_symbol, symbol) for symbol in symbols]
                for i, future in enumerate(concurrent.futures.as_completed(futures)):
                    response_time, status_code = future.result()
                    scenario.add_result(f"symbol_lookup_{symbols[i % len(symbols)]}", 
                                      response_time, status_code)
        
        scenario.end_time = time.time()
        scenario.print_report()
        
        assert len(scenario.results) >= 20

    def test_batch_processing_scenario(self, base_url, headers):
        scenario = RealWorldScenarioResults("Batch Processing Scenario")
        scenario.start_time = time.time()
        
        # Large batch of mixed data
        large_batch = {
            "data": [
                {"name": f"Company {i}", "symbol": "", "shares": 100 + i}
                for i in range(20)
            ] + [
                {"name": "", "symbol": f"SYM{i}", "shares": 50 + i}
                for i in range(15)
            ]
        }
        
        start_time = time.time()
        try:
            response = requests.post(
                f"{base_url}/api/v1/documents/lookup/full",
                json=large_batch,
                headers=headers,
                timeout=180
            )
            scenario.add_result("large_batch_lookup", time.time() - start_time, 
                              response.status_code, len(json.dumps(large_batch)))
        except requests.exceptions.RequestException:
            scenario.add_result("large_batch_lookup", time.time() - start_time, 0)
        
        # Multiple smaller batches
        for batch_num in range(5):
            small_batch = {
                "data": [
                    {"name": f"Batch{batch_num}_Company{i}", "symbol": "", "shares": 10}
                    for i in range(3)
                ]
            }
            
            start_time = time.time()
            try:
                response = requests.post(
                    f"{base_url}/api/v1/documents/lookup/single",
                    json=small_batch,
                    headers=headers,
                    timeout=60
                )
                scenario.add_result(f"small_batch_{batch_num}", time.time() - start_time, 
                                  response.status_code)
            except requests.exceptions.RequestException:
                scenario.add_result(f"small_batch_{batch_num}", time.time() - start_time, 0)
        
        scenario.end_time = time.time()
        scenario.print_report()
        
        assert len(scenario.results) >= 5

    def test_peak_load_simulation(self, base_url, headers):
        scenario = RealWorldScenarioResults("Peak Load Simulation")
        scenario.start_time = time.time()
        
        def simulate_user_request():
            start_time = time.time()
            try:
                # Random operation selection
                import random
                if random.choice([True, False]):
                    response = requests.get(f"{base_url}/", headers=headers, timeout=20)
                    operation = "health_check"
                else:
                    test_data = {"data": [{"name": "Apple Inc.", "symbol": "", "shares": 100}]}
                    response = requests.post(
                        f"{base_url}/api/v1/documents/lookup/single",
                        json=test_data,
                        headers=headers,
                        timeout=45
                    )
                    operation = "quick_lookup"
                
                return operation, time.time() - start_time, response.status_code
            except requests.exceptions.RequestException:
                return "failed_request", time.time() - start_time, 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(simulate_user_request) for _ in range(75)]
            
            for future in concurrent.futures.as_completed(futures):
                operation, response_time, status_code = future.result()
                scenario.add_result(operation, response_time, status_code)
        
        scenario.end_time = time.time()
        scenario.print_report()
        
        report = scenario.generate_scenario_report()
        assert report["execution_summary"]["total_operations"] == 75
        assert report["execution_summary"]["operations_per_second"] > 0

    def test_error_recovery_scenario(self, base_url, headers):
        scenario = RealWorldScenarioResults("Error Recovery Scenario")
        scenario.start_time = time.time()
        
        # Test invalid requests first
        invalid_requests = [
            {"endpoint": "/api/v1/documents/upload", "method": "POST", "data": None},
            {"endpoint": "/api/v1/documents/lookup/full", "method": "POST", "data": {"invalid": "data"}},
            {"endpoint": "/nonexistent", "method": "GET", "data": None}
        ]
        
        for req in invalid_requests:
            start_time = time.time()
            try:
                if req["method"] == "GET":
                    response = requests.get(f"{base_url}{req['endpoint']}", 
                                          headers=headers, timeout=20)
                else:
                    response = requests.post(f"{base_url}{req['endpoint']}", 
                                           json=req["data"], headers=headers, timeout=20)
                scenario.add_result("error_request", time.time() - start_time, response.status_code)
            except requests.exceptions.RequestException:
                scenario.add_result("error_request", time.time() - start_time, 0)
        
        # Follow up with valid requests to test recovery
        for _ in range(5):
            start_time = time.time()
            try:
                response = requests.get(f"{base_url}/", headers=headers, timeout=20)
                scenario.add_result("recovery_request", time.time() - start_time, response.status_code)
            except requests.exceptions.RequestException:
                scenario.add_result("recovery_request", time.time() - start_time, 0)
        
        scenario.end_time = time.time()
        scenario.print_report()
        
        assert len(scenario.results) >= 8