"""Tests for the encrypted keystore."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from secure_suite.keymgmt.keystore import Keystore


class KeystoreTests(unittest.TestCase):
    def test_save_and_load_with_correct_passphrase(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "keystore.bin"
            store = Keystore.open(path, "secret")
            store.put("alice", {"private": "value"})
            store.save()

            reloaded = Keystore.open(path, "secret")
            self.assertEqual(reloaded.get("alice"), {"private": "value"})

    def test_wrong_passphrase_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "keystore.bin"
            store = Keystore.open(path, "secret")
            store.put("alice", {"private": "value"})
            store.save()

            with self.assertRaises(ValueError):
                Keystore.open(path, "wrong")

    def test_tampered_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "keystore.bin"
            store = Keystore.open(path, "secret")
            store.put("alice", {"private": "value"})
            store.save()

            payload = json.loads(path.read_text(encoding="utf-8"))
            ciphertext = bytearray.fromhex(payload["ciphertext"])
            ciphertext[0] ^= 0x01
            payload["ciphertext"] = bytes(ciphertext).hex()
            path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaises(ValueError):
                Keystore.open(path, "secret")


if __name__ == "__main__":
    unittest.main()
