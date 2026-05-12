"""Encrypted keystore for private application data."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from Crypto.Random import get_random_bytes

from secure_suite.crypto.block_cipher import aes_gcm_decrypt, aes_gcm_encrypt
from secure_suite.crypto.hashing import DEFAULT_PBKDF2_ITERS, pbkdf2_sha256


KEYSTORE_SALT_SIZE = 16


@dataclass
class Keystore:
    """JSON-backed encrypted keystore."""

    path: Path
    passphrase: str
    records: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def open(cls, path: str | Path, passphrase: str) -> "Keystore":
        keystore = cls(path=Path(path), passphrase=passphrase)
        if keystore.path.exists():
            keystore._load()
        return keystore

    def put(self, name: str, value: Any) -> None:
        self.records[name] = value

    def get(self, name: str, default: Any = None) -> Any:
        return self.records.get(name, default)

    def save(self) -> None:
        salt = get_random_bytes(KEYSTORE_SALT_SIZE)
        key = pbkdf2_sha256(self.passphrase, salt, DEFAULT_PBKDF2_ITERS)
        plaintext = json.dumps(self.records, sort_keys=True).encode("utf-8")
        nonce, ciphertext, tag = aes_gcm_encrypt(key, plaintext)
        payload = {
            "salt": salt.hex(),
            "nonce": nonce.hex(),
            "tag": tag.hex(),
            "ciphertext": ciphertext.hex(),
        }
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")

    def _load(self) -> None:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            salt = bytes.fromhex(payload["salt"])
            nonce = bytes.fromhex(payload["nonce"])
            tag = bytes.fromhex(payload["tag"])
            ciphertext = bytes.fromhex(payload["ciphertext"])
            key = pbkdf2_sha256(self.passphrase, salt, DEFAULT_PBKDF2_ITERS)
            plaintext = aes_gcm_decrypt(key, nonce, ciphertext, tag)
            self.records = json.loads(plaintext.decode("utf-8"))
        except Exception as exc:
            raise ValueError("Unable to open keystore") from exc
