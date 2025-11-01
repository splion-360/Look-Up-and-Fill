import json
import os
import statistics
import time
from datetime import datetime
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class StatisticsReporter:
    def __init__(self):
        self.test_results = {}
        self.summary = {}
    
    def add_test_result(self, test_name, metrics):
        self.test_results[test_name] = {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
    
    def generate_summary_report(self):
        if not self.test_results:
            return {}
        
        all_response_times = []
        all_throughputs = []
        total_requests = 0
        total_errors = 0
        
        for test_name, result in self.test_results.items():
            metrics = result["metrics"]
            if "avg_response_time_ms" in metrics:
                all_response_times.append(metrics["avg_response_time_ms"])
            if "requests_per_second" in metrics:
                all_throughputs.append(metrics["requests_per_second"])
            if "total_requests" in metrics:
                total_requests += metrics["total_requests"]
            if "server_errors" in metrics:
                total_errors += metrics["server_errors"]
        
        self.summary = {
            "test_execution_summary": {
                "total_tests_run": len(self.test_results),
                "total_requests_processed": total_requests,
                "total_errors_encountered": total_errors,
                "overall_error_rate_percent": (total_errors / total_requests * 100) if total_requests > 0 else 0
            },
            "performance_overview": {
                "avg_response_time_across_tests_ms": statistics.mean(all_response_times) if all_response_times else 0,
                "min_response_time_ms": min(all_response_times) if all_response_times else 0,
                "max_response_time_ms": max(all_response_times) if all_response_times else 0,
                "avg_throughput_req_per_sec": statistics.mean(all_throughputs) if all_throughputs else 0,
                "max_throughput_req_per_sec": max(all_throughputs) if all_throughputs else 0
            },
            "detailed_test_results": self.test_results
        }
        
        return self.summary
    
    def save_report_to_file(self, filename="test_performance_report.json"):
        report = self.generate_summary_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        return filename
    
    def print_summary(self):
        summary = self.generate_summary_report()
        
        print("\n" + "="*60)
        print("PERFORMANCE TEST SUMMARY REPORT")
        print("="*60)
        
        exec_summary = summary.get("test_execution_summary", {})
        print(f"Total Tests Run: {exec_summary.get('total_tests_run', 0)}")
        print(f"Total Requests: {exec_summary.get('total_requests_processed', 0)}")
        print(f"Overall Error Rate: {exec_summary.get('overall_error_rate_percent', 0):.2f}%")
        
        perf_overview = summary.get("performance_overview", {})
        print(f"\nAverage Response Time: {perf_overview.get('avg_response_time_across_tests_ms', 0):.2f}ms")
        print(f"Max Throughput: {perf_overview.get('max_throughput_req_per_sec', 0):.2f} req/s")
        
        print("\nDetailed Results by Test:")
        for test_name, result in self.test_results.items():
            metrics = result["metrics"]
            print(f"\n{test_name}:")
            if "p50_response_time_ms" in metrics:
                print(f"  P50 Latency: {metrics['p50_response_time_ms']:.2f}ms")
            if "p99_response_time_ms" in metrics:
                print(f"  P99 Latency: {metrics['p99_response_time_ms']:.2f}ms")
            if "requests_per_second" in metrics:
                print(f"  Throughput: {metrics['requests_per_second']:.2f} req/s")
            if "success_rate_percent" in metrics:
                print(f"  Success Rate: {metrics['success_rate_percent']:.1f}%")


class TestStatisticsReporter:
    @patch('app.services.document_processing_service.lookup_missing_data')
    def test_comprehensive_performance_analysis(self, mock_lookup, client):
        mock_lookup.return_value = {"data": [], "enriched_count": 0}
        
        reporter = StatisticsReporter()
        
        # Test 1: Latency Analysis
        response_times = []
        for _ in range(30):
            start_time = time.time()
            response = client.post("/api/v1/documents/lookup/full", json={"data": []})
            end_time = time.time()
            response_times.append((end_time - start_time) * 1000)
        
        latency_metrics = {
            "avg_response_time_ms": statistics.mean(response_times),
            "p50_response_time_ms": statistics.median(response_times),
            "p99_response_time_ms": self._percentile(sorted(response_times), 99),
            "total_requests": len(response_times),
            "server_errors": 0
        }
        reporter.add_test_result("latency_analysis", latency_metrics)
        
        # Test 2: Throughput Analysis
        start_time = time.time()
        responses = []
        for _ in range(50):
            response = client.get("/")
            responses.append(response.status_code)
        end_time = time.time()
        
        duration = end_time - start_time
        throughput_metrics = {
            "requests_per_second": len(responses) / duration,
            "success_rate_percent": (sum(1 for code in responses if code == 200) / len(responses)) * 100,
            "total_requests": len(responses),
            "server_errors": sum(1 for code in responses if code >= 500)
        }
        reporter.add_test_result("throughput_analysis", throughput_metrics)
        
        # Generate and print comprehensive report
        summary = reporter.generate_summary_report()
        reporter.print_summary()
        
        # Save to file
        filename = reporter.save_report_to_file()
        assert os.path.exists(filename)
        
        # Verify summary structure
        assert "test_execution_summary" in summary
        assert "performance_overview" in summary
        assert "detailed_test_results" in summary
        assert summary["test_execution_summary"]["total_tests_run"] == 2
        
        # Cleanup
        if os.path.exists(filename):
            os.remove(filename)
    
    def _percentile(self, sorted_times, percentile):
        if not sorted_times:
            return 0
        index = int((percentile / 100) * len(sorted_times))
        if index >= len(sorted_times):
            return sorted_times[-1]
        return sorted_times[index]

    def test_edge_case_statistics(self, client):
        reporter = StatisticsReporter()
        
        # Test with minimal data
        minimal_metrics = {
            "total_requests": 1,
            "avg_response_time_ms": 50.0,
            "requests_per_second": 1.0,
            "server_errors": 0
        }
        reporter.add_test_result("minimal_test", minimal_metrics)
        
        summary = reporter.generate_summary_report()
        assert summary["test_execution_summary"]["total_tests_run"] == 1
        assert summary["performance_overview"]["avg_response_time_across_tests_ms"] == 50.0
        
        reporter.print_summary()

    @patch('app.services.document_processing_service.lookup_missing_data')
    def test_error_rate_analysis(self, mock_lookup, client):
        # Simulate API errors
        mock_lookup.side_effect = Exception("API Error")
        
        reporter = StatisticsReporter()
        
        error_count = 0
        total_requests = 20
        
        for _ in range(total_requests):
            try:
                response = client.post("/api/v1/documents/lookup/full", json={"data": [{"name": "Test"}]})
                if response.status_code >= 500:
                    error_count += 1
            except:
                error_count += 1
        
        error_metrics = {
            "total_requests": total_requests,
            "server_errors": error_count,
            "error_rate_percent": (error_count / total_requests) * 100,
            "avg_response_time_ms": 100.0,
            "requests_per_second": 10.0
        }
        reporter.add_test_result("error_analysis", error_metrics)
        
        summary = reporter.generate_summary_report()
        print(f"\nError Analysis Results:")
        print(f"Error Rate: {summary['test_execution_summary']['overall_error_rate_percent']:.2f}%")
        
        assert summary["test_execution_summary"]["total_errors_encountered"] == error_count