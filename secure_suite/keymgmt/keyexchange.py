"""RSA-based session key wrapping."""

from __future__ import annotations

from secure_suite.crypto.public_key import rsa_decrypt_oaep, rsa_encrypt_oaep


def wrap_session_key(peer_pub_pem: bytes | str, session_key: bytes) -> bytes:
    """Wrap a session key with the peer's RSA public key."""
    return rsa_encrypt_oaep(peer_pub_pem, session_key)


def unwrap_session_key(
    my_priv_pem: bytes | str, blob: bytes, passphrase: str | bytes | None = None
) -> bytes:
    """Unwrap a session key with the local RSA private key."""
    return rsa_decrypt_oaep(my_priv_pem, blob, passphrase=passphrase)
