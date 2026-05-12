"""Interactive terminal client."""

from __future__ import annotations

import argparse
import getpass

from secure_suite.net.client import SecureClient


HELP_TEXT = """Commands:
  register           Register a new user
  login              Login as an existing user
  send               Send a message
  fetch              Fetch queued messages
  logout             Logout from the current session
  help               Show this help
  quit               Exit the client
"""


def run_cli(host: str = "127.0.0.1", port: int = 9999) -> int:
    client = SecureClient(host=host, port=port)
    client.connect()
    print("Connected to secure server.")
    print(HELP_TEXT)
    try:
        while True:
            command = input("secure-suite> ").strip().lower()
            if command == "register":
                username = input("Username: ").strip()
                password = getpass.getpass("Password: ")
                result = client.register(username, password)
                print(result["status"])
            elif command == "login":
                username = input("Username: ").strip()
                password = getpass.getpass("Password: ")
                result = client.login(username, password)
                print(result["status"])
            elif command == "send":
                recipient = input("Recipient: ").strip()
                text = input("Message: ").strip()
                result = client.send_message(recipient, text)
                print(result["status"])
            elif command == "fetch":
                messages = client.fetch_messages()
                if not messages:
                    print("No messages.")
                for message in messages:
                    status = message.get("integrity", "?")
                    print(f'[{status}] {message["from"]}: {message["text"]}')
            elif command == "logout":
                result = client.logout()
                print(result["status"])
                host, port = client.host, client.port
                client.close()
                client = SecureClient(host=host, port=port)
                client.connect()
                print("Reconnected. You can log in as a different user.")
            elif command in {"help", "?"}:
                print(HELP_TEXT)
            elif command in {"quit", "exit"}:
                break
            elif not command:
                continue
            else:
                print("Unknown command. Type 'help'.")
    finally:
        client.close()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Secure Communication Suite CLI client")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9999)
    args = parser.parse_args(argv)
    return run_cli(args.host, args.port)
