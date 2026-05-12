"""RSA helpers for encryption and signatures."""

from __future__ import annotations

from typing import Tuple

from Crypto.Cipher import PKCS1_OAEP
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA
from Crypto.Signature import pss


def generate_rsa_keypair(bits: int = 2048, passphrase: str | bytes | None = None) -> Tuple[bytes, bytes]:
    """Generate an RSA private/public PEM pair."""
    key = RSA.generate(bits)
    if passphrase:
        private_pem = key.export_key(
            format="PEM",
            passphrase=passphrase,
            pkcs=8,
            protection="PBKDF2WithHMAC-SHA1AndAES256-CBC",
        )
    else:
        private_pem = key.export_key(format="PEM")
    public_pem = key.publickey().export_key(format="PEM")
    return private_pem, public_pem


def load_private_key(priv_pem: bytes | str, passphrase: str | bytes | None = None) -> RSA.RsaKey:
    """Import an RSA private key."""
    return RSA.import_key(priv_pem, passphrase=passphrase)


def load_public_key(pub_pem: bytes | str) -> RSA.RsaKey:
    """Import an RSA public key."""
    return RSA.import_key(pub_pem)


def rsa_encrypt_oaep(pub_pem: bytes | str, data: bytes) -> bytes:
    """Encrypt a message with RSA-OAEP using SHA-256."""
    public_key = load_public_key(pub_pem)
    cipher = PKCS1_OAEP.new(public_key, hashAlgo=SHA256)
    return cipher.encrypt(data)


def rsa_decrypt_oaep(
    priv_pem: bytes | str, ciphertext: bytes, passphrase: str | bytes | None = None
) -> bytes:
    """Decrypt an RSA-OAEP ciphertext."""
    private_key = load_private_key(priv_pem, passphrase=passphrase)
    cipher = PKCS1_OAEP.new(private_key, hashAlgo=SHA256)
    return cipher.decrypt(ciphertext)


def rsa_sign_pss(priv_pem: bytes | str, message: bytes, passphrase: str | bytes | None = None) -> bytes:
    """Sign a message with RSA-PSS using SHA-256."""
    private_key = load_private_key(priv_pem, passphrase=passphrase)
    digest = SHA256.new(message)
    signer = pss.new(private_key)
    return signer.sign(digest)


def rsa_verify_pss(pub_pem: bytes | str, message: bytes, signature: bytes) -> bool:
    """Verify an RSA-PSS signature."""
    public_key = load_public_key(pub_pem)
    digest = SHA256.new(message)
    verifier = pss.new(public_key)
    try:
        verifier.verify(digest, signature)
        return True
    except (ValueError, TypeError):
        return False
