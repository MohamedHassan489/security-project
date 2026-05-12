# CSE451 Secure Communication Suite

End-to-end encrypted messaging system built for the CSE451 assignment.
Implements AES-256-GCM, RSA-2048, PBKDF2 authentication, signed session tokens,
and an encrypted keystore.

## Requirements

- Python 3.9 or newer
- `pycryptodome` (install below)
- `tkinter` — required only for the GUI; bundled with Python on Windows/macOS.
  On Linux: `sudo apt install python3-tk`

## Quickstart

```bash
pip install -r requirements.txt
```

Start the server (creates `keystore.bin` and `users.json` on first run):

```bash
python -m secure_suite server
```

In a second terminal, open the GUI client:

```bash
python -m secure_suite gui
```

Or the terminal (CLI) client:

```bash
python -m secure_suite client
```

## Running the Tests

```bash
python -m unittest discover -s tests -v
```

## Benchmarks

```bash
python scripts/benchmark.py
```

## Spec-to-Code Map

| Requirement Area | Primary Code Path |
|---|---|
| Block cipher module | `secure_suite/crypto/block_cipher.py` |
| Public key cryptosystem | `secure_suite/crypto/public_key.py` |
| Hashing / integrity | `secure_suite/crypto/hashing.py` |
| Key management | `secure_suite/keymgmt/keystore.py`, `secure_suite/keymgmt/keyexchange.py` |
| Authentication | `secure_suite/auth/user_db.py`, `secure_suite/auth/session.py` |
| Secure network layer | `secure_suite/net/protocol.py`, `secure_suite/net/server.py`, `secure_suite/net/client.py` |
| CLI client | `secure_suite/ui/cli_client.py` |
| Tkinter GUI client | `secure_suite/ui/gui_client.py` |
| Package entrypoint | `secure_suite/cli.py`, `secure_suite/__main__.py` |
