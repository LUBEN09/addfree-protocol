# adfree_proxy/reporter.py

import asyncio
import json
import logging
import time
from typing import Dict, Any, Optional
from aiohttp import ClientSession, ClientError
from .metrics import REPORT_SENT, REPORT_FAILED

logger = logging.getLogger(__name__)

class ReportClient:
    def __init__(self, session: ClientSession):
        self.session = session

    async def send_report(self, report_to: str, report_data: Dict[str, Any], max_retries: int = 3) -> bool:
        """
        Envía un informe a la URL report_to de forma asíncrona y con reintentos.
        Retorna True si se envió con éxito, False en caso contrario.
        """
        if not report_to:
            logger.warning("No report_to URL provided. Skipping report.")
            return False

        # Añadir timestamp y versión al reporte
        payload = {
            "version": "1.0",
            "generated_at": time.time(),
            **report_data
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Adfree-Proxy/0.1"
        }

        for attempt in range(max_retries + 1):
            try:
                async with self.session.post(report_to, json=payload, headers=headers, timeout=10) as resp:
                    if resp.status in (200, 201, 202, 204):
                        logger.info(f"Report sent successfully to {report_to}")
                        REPORT_SENT.labels(endpoint=report_to, status=str(resp.status)).inc()
                        return True
                    else:
                        logger.warning(f"Report failed with status {resp.status} on attempt {attempt + 1}")
                        REPORT_FAILED.labels(endpoint=report_to, reason=f"HTTP_{resp.status}").inc()

            except asyncio.TimeoutError:
                logger.warning(f"Timeout sending report to {report_to} (attempt {attempt + 1})")
                REPORT_FAILED.labels(endpoint=report_to, reason="timeout").inc()

            except ClientError as e:
                logger.error(f"Network error sending report to {report_to}: {e} (attempt {attempt + 1})")
                REPORT_FAILED.labels(endpoint=report_to, reason="network_error").inc()

            except Exception as e:
                logger.error(f"Unexpected error sending report to {report_to}: {e} (attempt {attempt + 1})")
                REPORT_FAILED.labels(endpoint=report_to, reason="unexpected_error").inc()

            # Si no es el último intento, esperar con backoff exponencial
            if attempt < max_retries:
                delay = 2 ** attempt  # 1s, 2s, 4s...
                logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)

        logger.error(f"Failed to send report to {report_to} after {max_retries + 1} attempts")
        return False

    async def report_policy_violation(self, policy: 'AdfreePolicy', violation: Dict[str, Any]):
        """
        Reporta una violación de política (ej: anuncio extra, iframe bloqueado, redirección bloqueada).
        Solo si policy.mode == "report-only" o si se quiere reportar en modo strict (opcional).
        """
        if not policy.report_to:
            return

        report_data = {
            "type": "policy_violation",
            "policy_mode": policy.mode,
            "violation": violation,
            "context": {
                "url": violation.get("url", "unknown"),
                "element": violation.get("element", "unknown"),
                "timestamp": time.time()
            }
        }

        # Enviar de forma fire-and-forget
        asyncio.create_task(self.send_report(policy.report_to, report_data))

    async def report_invalid_policy(self, origin: str, error: str, raw_policy: Optional[str] = None):
        """
        Reporta una política inválida o mal firmada.
        """
        report_data = {
            "type": "invalid_policy",
            "origin": origin,
            "error": error,
            "raw_policy": raw_policy[:1000] if raw_policy else None  # Truncar por seguridad
        }

        # Aquí podríamos tener un endpoint global de reporte de errores del protocolo
        # Por ahora, si no hay policy.report_to, no reportamos.
        # En el futuro, podríamos tener un fallback global.

        # NOTA: En este caso, no tenemos una política válida, así que no sabemos report_to.
        # Podríamos permitir un "global_report_to" en la configuración del proxy.
        # Por ahora, omitimos.
        logger.warning(f"Invalid policy from {origin}: {error}. No report_to available.")
        # En producción, enviarlo a un endpoint de monitoreo interno.