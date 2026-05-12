# CSE451 Secure Communication Suite

Project implementation for the CSE451 Secure Communication Suite assignment.

## Contents

- `secure_suite/` application code
- `tests/` stdlib `unittest` suite
- `docs/` SRS, design, test plan, report, and presentation sources
- `scripts/` benchmark and document-rendering helpers

## Quickstart

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Run tests:

```bash
python3 -m unittest discover -s tests -v
```

Run the server:

```bash
python3 -m secure_suite server
```

Run the CLI client:

```bash
python3 -m secure_suite client
```

Run the GUI client:

```bash
python3 -m secure_suite gui
```

Generate an encrypted keystore:

```bash
python3 -m secure_suite genkeys --out keystore.bin
```

## Verification

Run the automated test suite:

```bash
python3 -m unittest discover -s tests -v
```

Run the benchmark:

```bash
python3 scripts/benchmark.py
```

Render final deliverables without pandoc:

```bash
python3 scripts/render_docs.py
```

## Spec-to-Code Map

| Requirement Area | Primary Code Path |
|---|---|
| Block cipher module | `secure_suite/crypto/block_cipher.py` |
| Public key cryptosystem | `secure_suite/crypto/public_key.py` |
| Hashing module | `secure_suite/crypto/hashing.py` |
| Key management | `secure_suite/keymgmt/keystore.py`, `secure_suite/keymgmt/keyexchange.py` |
| Authentication | `secure_suite/auth/user_db.py`, `secure_suite/auth/session.py` |
| Internet services security | `secure_suite/net/protocol.py`, `secure_suite/net/server.py`, `secure_suite/net/client.py` |
| CLI client | `secure_suite/ui/cli_client.py` |
| Tkinter GUI client | `secure_suite/ui/gui_client.py` |
| Package entrypoint | `secure_suite/cli.py`, `secure_suite/__main__.py` |

## Deliverables

- `Report.docx`
- `Report.pdf`
- `Presentation.pptx`
- `CSE451_SecureCommSuite.zip`
