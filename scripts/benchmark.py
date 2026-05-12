"""Measure cryptographic throughput for the project report."""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from secure_suite.crypto.block_cipher import aes_gcm_decrypt, aes_gcm_encrypt, generate_aes_key
from secure_suite.crypto.public_key import (
    generate_rsa_keypair,
    rsa_decrypt_oaep,
    rsa_encrypt_oaep,
    rsa_sign_pss,
    rsa_verify_pss,
)


def measure_aes(iterations: int, payload_size: int) -> dict[str, float]:
    key = generate_aes_key()
    payload = b"A" * payload_size
    start = time.perf_counter()
    for _ in range(iterations):
        nonce, ciphertext, tag = aes_gcm_encrypt(key, payload)
        aes_gcm_decrypt(key, nonce, ciphertext, tag)
    elapsed = time.perf_counter() - start
    processed_megabytes = (payload_size * iterations) / (1024 * 1024)
    return {
        "iterations": iterations,
        "payload_bytes": payload_size,
        "elapsed_seconds": elapsed,
        "encrypt_decrypt_mb_per_s": processed_megabytes / elapsed,
    }


def measure_rsa(iterations: int) -> dict[str, float]:
    private_key, public_key = generate_rsa_keypair()
    plaintext = b"session-key-32-bytes-material!!!"
    start_encrypt = time.perf_counter()
    ciphertexts = [rsa_encrypt_oaep(public_key, plaintext) for _ in range(iterations)]
    encrypt_elapsed = time.perf_counter() - start_encrypt

    start_decrypt = time.perf_counter()
    for ciphertext in ciphertexts:
        rsa_decrypt_oaep(private_key, ciphertext)
    decrypt_elapsed = time.perf_counter() - start_decrypt

    message = b"benchmark message"
    start_sign = time.perf_counter()
    signatures = [rsa_sign_pss(private_key, message) for _ in range(iterations)]
    sign_elapsed = time.perf_counter() - start_sign

    start_verify = time.perf_counter()
    for signature in signatures:
        rsa_verify_pss(public_key, message, signature)
    verify_elapsed = time.perf_counter() - start_verify

    return {
        "iterations": iterations,
        "rsa_encrypt_ops_per_s": iterations / encrypt_elapsed,
        "rsa_decrypt_ops_per_s": iterations / decrypt_elapsed,
        "rsa_sign_ops_per_s": iterations / sign_elapsed,
        "rsa_verify_ops_per_s": iterations / verify_elapsed,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark secure suite primitives")
    parser.add_argument("--aes-iterations", type=int, default=64)
    parser.add_argument("--aes-payload-bytes", type=int, default=1024 * 1024)
    parser.add_argument("--rsa-iterations", type=int, default=50)
    args = parser.parse_args()

    results = {
        "aes": measure_aes(args.aes_iterations, args.aes_payload_bytes),
        "rsa": measure_rsa(args.rsa_iterations),
    }
    print(json.dumps(results, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
