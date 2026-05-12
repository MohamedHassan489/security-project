"""Signed session tokens."""

from __future__ import annotations

import base64
import json
import time
from typing import Any

from Crypto.Random import get_random_bytes

from secure_suite.crypto.public_key import rsa_sign_pss, rsa_verify_pss


DEFAULT_TOKEN_TTL = 3600


def _canonical_payload(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def issue_token(
    private_key_pem: bytes | str, username: str, ttl_seconds: int = DEFAULT_TOKEN_TTL
) -> dict[str, str]:
    """Issue a signed token for a username."""
    payload = {
        "user": username,
        "exp": int(time.time()) + ttl_seconds,
        "nonce": get_random_bytes(12).hex(),
    }
    payload_bytes = _canonical_payload(payload)
    signature = rsa_sign_pss(private_key_pem, payload_bytes)
    return {
        "payload": base64.b64encode(payload_bytes).decode("ascii"),
        "signature": base64.b64encode(signature).decode("ascii"),
    }


def verify_token(public_key_pem: bytes | str, token: dict[str, str]) -> dict[str, Any]:
    """Verify a signed token and return its payload."""
    try:
        payload_bytes = base64.b64decode(token["payload"])
        signature = base64.b64decode(token["signature"])
        if not rsa_verify_pss(public_key_pem, payload_bytes, signature):
            raise ValueError("Invalid token signature")
        payload = json.loads(payload_bytes.decode("utf-8"))
        if int(payload["exp"]) < int(time.time()):
            raise ValueError("Token expired")
        return payload
    except Exception as exc:
        raise ValueError("Invalid token") from exc
