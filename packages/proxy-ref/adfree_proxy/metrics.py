# adfree_proxy/metrics.py

from prometheus_client import Counter, Histogram

# Métricas clave
REQUEST_COUNT = Counter(
    'adfree_requests_total',
    'Total de requests procesadas por el proxy',
    ['method', 'path']
)

BLOCKED_REQUESTS = Counter(
    'adfree_blocked_requests_total',
    'Requests bloqueadas por política Adfree',
    ['reason', 'domain']
)

POLICY_VALIDATION_ERRORS = Counter(
    'adfree_policy_validation_errors_total',
    'Errores al validar políticas Adfree',
    ['origin', 'error_type']
)

REQUEST_LATENCY = Histogram(
    'adfree_request_latency_seconds',
    'Latencia de requests procesadas por el proxy',
    ['method', 'path']
)

# Métricas para reporter.py
REPORT_SENT = Counter(
    'adfree_reports_sent_total',
    'Total de reportes enviados exitosamente',
    ['endpoint', 'status']
)

REPORT_FAILED = Counter(
    'adfree_reports_failed_total',
    'Total de reportes que fallaron al enviarse',
    ['endpoint', 'reason']
)


class MetricsCollector:
    """Pequeño wrapper para exponer operaciones simples en tests.
    En producción, los contadores de prometheus se usan directamente.
    """
    def inc_requests(self, method: str = 'GET', path: str = '/'):
        REQUEST_COUNT.labels(method=method, path=path).inc()

    def inc_blocked(self, domain: str, reason: str = 'iframe_blocked'):
        BLOCKED_REQUESTS.labels(reason=reason, domain=domain).inc()

    def observe_latency(self, method: str, path: str, value: float):
        REQUEST_LATENCY.labels(method=method, path=path).observe(value)