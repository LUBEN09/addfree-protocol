"""Request/Response interception utilities"""
from typing import Any, Dict


class RequestInterceptor:
    def __init__(self, evaluator):
        self.evaluator = evaluator

    async def intercept(self, request) -> Dict[str, Any]:
        """Inspect request and return decision metadata."""
        # Extract minimal request_info
        request_info = {"path": str(request.rel_url), "method": request.method}
        decision = self.evaluator.evaluate(request_info)
        return decision


class ResponseModifier:
    def modify(self, response, decision: Dict[str, Any]):
        """Modify response based on decision (placeholder)."""
        if decision.get('action') == 'block':
            return b''
        return response
