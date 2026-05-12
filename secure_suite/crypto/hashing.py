"""SHA-256 and HMAC helpers."""

from __future__ import annotations

import hmac
from hashlib import pbkdf2_hmac, sha256
from pathlib import Path


DEFAULT_PBKDF2_ITERS = 200_000
FILE_CHUNK_SIZE = 64 * 1024


def sha256_bytes(data: bytes) -> str:
    """Return the hex SHA-256 digest of a byte string."""
    return sha256(data).hexdigest()


def sha256_file(path: str | Path, chunk: int = FILE_CHUNK_SIZE) -> str:
    """Hash a file incrementally with SHA-256."""
    digest = sha256()
    with Path(path).open("rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def hmac_sha256(key: bytes, data: bytes) -> str:
    """Return the hex HMAC-SHA256 digest."""
    return hmac.new(key, data, sha256).hexdigest()


def pbkdf2_sha256(password: str, salt: bytes, iterations: int = DEFAULT_PBKDF2_ITERS) -> bytes:
    """Derive a key with PBKDF2-HMAC-SHA256."""
    return pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
