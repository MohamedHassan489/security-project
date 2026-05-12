# Secure Communication Suite: A Cryptography Application in Python

**Course:** CSE451 Computer and Network Security  
**University:** Ain Shams University  
**Team:** TODO_TEAM_NAME  
**Submission Date:** 2026-05-08

## Literature survey 25%

### Introduction

The Secure Communication Suite was designed as an educational security application that combines
multiple cryptographic building blocks into one coherent workflow. Instead of demonstrating each
algorithm in isolation, the project integrates symmetric encryption, public-key cryptography,
hashing, protected key storage, authentication, and a secure networked service. This matches the
 assignment specification, which requires a suite that protects both data in transit and data at
 rest.

### AES for the block cipher module

AES is the current industry-standard symmetric cipher and is standardized in NIST FIPS 197. It
supports 128-bit block size and multiple key sizes, making it suitable for both classroom study
and real-world secure systems. The project uses AES-256-GCM for the production path because GCM
provides confidentiality and integrity in one construction. The specification also provides a
threading-based AES worker skeleton; that worker is preserved verbatim in the implementation for
grading compatibility and is exercised by the server outbound queue. DES was not selected because
its 56-bit effective key size is obsolete and vulnerable to brute-force attacks.

### RSA for public-key cryptography

RSA remains one of the most widely taught public-key systems and is standardized in RFC 8017. In
this suite, RSA-2048 with OAEP is used to protect session-key distribution, while RSA-PSS is used
for signatures. That combination allows the server to encrypt AES session keys for clients and to
issue signed tokens that clients can verify. ECC was considered as a literature comparison point,
but RSA was selected because it aligns with the project’s goal of building transparent, easy-to-
explain cryptographic workflows for a university assessment.

### SHA-256 and password hashing

SHA-256, defined in FIPS 180-4, is used for data integrity and as the hash foundation for HMAC
and RSA signatures in the suite. Passwords are not stored with a plain hash; instead, the project
uses PBKDF2-HMAC-SHA256 with at least 200,000 iterations and a unique per-user salt. This slows
offline guessing attacks and demonstrates secure credential handling. MD5 is discussed only as a
weak legacy algorithm in the report and the standalone demo script. It is intentionally excluded
from the production code path.

### Related key-management and authentication practice

A secure system must protect keys not only on the network but also on disk. For that reason, the
project stores sensitive key material inside an encrypted keystore protected by AES-GCM, with the
encryption key derived from a master passphrase using PBKDF2-HMAC-SHA256. Authentication combines
password verification with a signed session token so that the project covers both password-based
and certificate-style identity concepts mentioned in the specification.

### Phase 1 Question: What are the key components of the Secure Communication Suite?

The key components are the block cipher module, public-key cryptosystem module, hashing module,
key management module, authentication module, and the internet-services security module that
integrates all of them into a secure messaging service.

### Phase 1 Question: What cryptographic techniques will be used in the project?

The project uses AES-256-GCM, RSA-2048 OAEP, RSA-2048 PSS, SHA-256, HMAC-SHA256, and
PBKDF2-HMAC-SHA256 with 200,000 iterations. AES-CBC is included only as a teaching comparison
variant inside the block-cipher module documentation and tests.

### Phase 1 Question: What are the main functions of each module in the suite?

- The block cipher module encrypts and authenticates records.
- The public-key module generates RSA keys, wraps session keys, and signs tokens.
- The hashing module provides SHA-256, HMAC-SHA256, and PBKDF2 support.
- The key-management module secures private material at rest.
- The authentication module verifies users and authorizes active sessions.
- The internet-services security module applies all previous modules to real TCP messaging.

## Research objectives 25%

### Project objectives derived from the user stories

The project objectives follow directly from the assignment user stories:

1. Build a block-cipher workflow that can encrypt messages before transmission.
2. Build a public-key workflow that can securely exchange session keys.
3. Build a hashing workflow that can verify integrity and support authenticated operations.
4. Build a key-management workflow that stores sensitive material securely.
5. Build an authentication workflow that verifies user identities before granting access.
6. Integrate all modules into an internet-services security application.

### Security and engineering objectives

The project was also designed around three engineering objectives. First, the suite had to use
modern algorithms rather than legacy weak ones in the production path. Second, the system had to
be testable, so every core behavior is backed by a `unittest` case. Third, the code had to be
demonstrable to graders, which is why the repository includes both a CLI client and a Tkinter GUI
that share the same protocol implementation.

### Phase 2 Question: How does the block cipher module work?

The block-cipher module exposes AES-GCM encrypt/decrypt helpers that generate a fresh nonce,
encrypt the plaintext, bind protocol metadata as additional authenticated data, and return a tag
that must verify before decryption succeeds. The same module also preserves the assignment’s
threaded AES worker skeleton and adapts it through a queue bridge so the server can use it on
outbound responses.

### Phase 2 Question: What is the role of the public key cryptosystem module?

The public-key module generates RSA key pairs, encrypts short secrets such as session keys with
RSA-OAEP, and signs session-token payloads with RSA-PSS. Its main role is to establish trust and
secure key exchange before symmetric encryption begins.

### Phase 2 Question: How does the hashing module ensure data integrity?

The hashing module computes SHA-256 digests over bytes and files and supplies HMAC-SHA256 support.
In the suite, integrity is also reinforced at the transport layer because AES-GCM will reject any
tampering with ciphertext, authentication tag, or bound metadata.

## Methodology 25%

### Phase-based implementation method

The development followed the four phases stated in the assignment specification:

1. Design and planning
2. Development of cryptographic modules
3. Development of key-management and authentication modules
4. Integration and testing

The design phase produced an SRS and architecture documentation before implementation. The
cryptographic phase implemented the reusable primitives first, because all higher-level modules
depend on them. The key-management and authentication phase then added secure storage and identity
verification. Finally, the integration phase combined all modules into a socket-based messaging
application and validated the result with automated and manual tests.

### System architecture and methodology choices

The system uses a layered structure so that cryptographic responsibilities remain separated. The
`crypto` package holds primitive operations. The `keymgmt` package uses those primitives for secure
storage and key wrapping. The `auth` package manages registration, password verification, and
session tokens. The `net` package applies the cryptographic layer to a real communication service.
The `ui` package then exposes the same client core through two interfaces. This structure reduces
duplication and supports focused testing.

### Handshake and secure transport methodology

When a client connects, it first sends an RSA public key in a `HELLO` message. The server replies
with its public key and sends a randomly generated 32-byte AES session key encrypted under the
client’s public key. Once the client unwraps the key, all subsequent application records are
carried inside AES-256-GCM protected frames. Each frame includes a monotonically increasing
counter in the authenticated header to reject replayed messages.

### Credential and token methodology

User registration stores a per-user random salt, a PBKDF2-HMAC-SHA256 derived password value, the
iteration count, and the user’s public key. Login verifies the password by recomputing the same
PBKDF2 output and comparing it with `hmac.compare_digest`. On success, the server issues a signed
token containing username, expiry, and nonce fields. That token is then attached to message and
fetch requests, so the application re-validates session authorization instead of trusting the
client blindly.

### Phase 3 Question: How does the key management module secure key distribution and storage?

The key-management module secures distribution by wrapping the AES session key with RSA-OAEP and
secures storage by encrypting the keystore file with AES-GCM. The keystore encryption key is
derived from a passphrase using PBKDF2-HMAC-SHA256 and a random salt, so the stored key material
is unreadable without the correct passphrase.

### Phase 3 Question: What authentication mechanisms are implemented in the authentication module?

The authentication module implements password-based authentication using PBKDF2-HMAC-SHA256 and
token-based authorization using RSA-PSS signatures. This satisfies the assignment’s requirement to
implement password-based or certificate-based authentication by combining both ideas in one
lightweight design.

### Phase 3 Question: How does the authentication module verify user identities?

The module verifies user identities by checking a password against a stored salted PBKDF2 value,
then by validating a server-signed token on subsequent requests. An attacker who tampers with the
token or replays an expired token cannot bypass verification.

## Analysis of results & conclusions 25%

### Test execution summary

The final automated test suite contains 23 unit and integration tests spanning all required
modules. These tests cover correct encryption/decryption, tamper detection, signing, hashing,
keystore protection, password verification, protocol framing, replay defense, end-to-end message
delivery, and transport tamper handling. The full command executed was:

```bash
python3 -m unittest discover -s tests -v
```

The final run completed successfully with all 23 tests passing.

### Phase 4 Question: How are the different modules integrated into the Secure Communication Suite?

Integration happens through the client/server protocol. The server uses RSA to establish an AES
session key, the authentication layer to verify users and issue tokens, the keystore to protect
its own private material, and the AES-GCM record layer to protect network messages. The CLI and
GUI both call the same client core, which ensures that the integration logic is implemented only
once and tested consistently.

### Phase 4 Question: What types of tests were conducted on the suite?

Three categories of tests were conducted:

1. Unit tests for cryptographic primitives and local storage behavior.
2. Protocol tests for framing, truncation handling, and replay rejection.
3. Integration tests for live registration, login, secure message transfer, plaintext absence on
   the wire, and disconnect behavior after tampering.

### Phase 4 Question: How does the suite secure internet services?

The suite secures internet services by applying cryptography at multiple layers. RSA protects the
session-key handshake, AES-256-GCM protects message confidentiality and integrity, counters defend
against replay, PBKDF2 protects stored passwords, and AES-GCM protects server key material on
disk. As a result, both transmitted messages and stored secrets are defended against common attack
classes expected in a classroom threat model.

### Performance measurements

The cryptographic performance was measured using `time.perf_counter()` on the development machine.
The benchmark script encrypts and decrypts repeated 1 MiB payloads and measures RSA encryption,
decryption, signing, and verification rates over multiple iterations.

| Metric | Value |
|---|---:|
| AES encrypt+decrypt throughput (MB/s) | 89.53 |
| RSA encrypt operations per second | 3180.83 |
| RSA decrypt operations per second | 47.18 |
| RSA sign operations per second | 46.85 |
| RSA verify operations per second | 3322.31 |

### Limitations

The suite is intentionally educational. It does not replace mature TLS implementations, does not
include multi-factor authentication, and uses in-memory mailbox handling rather than a durable
message database. The compatibility requirement to preserve the provided AES worker skeleton also
means the code carries a grading-driven legacy element alongside the modern AES-GCM record layer.

### Conclusions and future work

The project objectives were achieved: the suite combines the required cryptographic modules, uses
modern production algorithms, protects credentials and key material, secures message transport,
and provides both CLI and GUI demonstrations. Future work could include ECC-based key exchange,
certificate chains, message persistence, multi-factor authentication, and migration from the
teaching transport layer to TLS for deployment realism.
