"""Package command entrypoint."""

from __future__ import annotations

import argparse
import signal
import sys
import time

from secure_suite.crypto.public_key import generate_rsa_keypair
from secure_suite.keymgmt.keystore import Keystore
from secure_suite.net.server import SecureServer
from secure_suite.ui.cli_client import run_cli
from secure_suite.ui.gui_client import main as gui_main


def _server_command(args: argparse.Namespace) -> int:
    server = SecureServer(host=args.host, port=args.port, data_dir=args.data_dir)
    server.start()
    print(f"Server listening on {args.host}:{server.port}")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
    return 0


def _client_command(args: argparse.Namespace) -> int:
    return run_cli(args.host, args.port)


def _gui_command(args: argparse.Namespace) -> int:
    return gui_main(["--host", args.host, "--port", str(args.port)])


def _genkeys_command(args: argparse.Namespace) -> int:
    private_key, public_key = generate_rsa_keypair()
    keystore = Keystore.open(args.out, args.passphrase)
    keystore.put(
        "generated_keys",
        {
            "private_key": private_key.decode("utf-8"),
            "public_key": public_key.decode("utf-8"),
        },
    )
    keystore.save()
    print(f"Encrypted keypair written to {args.out}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Secure Communication Suite")
    subparsers = parser.add_subparsers(dest="command", required=True)

    server_parser = subparsers.add_parser("server", help="Run the secure messaging server")
    server_parser.add_argument("--host", default="127.0.0.1")
    server_parser.add_argument("--port", type=int, default=9999)
    server_parser.add_argument("--data-dir", default=".")
    server_parser.set_defaults(func=_server_command)

    client_parser = subparsers.add_parser("client", help="Run the CLI client")
    client_parser.add_argument("--host", default="127.0.0.1")
    client_parser.add_argument("--port", type=int, default=9999)
    client_parser.set_defaults(func=_client_command)

    gui_parser = subparsers.add_parser("gui", help="Run the Tkinter GUI client")
    gui_parser.add_argument("--host", default="127.0.0.1")
    gui_parser.add_argument("--port", type=int, default=9999)
    gui_parser.set_defaults(func=_gui_command)

    genkeys_parser = subparsers.add_parser("genkeys", help="Generate an encrypted keystore")
    genkeys_parser.add_argument("--out", default="keystore.bin")
    genkeys_parser.add_argument("--passphrase", default="secure-suite-demo")
    genkeys_parser.set_defaults(func=_genkeys_command)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
