# adfree_proxy/utils.py

import base64

def normalize_header_name(name: str) -> str:
    """Convierte 'Adfree-Policy' -> 'adfree-policy'"""
    return name.lower().replace('_', '-')

def safe_b64decode(b64_str: str) -> bytes:
    """Decodifica base64url con padding seguro."""
    padding = '=' * (4 - len(b64_str) % 4)
    return base64.urlsafe_b64decode(b64_str + padding)