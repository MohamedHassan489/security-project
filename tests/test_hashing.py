"""Tests for hashing helpers."""

from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from secure_suite.crypto.hashing import hmac_sha256, sha256_bytes, sha256_file


class HashingTests(unittest.TestCase):
    def test_sha256_known_answer(self) -> None:
        self.assertEqual(
            sha256_bytes(b"abc"),
            "ba7816bf8f01cfea414140de5dae2223"
            "b00361a396177a9cb410ff61f20015ad",
        )

    def test_hmac_rfc_4231_vector(self) -> None:
        key = bytes.fromhex("0b" * 20)
        data = b"Hi There"
        self.assertEqual(
            hmac_sha256(key, data),
            "b0344c61d8db38535ca8afceaf0bf12b"
            "881dc200c9833da726e9376c2e32cff7",
        )

    def test_file_hash_matches_hashlib(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.bin"
            payload = b"file hashing test payload"
            path.write_bytes(payload)
            self.assertEqual(sha256_file(path), hashlib.sha256(payload).hexdigest())


if __name__ == "__main__":
    unittest.main()
