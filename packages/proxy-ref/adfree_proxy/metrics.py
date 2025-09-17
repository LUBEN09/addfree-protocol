"""Metrics collector wrapper for prometheus_client"""
from prometheus_client import Counter


class MetricsCollector:
    def __init__(self):
        self.requests_total = Counter('adfree_requests_total', 'Total requests processed')

    def inc_requests(self):
        self.requests_total.inc()
