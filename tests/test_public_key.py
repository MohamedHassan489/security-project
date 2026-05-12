"""Tests for RSA helpers."""

from __future__ import annotations

import unittest

from secure_suite.crypto.public_key import (
    generate_rsa_keypair,
    rsa_decrypt_oaep,
    rsa_encrypt_oaep,
    rsa_sign_pss,
    rsa_verify_pss,
)


class PublicKeyTests(unittest.TestCase):
    def test_oaep_round_trip(self) -> None:
        private_pem, public_pem = generate_rsa_keypair()
        ciphertext = rsa_encrypt_oaep(public_pem, b"shared secret")
        plaintext = rsa_decrypt_oaep(private_pem, ciphertext)
        self.assertEqual(plaintext, b"shared secret")

    def test_pss_sign_and_verify(self) -> None:
        private_pem, public_pem = generate_rsa_keypair()
        message = b"important message"
        signature = rsa_sign_pss(private_pem, message)
        self.assertTrue(rsa_verify_pss(public_pem, message, signature))
        self.assertFalse(rsa_verify_pss(public_pem, message + b"!", signature))

    def test_key_serialization_with_passphrase(self) -> None:
        private_pem, public_pem = generate_rsa_keypair(passphrase="secret-pass")
        ciphertext = rsa_encrypt_oaep(public_pem, b"protected")
        plaintext = rsa_decrypt_oaep(private_pem, ciphertext, passphrase="secret-pass")
        self.assertEqual(plaintext, b"protected")


if __name__ == "__main__":
    unittest.main()
