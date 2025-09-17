"""Reporting client for sending events to portal or collector."""
import asyncio
from typing import Any, Dict


class ReportClient:
    def __init__(self, endpoint: str):
        self.endpoint = endpoint

    async def send(self, event: Dict[str, Any]):
        """Send event asynchronously (placeholder)."""
        # Implement actual HTTP client call here (aiohttp)
        await asyncio.sleep(0)
