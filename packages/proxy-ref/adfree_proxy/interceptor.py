"""adfree_proxy/interceptor.py

Middleware and helpers for applying Adfree policies to upstream responses.
This file provides a clean, self-contained implementation that expects a
ClientSession to be injected by the caller. It uses ReportClient to send
policy violation reports (fire-and-forget via asyncio.create_task).
"""

import asyncio
import logging
import re
import json
from typing import Dict, Any, List, Optional

from aiohttp import web, ClientSession

from .policy import AdfreePolicy, validate_policy
from .metrics import REQUEST_COUNT, BLOCKED_REQUESTS
from .reporter import ReportClient

logger = logging.getLogger(__name__)


class AdfreeInterceptor:
    def __init__(self, session: ClientSession):
        """Create interceptor with an injected aiohttp ClientSession.

        The caller owns the session lifecycle; this class will use it to send
        reports via ReportClient.
        """
        self.session = session
        self.reporter = ReportClient(session)
        self.active_policies: Dict[str, AdfreePolicy] = {}

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        # Do not close injected session here
        return None

    @web.middleware
    async def intercept_request(self, request: web.Request, handler):
        # Record basic metric
        REQUEST_COUNT.labels(method=request.method, path=request.path).inc()

        # If client didn't opt-in to Adfree, pass through
        if 'Adfree-Want' not in request.headers:
            return await handler(request)

        # For this reference implementation we simulate the upstream response.
        # In production, this should forward the request to the real upstream
        # and apply the policy present on the upstream response.
        response = await self._simulate_upstream_response(request)

        policy_json_str = response.headers.get('Adfree-Policy')
        signature_b64 = response.headers.get('Adfree-Signature')

        if policy_json_str and signature_b64:
            try:
                policy_json = json.loads(policy_json_str)
                origin = request.host

                policy = await validate_policy(policy_json, signature_b64, origin)
                if policy:
                    self.active_policies[origin] = policy
                    logger.info('Policy activated for %s in mode %s', origin, policy.mode)

                    if policy.mode in ('strict', 'relaxed'):
                        response = await self._apply_policy_to_response(response, policy, origin)
                    elif policy.mode == 'report-only':
                        # report-only: we may still want to scan the body and emit reports
                        response = await self._apply_policy_to_response(response, policy, origin)
                else:
                    logger.warning('Invalid or unsigned policy from %s', origin)
            except Exception as e:
                logger.exception('Error processing policy: %s', e)

        return response

    async def _simulate_upstream_response(self, request: web.Request) -> web.Response:
        # This simulates an upstream response that contains a policy header.
        policy_data = {
            'version': '1',
            'mode': 'report-only',
            'max_ads_per_page': 2,
            'allow_redirects': False,
            'allow_iframes': ['self'],
            'blocked_domains': ['ads.example.com', 'trackers.net'],
            'report_to': 'http://127.0.0.1:8089/adfree'
        }

        body = b"<html><head></head><body><h1>Hello</h1><iframe src='https://ads.example.com/banner'></iframe></body></html>"

        return web.Response(
            body=body,
            content_type='text/html',
            headers={
                'Adfree-Policy': json.dumps(policy_data),
                'Adfree-Signature': 'SIMULATED_SIGNATURE',
                'Adfree-Supported': 'true'
            }
        )

    async def _apply_policy_to_response(self, response: web.Response, policy: AdfreePolicy, origin: str) -> web.Response:
        if response.content_type != 'text/html':
            return response

        body = await response.read()
        body_str = body.decode('utf-8', errors='ignore')

        # Remove blocked iframes and optionally report violations
        if getattr(policy, 'blocked_domains', None):
            body_str = await self._remove_blocked_iframes(body_str, policy)

        # Inject redirect blocker script if redirects not allowed
        if not getattr(policy, 'allow_redirects', True):
            body_str = self._inject_redirect_blocker(body_str)

        new_body = body_str.encode('utf-8')

        # Rebuild response preserving status and headers
        new_headers = dict(response.headers)
        # Ensure content-length matches
        new_headers['Content-Length'] = str(len(new_body))

        new_response = web.Response(
            body=new_body,
            content_type=response.content_type,
            headers=new_headers,
            status=getattr(response, 'status', 200)
        )

        return new_response

    async def _remove_blocked_iframes(self, html_text: str, policy: AdfreePolicy) -> str:
        """Remove iframe tags whose src matches any blocked domain.

        This function also schedules a report for each removed iframe when the
        policy is in 'report-only' mode. It updates the BLOCKED_REQUESTS metric
        for observability.
        """
        blocked_domains = getattr(policy, 'blocked_domains', []) or []

        iframe_pattern = r"<iframe\s+[^>]*src\s*=\s*(['\"])(https?://([^/\"'>]+))\1[^>]*>.*?</iframe>"

        # Lista para acumular violaciones (para reportar después)
        violations_to_report = []

        def repl(match: re.Match) -> str:
            url = match.group(2)
            domain = match.group(3)

            for blocked in blocked_domains:
                if blocked.startswith('*.'):
                    base = blocked[2:]
                    if domain.endswith(base):
                        # Registrar violación para reportar después
                        violations_to_report.append((url, blocked))
                        logger.info('Blocked iframe to %s (matched %s)', url, blocked)
                        return ''  # Eliminar iframe
                else:
                    if domain == blocked:
                        violations_to_report.append((url, blocked))
                        logger.info('Blocked iframe to %s (matched %s)', url, blocked)
                        return ''  # Eliminar iframe

            return match.group(0)

        # Aplicar el reemplazo síncronamente
        cleaned = re.sub(iframe_pattern, repl, html_text, flags=re.IGNORECASE | re.DOTALL)

        # Ahora, programar las tareas de métricas y reportes (fuera de re.sub)
        for url, domain in violations_to_report:
            # Incrementar métrica
            try:
                BLOCKED_REQUESTS.labels(reason='iframe_blocked', domain=domain).inc()
            except Exception:
                logger.debug('Could not increment BLOCKED_REQUESTS metric')

            # Programar reporte si es report-only
            if getattr(policy, 'mode', '') == 'report-only' and getattr(self, 'reporter', None):
                violation = {
                    'type': 'blocked_iframe',
                    'url': url,
                    'domain': domain,
                    'action': 'blocked'
                }
                try:
                    asyncio.create_task(self.reporter.report_policy_violation(policy, violation))
                except Exception:
                    logger.exception('Failed to schedule report_policy_violation task')

        return cleaned

    def _inject_redirect_blocker(self, html_text: str) -> str:
        script = (
            '<script>'
            '(function(){var originalOpen=window.open; window.open=function(){return null;};})();'
            '</script>'
        )

        if '</head>' in html_text:
            return html_text.replace('</head>', script + '</head>')
        if '</body>' in html_text:
            return html_text.replace('</body>', script + '</body>')
        return html_text + script

    async def metrics_handler(self, request: web.Request) -> web.Response:
        from prometheus_client import generate_latest
        return web.Response(body=generate_latest())


class RequestInterceptor:
    """Small shim used by tests to adapt different evaluator shapes."""

    def __init__(self, evaluator):
        self.evaluator = evaluator

    async def intercept(self, request):
        if hasattr(self.evaluator, 'evaluate'):
            return await self.evaluator.evaluate(request)
        return {'action': 'allow'}