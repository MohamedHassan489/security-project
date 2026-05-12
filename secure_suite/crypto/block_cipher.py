"""AES helpers for symmetric encryption workflows."""

from __future__ import annotations

import queue
import threading
from typing import Tuple

from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes


GCM_NONCE_SIZE = 12
GCM_TAG_SIZE = 16
DEFAULT_AES_KEY_SIZE = 32
BLOCK_SIZE = 16


def generate_aes_key(length: int = DEFAULT_AES_KEY_SIZE) -> bytes:
    """Return a random AES key with a valid length."""
    if length not in (16, 24, 32):
        raise ValueError("AES key length must be 16, 24, or 32 bytes")
    return get_random_bytes(length)


def aes_gcm_encrypt(
    key: bytes, plaintext: bytes, aad: bytes = b""
) -> Tuple[bytes, bytes, bytes]:
    """Encrypt plaintext with AES-GCM and return nonce, ciphertext, and tag."""
    cipher = AES.new(key, AES.MODE_GCM, nonce=get_random_bytes(GCM_NONCE_SIZE))
    if aad:
        cipher.update(aad)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce, ciphertext, tag


def aes_gcm_decrypt(
    key: bytes,
    nonce: bytes,
    ciphertext: bytes,
    tag: bytes,
    aad: bytes = b"",
) -> bytes:
    """Decrypt and authenticate an AES-GCM payload."""
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    if aad:
        cipher.update(aad)
    return cipher.decrypt_and_verify(ciphertext, tag)


def _pkcs7_pad(data: bytes) -> bytes:
    pad_len = BLOCK_SIZE - (len(data) % BLOCK_SIZE)
    return data + bytes([pad_len]) * pad_len


def _pkcs7_unpad(data: bytes) -> bytes:
    if not data or len(data) % BLOCK_SIZE != 0:
        raise ValueError("Invalid padded data")
    pad_len = data[-1]
    if pad_len < 1 or pad_len > BLOCK_SIZE:
        raise ValueError("Invalid PKCS#7 padding")
    if data[-pad_len:] != bytes([pad_len]) * pad_len:
        raise ValueError("Invalid PKCS#7 padding")
    return data[:-pad_len]


def aes_cbc_encrypt(key: bytes, plaintext: bytes) -> Tuple[bytes, bytes]:
    """Encrypt plaintext with AES-CBC and PKCS#7 padding."""
    iv = get_random_bytes(BLOCK_SIZE)
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    ciphertext = cipher.encrypt(_pkcs7_pad(plaintext))
    return iv, ciphertext


def aes_cbc_decrypt(key: bytes, iv: bytes, ciphertext: bytes) -> bytes:
    """Decrypt an AES-CBC payload and remove PKCS#7 padding."""
    cipher = AES.new(key, AES.MODE_CBC, iv=iv)
    plaintext = cipher.decrypt(ciphertext)
    return _pkcs7_unpad(plaintext)


class EncryptionWorker(threading.Thread):
    def __init__(self, plaintext_queue, ciphertext_queue):
        threading.Thread.__init__(self)
        self.plaintext_queue = plaintext_queue
        self.ciphertext_queue = ciphertext_queue
        self.key = get_random_bytes(16)  # AES key must be either 16, 24, or 32 bytes long
        self.cipher = AES.new(self.key, AES.MODE_EAX)

    def run(self):
        while True:
            plaintext = self.plaintext_queue.get()
            if plaintext is None:
                break
            ciphertext, tag = self.cipher.encrypt_and_digest(plaintext)
            self.ciphertext_queue.put((ciphertext, tag))


# Usage:
# plaintext_queue = queue.Queue()
# ciphertext_queue = queue.Queue()
# worker = EncryptionWorker(plaintext_queue, ciphertext_queue)
# worker.start()
# ...
# worker.join()


class QueueEncryptionBridge:
    """Adapt the spec-mandated worker to request/response encryption calls."""

    def __init__(self) -> None:
        self.plaintext_queue: "queue.Queue[bytes | None]" | None = None
        self.ciphertext_queue: "queue.Queue[Tuple[bytes, bytes]]" | None = None
        self.worker: EncryptionWorker | None = None

    def _start_worker(self) -> None:
        self.plaintext_queue = queue.Queue()
        self.ciphertext_queue = queue.Queue()
        self.worker = EncryptionWorker(self.plaintext_queue, self.ciphertext_queue)
        self.worker.daemon = True
        self.worker.start()

    def encrypt(self, plaintext: bytes) -> Tuple[bytes, bytes]:
        self.stop()
        self._start_worker()
        assert self.plaintext_queue is not None
        assert self.ciphertext_queue is not None
        self.plaintext_queue.put(plaintext)
        result = self.ciphertext_queue.get()
        self.plaintext_queue.put(None)
        if self.worker is not None:
            self.worker.join(timeout=1)
        return result

    def stop(self) -> None:
        if self.worker is not None and self.worker.is_alive():
            assert self.plaintext_queue is not None
            self.plaintext_queue.put(None)
            self.worker.join(timeout=1)
        self.worker = None
        self.plaintext_queue = None
        self.ciphertext_queue = None
