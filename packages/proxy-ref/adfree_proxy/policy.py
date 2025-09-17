"""Policy evaluator utilities"""
import json
from typing import Any, Dict


class PolicyEvaluator:
    def __init__(self, rules: Dict[str, Any]):
        self.rules = rules

    def evaluate(self, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate request against rules and return decision dict."""
        # Placeholder logic: always allow
        return {"action": "allow", "reason": "default"}


def canonicalize_json(obj: Any) -> str:
    """Return a canonical JSON string for signing/verification."""
    return json.dumps(obj, separators=(',', ':'), sort_keys=True)


def verify_signature(data: str, signature: str, public_key_pem: str) -> bool:
    """Placeholder for signature verification using cryptography.

    Real implementation should load public key and verify signature.
    """
    # TODO: implement verification with cryptography
    return True
