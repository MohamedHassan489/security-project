# Test Plan and Results

## Overview

This document records the verification strategy for the Secure Communication Suite and the
actual outcomes observed during execution. The suite uses Python `unittest` only, as required
by the project plan.

## Automated Test Matrix

| Test ID | File | Input / Scenario | Expected Result | Actual Result | Status |
|---|---|---|---|---|---|
| T-BC-01 | `tests/test_block_cipher.py` | AES-GCM round-trip with 128/192/256-bit keys | Plaintext is recovered exactly | Passed | PASS |
| T-BC-02 | `tests/test_block_cipher.py` | Tampered ciphertext | Authentication failure raised | Passed | PASS |
| T-BC-03 | `tests/test_block_cipher.py` | Tampered tag and AAD | Authentication failure raised | Passed | PASS |
| T-BC-04 | `tests/test_block_cipher.py` | AES-CBC teaching-variant round-trip | Plaintext is recovered exactly | Passed | PASS |
| T-PK-01 | `tests/test_public_key.py` | RSA-OAEP encrypt/decrypt | Plaintext is recovered exactly | Passed | PASS |
| T-PK-02 | `tests/test_public_key.py` | RSA-PSS sign/verify | Valid signature accepted; tampered message rejected | Passed | PASS |
| T-PK-03 | `tests/test_public_key.py` | Encrypted private-key serialization | Key can be used with passphrase | Passed | PASS |
| T-H-01 | `tests/test_hashing.py` | SHA-256 of `abc` | Matches NIST known-answer vector | Passed | PASS |
| T-H-02 | `tests/test_hashing.py` | HMAC-SHA256 RFC 4231 vector | Digest matches published test vector | Passed | PASS |
| T-H-03 | `tests/test_hashing.py` | File hashing | Result matches `hashlib` | Passed | PASS |
| T-KM-01 | `tests/test_keystore.py` | Save/load keystore with correct passphrase | Records decrypt successfully | Passed | PASS |
| T-KM-02 | `tests/test_keystore.py` | Wrong keystore passphrase | Load fails | Passed | PASS |
| T-KM-03 | `tests/test_keystore.py` | Tampered keystore ciphertext | Load fails | Passed | PASS |
| T-AU-01 | `tests/test_auth.py` | Register and verify correct password | Verification returns `True` | Passed | PASS |
| T-AU-02 | `tests/test_auth.py` | Wrong password | Verification returns `False` | Passed | PASS |
| T-AU-03 | `tests/test_auth.py` | Timing sanity check | No extreme timing skew between correct/incorrect paths | Passed | PASS |
| T-PR-01 | `tests/test_protocol.py` | Frame encode/decode | Payload round-trips exactly | Passed | PASS |
| T-PR-02 | `tests/test_protocol.py` | Truncated frame | Exception raised | Passed | PASS |
| T-PR-03 | `tests/test_protocol.py` | Replayed protected record | Replay rejected | Passed | PASS |
| T-INT-01 | `tests/test_integration.py` | Two clients register, login, send/fetch message | Recipient receives expected plaintext | Passed | PASS |
| T-INT-02 | `tests/test_integration.py` | Inspect captured wire bytes during message send | No plaintext message appears on wire | Passed | PASS |
| T-INT-03 | `tests/test_integration.py` | Tampered protected frame | Connection or request fails | Passed | PASS |

## Test Suite Command

```bash
python3 -m unittest discover -s tests -v
```

## Latest Automated Run

The latest full suite execution produced:

- Total tests: 23
- Result: `OK`
- Runtime: approximately 5 seconds on the development machine

## Performance Results

The benchmark command used is:

```bash
python3 scripts/benchmark.py
```

The latest measured values are recorded in the report and summarized below:

| Metric | Value |
|---|---:|
| AES encrypt+decrypt throughput (MB/s) | 89.53 |
| RSA encrypt operations per second | 3180.83 |
| RSA decrypt operations per second | 47.18 |
| RSA sign operations per second | 46.85 |
| RSA verify operations per second | 3322.31 |

## Manual Demo Checklist

1. Start server with `python3 -m secure_suite server`.
2. Register and login from the CLI client.
3. Register and login from the Tkinter GUI client.
4. Send a message and fetch it from the other client.
5. Inspect `keystore.bin` with `hexdump -C keystore.bin | head`.
6. Capture loopback traffic and confirm that plaintext does not appear.
