"""Tests for symmetric encryption helpers."""

from __future__ import annotations

import unittest

from secure_suite.crypto.block_cipher import (
    QueueEncryptionBridge,
    aes_cbc_decrypt,
    aes_cbc_encrypt,
    aes_gcm_decrypt,
    aes_gcm_encrypt,
    generate_aes_key,
)


class BlockCipherTests(unittest.TestCase):
    def test_aes_gcm_round_trip_for_supported_key_sizes(self) -> None:
        plaintext = b"confidential message"
        aad = b"header"
        for size in (16, 24, 32):
            key = generate_aes_key(size)
            nonce, ciphertext, tag = aes_gcm_encrypt(key, plaintext, aad)
            self.assertEqual(aes_gcm_decrypt(key, nonce, ciphertext, tag, aad), plaintext)

    def test_aes_gcm_rejects_tampered_ciphertext(self) -> None:
        key = generate_aes_key()
        nonce, ciphertext, tag = aes_gcm_encrypt(key, b"attack at dawn", b"aad")
        tampered = bytearray(ciphertext)
        tampered[0] ^= 0x01
        with self.assertRaises(ValueError):
            aes_gcm_decrypt(key, nonce, bytes(tampered), tag, b"aad")

    def test_aes_gcm_rejects_tampered_tag(self) -> None:
        key = generate_aes_key()
        nonce, ciphertext, tag = aes_gcm_encrypt(key, b"attack at dawn", b"aad")
        tampered = bytearray(tag)
        tampered[-1] ^= 0x01
        with self.assertRaises(ValueError):
            aes_gcm_decrypt(key, nonce, ciphertext, bytes(tampered), b"aad")

    def test_aes_gcm_rejects_tampered_aad(self) -> None:
        key = generate_aes_key()
        nonce, ciphertext, tag = aes_gcm_encrypt(key, b"attack at dawn", b"aad")
        with self.assertRaises(ValueError):
            aes_gcm_decrypt(key, nonce, ciphertext, tag, b"changed")

    def test_aes_cbc_round_trip(self) -> None:
        key = generate_aes_key()
        iv, ciphertext = aes_cbc_encrypt(key, b"cbc payload")
        self.assertEqual(aes_cbc_decrypt(key, iv, ciphertext), b"cbc payload")

    def test_spec_worker_bridge_encrypts(self) -> None:
        bridge = QueueEncryptionBridge()
        try:
            ciphertext, tag = bridge.encrypt(b"queue payload")
            self.assertNotEqual(ciphertext, b"queue payload")
            self.assertEqual(len(tag), 16)
        finally:
            bridge.stop()


if __name__ == "__main__":
    unittest.main()
