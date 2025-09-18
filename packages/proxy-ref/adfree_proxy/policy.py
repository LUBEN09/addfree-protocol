# adfree_proxy/policy.py

import json
from typing import Dict, Any, Optional, Literal
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import load_pem_public_key
from cryptography.exceptions import InvalidSignature
from pydantic import BaseModel, Field, validator
import aiohttp
import logging

logger = logging.getLogger(__name__)

class BotPolicy(BaseModel):
    allowed: bool = False
    payment_required: bool = True
    payment_url: str
    rate_limit: Optional[Dict[str, Any]] = None

class AdfreePolicy(BaseModel):
    version: Literal["1"] = "1"
    mode: str  # "strict" | "relaxed" | "report-only"
    max_ads_per_page: int = 3
    allow_redirects: bool = False
    allow_iframes: list[str] = Field(default_factory=lambda: ["self"])
    blocked_domains: list[str] = Field(default_factory=list)
    report_to: Optional[str] = None
    bot_policy: Optional[BotPolicy] = None

    @validator('mode')
    def validate_mode(cls, v):
        if v not in {"strict", "relaxed", "report-only"}:
            raise ValueError('mode must be "strict", "relaxed", or "report-only"')
        return v

def canonicalize_json(data: Dict[str, Any]) -> bytes:
    """
    Canonicaliza JSON ordenando recursivamente las claves.
    NOTA: Esto es una simplificación. Para producción, usar JSON Canonicalization Scheme (JCS).
    """
    def _sorted_dict(d):
        if isinstance(d, dict):
            return {k: _sorted_dict(v) for k, v in sorted(d.items())}
        elif isinstance(d, list):
            return [_sorted_dict(i) for i in d]
        else:
            return d
    sorted_data = _sorted_dict(data)
    return json.dumps(sorted_data, separators=(',', ':'), sort_keys=True).encode('utf-8')


class PolicyEvaluator:
    """Shim used by tests: a minimal evaluator interface.
    In real code this would apply policy logic to requests.
    """
    def __init__(self, policy_dict: Dict[str, Any]):
        self.policy = policy_dict or {}

    async def evaluate(self, request: Any) -> Dict[str, Any]:
        # Minimal behaviour: always allow
        return {"action": "allow"}

async def fetch_public_key(origin: str) -> bytes:
    """
    Obtiene la clave pública JWK desde .well-known
    """
    url = f"https://{origin}/.well-known/adfree-policy-key"
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status == 200:
                    jwk_data = await resp.json()
                    # Convertir JWK a PEM (simplificado, solo para clave EC P-256)
                    # En producción, usar python-jose o similar
                    from python_jose import jwk
                    key = jwk.construct(jwk_data)
                    return key.to_pem()
                else:
                    logger.error(f"Failed to fetch key from {url}: {resp.status}")
                    return None
        except Exception as e:
            logger.error(f"Error fetching public key: {e}")
            return None

def verify_policy_signature(policy_json: Dict[str, Any], signature_b64: str, public_key_pem: bytes) -> bool:
    """
    Verifica la firma ES256 sobre el JSON canonicalizado.
    """
    try:
        canonical_data = canonicalize_json(policy_json)
        signature = base64.urlsafe_b64decode(signature_b64 + '==')  # padding

        public_key = load_pem_public_key(public_key_pem)
        if not isinstance(public_key, ec.EllipticCurvePublicKey):
            raise ValueError("Public key is not an EC key")

        public_key.verify(
            signature,
            canonical_data,
            ec.ECDSA(hashes.SHA256())
        )
        return True
    except (InvalidSignature, Exception) as e:
        logger.warning(f"Signature verification failed: {e}")
        return False

async def validate_policy(policy_json: Dict[str, Any], signature_b64: str, origin: str) -> Optional[AdfreePolicy]:
    """
    Valida esquema y firma de la política.
    Retorna objeto AdfreePolicy si es válida, None si no.
    """
    try:
        # Validar esquema
        policy_obj = AdfreePolicy.parse_obj(policy_json)

        # Obtener clave pública
        public_key_pem = await fetch_public_key(origin)
        if not public_key_pem:
            return None

        # Verificar firma
        if not verify_policy_signature(policy_json, signature_b64, public_key_pem):
            return None

        return policy_obj

    except Exception as e:
        logger.error(f"Policy validation error: {e}")
        return None