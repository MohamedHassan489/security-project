% Secure Communication Suite
% TODO_TEAM_NAME
% CSE451 Computer and Network Security

# Secure Communication Suite

- Secure messaging application built in Python
- Integrates block cipher, public key, hashing, key management, authentication, and secure internet services
- Submission target: working code, report, and demonstration

---

# Problem Statement and User Stories

- Users need confidential message exchange over a network
- Keys must be shared securely and stored safely
- Messages must be checked for integrity
- Access must be limited to authenticated users
- The full workflow must demonstrate internet-service security

---

# Architecture Overview

- `crypto/`: AES-256-GCM, RSA-2048, SHA-256 helpers
- `keymgmt/`: encrypted keystore and RSA-wrapped session keys
- `auth/`: PBKDF2 password verification and signed tokens
- `net/`: framing, record protection, threaded server, shared client core
- `ui/`: CLI client and Tkinter GUI using the same networking logic

---

# Block Cipher Module

- Production path uses AES-256-GCM
- Provides confidentiality and integrity in one step
- Record header includes version, type, and counter as authenticated data
- Assignment `EncryptionWorker` skeleton preserved verbatim and used by the server outbound queue

---

# Public-Key Module

- RSA-2048 key generation
- RSA-OAEP protects AES session-key delivery
- RSA-PSS signs session tokens
- Public-key cryptography is used only for small secrets and signatures, not bulk traffic

---

# Hashing Module

- SHA-256 for byte strings and files
- HMAC-SHA256 for keyed integrity support
- PBKDF2-HMAC-SHA256 with 200,000 iterations for password storage and keystore keys
- MD5 appears only in the report discussion and standalone demo script

---

# Key Management Module

- Server keypair stored in encrypted `keystore.bin`
- Keystore format stores `salt`, `nonce`, `tag`, and `ciphertext`
- Master key derived from passphrase using PBKDF2-HMAC-SHA256
- Hex dump does not reveal PEM plaintext

---

# Authentication Module

- User registration stores per-user salt and PBKDF2 hash
- Login verifies credentials with constant-time comparison
- Server issues signed token containing user, expiry, and nonce
- Subsequent requests carry token for authorization

---

# Internet Services Security Workflow

1. Client connects and sends RSA public key
2. Server returns its RSA public key
3. Server generates AES session key and wraps it with RSA-OAEP
4. Client logs in over AES-GCM protected records
5. Client sends and fetches protected messages using signed token

---

# Testing Strategy

- 23 `unittest` cases
- Unit tests for crypto, keystore, auth, and protocol
- Integration tests for register/login/send/fetch flow
- Explicit proof that plaintext does not appear on the wire
- Tampering test that forces request failure or disconnect

---

# Results

- Full suite status: all tests pass
- Message delivery works end-to-end
- Replay and tampering are rejected
- CLI and GUI both operate against the same client core

| Metric | Value |
|---|---:|
| AES encrypt+decrypt throughput (MB/s) | 89.53 |
| RSA encrypt ops/s | 3180.83 |
| RSA decrypt ops/s | 47.18 |

---

# Threat Model and Security Discussion

- Network attacker can observe and alter packets
- AES-GCM blocks plaintext disclosure and detects tampering
- Replay counters reject reused records
- PBKDF2 slows offline password guessing
- AES-GCM keystore protects server private keys at rest

---

# Limitations and Future Work

- Educational transport layer, not production TLS
- In-memory message queue instead of durable storage
- No MFA or certificate chain validation
- Future work: ECC, persistent mailboxes, stronger account management, TLS integration

---

# Live Demo Plan

- Start server with `python3 -m secure_suite server`
- Register/login from CLI and GUI
- Send message from one client to the other
- Show encrypted `keystore.bin`
- Show that the wire capture contains no message plaintext

---

# Questions

- Why AES-GCM instead of DES or MD5-based approaches?
- How does the signed token strengthen authentication?
- How would the design change for production deployment?
