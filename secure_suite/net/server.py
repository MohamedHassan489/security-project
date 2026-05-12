"""Threaded secure messaging server."""

from __future__ import annotations

import logging
import socket
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from Crypto.Random import get_random_bytes

from secure_suite.auth.session import issue_token, verify_token
from secure_suite.auth.user_db import UserDatabase
from secure_suite.crypto.block_cipher import QueueEncryptionBridge
from secure_suite.crypto.hashing import sha256_bytes
from secure_suite.crypto.public_key import generate_rsa_keypair
from secure_suite.keymgmt.keystore import Keystore
from secure_suite.keymgmt.keyexchange import wrap_session_key
from secure_suite.net.protocol import (
    SessionContext,
    b64encode_bytes,
    recv_json_frame,
    recv_protected_message,
    send_json_frame,
    send_protected_message,
)


logging.basicConfig(level=logging.ERROR, format="%(levelname)s %(name)s: %(message)s")
LOGGER = logging.getLogger(__name__)
DEFAULT_SERVER_KEYSTORE = "keystore.bin"
DEFAULT_SERVER_KEYSTORE_PASSPHRASE = "secure-suite-server"


@dataclass
class ClientSession:
    """Connection-local state."""

    socket: socket.socket
    address: tuple[str, int]
    session: SessionContext
    bridge: QueueEncryptionBridge
    client_public_key: str


class SecureServer:
    """Secure threaded messaging server."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9999,
        data_dir: str | Path = ".",
        wiretap: Callable[[bytes], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.wiretap = wiretap
        self.user_db = UserDatabase(self.data_dir / "users.json")
        self.mailboxes: dict[str, list[dict[str, str]]] = {}
        self.mailbox_lock = threading.Lock()
        self.server_socket: socket.socket | None = None
        self.accept_thread: threading.Thread | None = None
        self.running = threading.Event()
        self.client_threads: list[threading.Thread] = []
        self.server_private_key, self.server_public_key = self._load_or_create_server_keys()

    def _load_or_create_server_keys(self) -> tuple[str, str]:
        keystore = Keystore.open(self.data_dir / DEFAULT_SERVER_KEYSTORE, DEFAULT_SERVER_KEYSTORE_PASSPHRASE)
        private_key = keystore.get("server_private_key")
        public_key = keystore.get("server_public_key")
        if private_key and public_key:
            return private_key, public_key
        private_pem, public_pem = generate_rsa_keypair()
        private_key = private_pem.decode("utf-8")
        public_key = public_pem.decode("utf-8")
        keystore.put("server_private_key", private_key)
        keystore.put("server_public_key", public_key)
        keystore.save()
        return private_key, public_key

    def start(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.port = self.server_socket.getsockname()[1]
        self.running.set()
        self.accept_thread = threading.Thread(target=self._accept_loop, daemon=True)
        self.accept_thread.start()

    def stop(self) -> None:
        self.running.clear()
        if self.server_socket is not None:
            try:
                self.server_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.server_socket.close()
        if self.accept_thread is not None:
            self.accept_thread.join(timeout=1)
        for thread in self.client_threads:
            thread.join(timeout=1)

    def _accept_loop(self) -> None:
        assert self.server_socket is not None
        while self.running.is_set():
            try:
                client_sock, address = self.server_socket.accept()
            except OSError:
                break
            thread = threading.Thread(
                target=self._handle_client,
                args=(client_sock, address),
                daemon=True,
            )
            self.client_threads.append(thread)
            thread.start()

    def _handle_client(self, client_sock: socket.socket, address: tuple[str, int]) -> None:
        bridge = QueueEncryptionBridge()
        try:
            hello = recv_json_frame(client_sock)
            client_public_key = hello["public_key"]
            send_json_frame(
                client_sock,
                {"type": "HELLO", "public_key": self.server_public_key},
                self.wiretap,
            )
            session_key = get_random_bytes(32)
            wrapped = wrap_session_key(client_public_key, session_key)
            send_json_frame(
                client_sock,
                {"type": "KEX", "wrapped_session_key": b64encode_bytes(wrapped)},
                self.wiretap,
            )
            client = ClientSession(
                socket=client_sock,
                address=address,
                session=SessionContext(session_key),
                bridge=bridge,
                client_public_key=client_public_key,
            )
            while self.running.is_set():
                message_type, payload, _ = recv_protected_message(client_sock, client.session)
                if message_type == "REGISTER":
                    self._handle_register(client, payload)
                elif message_type == "LOGIN":
                    self._handle_login(client, payload)
                elif message_type == "MSG":
                    self._handle_send_message(client, payload)
                elif message_type == "FETCH":
                    self._handle_fetch_messages(client, payload)
                elif message_type == "LOGOUT":
                    self._send_response(client, "LOGOUT_OK", {"status": "logged_out"})
                    break
                else:
                    self._send_response(client, "ERR", {"error": f"Unsupported type: {message_type}"})
        except (EOFError, OSError):
            LOGGER.debug("Client %s disconnected", address)
        except Exception as exc:
            LOGGER.debug("Client %s error: %s", address, exc)
            try:
                self._send_response_fallback(client_sock, bridge, {"error": str(exc)})
            except Exception:
                pass
        finally:
            bridge.stop()
            try:
                client_sock.close()
            except OSError:
                pass

    def _send_response_fallback(
        self, client_sock: socket.socket, bridge: QueueEncryptionBridge, payload: dict[str, str]
    ) -> None:
        compat_ciphertext, compat_tag = bridge.encrypt(str(payload).encode("utf-8"))
        send_json_frame(
            client_sock,
            {
                "type": "ERR",
                "compat_ciphertext": b64encode_bytes(compat_ciphertext),
                "compat_tag": b64encode_bytes(compat_tag),
            },
            self.wiretap,
        )

    def _send_response(self, client: ClientSession, message_type: str, payload: dict) -> None:
        compat_ciphertext, compat_tag = client.bridge.encrypt(str(payload).encode("utf-8"))
        envelope = {
            "payload": payload,
            "compat_ciphertext": b64encode_bytes(compat_ciphertext),
            "compat_tag": b64encode_bytes(compat_tag),
        }
        send_protected_message(client.socket, client.session, message_type, envelope, self.wiretap)

    def _handle_register(self, client: ClientSession, payload: dict[str, str]) -> None:
        try:
            username = payload["username"]
            password = payload["password"]
            rsa_pub = payload.get("rsa_pub_pem", client.client_public_key)
            self.user_db.register(username, password, rsa_pub)
            with self.mailbox_lock:
                self.mailboxes.setdefault(username, [])
            self._send_response(client, "REGISTER_OK", {"status": "registered"})
        except Exception as exc:
            LOGGER.error("Register error: %s", exc)
            self._send_response(client, "ERR", {"error": str(exc)})

    def _handle_login(self, client: ClientSession, payload: dict[str, str]) -> None:
        try:
            username = payload["username"]
            password = payload["password"]
            if not self.user_db.verify(username, password):
                self._send_response(client, "ERR", {"error": "Authentication failed"})
                return
            token = issue_token(self.server_private_key, username)
            self._send_response(client, "LOGIN_OK", {"status": "ok", "token": token})
        except Exception as exc:
            LOGGER.error("Login error: %s", exc)
            self._send_response(client, "ERR", {"error": str(exc)})

    def _handle_send_message(self, client: ClientSession, payload: dict) -> None:
        try:
            token_payload = verify_token(self.server_public_key, payload["token"])
            sender = token_payload["user"]
            recipient = payload["recipient"]
            text = payload["text"]
            with self.mailbox_lock:
                self.mailboxes.setdefault(recipient, []).append({
                "from": sender,
                "text": text,
                "sha256": sha256_bytes(text.encode("utf-8")),
            })
            self._send_response(client, "MSG_OK", {"status": "queued"})
        except Exception as exc:
            LOGGER.error("Send message error: %s", exc)
            self._send_response(client, "ERR", {"error": str(exc)})

    def _handle_fetch_messages(self, client: ClientSession, payload: dict) -> None:
        try:
            token_payload = verify_token(self.server_public_key, payload["token"])
            username = token_payload["user"]
            with self.mailbox_lock:
                messages = list(self.mailboxes.get(username, []))
                self.mailboxes[username] = []
            self._send_response(client, "FETCH_OK", {"messages": messages})
        except Exception as exc:
            LOGGER.error("Fetch error: %s", exc)
            self._send_response(client, "ERR", {"error": str(exc)})
