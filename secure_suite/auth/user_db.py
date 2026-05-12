"""Password-based user registry."""

from __future__ import annotations

import hmac
import json
from pathlib import Path

from Crypto.Random import get_random_bytes

from secure_suite.crypto.hashing import DEFAULT_PBKDF2_ITERS, pbkdf2_sha256


USER_SALT_SIZE = 16


class UserDatabase:
    """Simple JSON user database."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._users = self._load()

    def register(self, username: str, password: str, rsa_pub_pem: str) -> None:
        if username in self._users:
            raise ValueError("User already exists")
        salt = get_random_bytes(USER_SALT_SIZE)
        derived = pbkdf2_sha256(password, salt, DEFAULT_PBKDF2_ITERS)
        self._users[username] = {
            "salt_hex": salt.hex(),
            "pbkdf2_hex": derived.hex(),
            "iters": DEFAULT_PBKDF2_ITERS,
            "rsa_pub_pem": rsa_pub_pem,
        }
        self._save()

    def verify(self, username: str, password: str) -> bool:
        record = self._users.get(username)
        if not record:
            return False
        salt = bytes.fromhex(record["salt_hex"])
        expected = bytes.fromhex(record["pbkdf2_hex"])
        candidate = pbkdf2_sha256(password, salt, int(record["iters"]))
        return hmac.compare_digest(candidate, expected)

    def get_public_key(self, username: str) -> str | None:
        record = self._users.get(username)
        return None if record is None else record["rsa_pub_pem"]

    def _load(self) -> dict[str, dict[str, str | int]]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self) -> None:
        self.path.write_text(json.dumps(self._users, indent=2, sort_keys=True), encoding="utf-8")
