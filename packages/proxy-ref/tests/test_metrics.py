from adfree_proxy.metrics import MetricsCollector


def test_metrics_inc():
    m = MetricsCollector()
    m.inc_requests()
    # No assertion for prometheus counter, just ensure call doesn't raise
