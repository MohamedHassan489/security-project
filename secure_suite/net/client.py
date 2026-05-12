"""Shared client core for CLI and GUI clients."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from typing import Callable

from secure_suite.auth.session import verify_token
from secure_suite.crypto.hashing import sha256_bytes
from secure_suite.crypto.public_key import generate_rsa_keypair
from secure_suite.keymgmt.keyexchange import unwrap_session_key
from secure_suite.net.protocol import (
    SessionContext,
    b64decode_text,
    recv_json_frame,
    recv_protected_message,
    send_json_frame,
    send_protected_message,
)


@dataclass
class AuthState:
    """Authenticated session state."""

    username: str
    token: dict[str, str]


class SecureClient:
    """Client core shared by both UIs."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9999,
        timeout: float = 5.0,
        wiretap: Callable[[bytes], None] | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.wiretap = wiretap
        self.socket: socket.socket | None = None
        self.session: SessionContext | None = None
        self.server_public_key: str | None = None
        self.private_key: str | None = None
        self.public_key: str | None = None
        self.auth: AuthState | None = None

    def connect(self) -> None:
        self.socket = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.socket.settimeout(self.timeout)
        private_key, public_key = generate_rsa_keypair()
        self.private_key = private_key.decode("utf-8")
        self.public_key = public_key.decode("utf-8")
        send_json_frame(self.socket, {"type": "HELLO", "public_key": self.public_key}, self.wiretap)
        hello = recv_json_frame(self.socket)
        self.server_public_key = hello["public_key"]
        kex = recv_json_frame(self.socket)
        session_key = unwrap_session_key(self.private_key, b64decode_text(kex["wrapped_session_key"]))
        self.session = SessionContext(session_key)

    def close(self) -> None:
        if self.socket is not None:
            try:
                self.socket.close()
            except OSError:
                pass
        self.socket = None

    def register(self, username: str, password: str) -> dict:
        response_type, payload = self._request(
            "REGISTER",
            {"username": username, "password": password, "rsa_pub_pem": self.public_key},
        )
        if response_type != "REGISTER_OK":
            raise ValueError(payload["error"])
        return payload

    def login(self, username: str, password: str) -> dict:
        response_type, payload = self._request("LOGIN", {"username": username, "password": password})
        if response_type != "LOGIN_OK":
            raise ValueError(payload["error"])
        assert self.server_public_key is not None
        token = payload["token"]
        token_payload = verify_token(self.server_public_key, token)
        self.auth = AuthState(username=token_payload["user"], token=token)
        return payload

    def send_message(self, recipient: str, text: str) -> dict:
        auth = self._require_auth()
        response_type, payload = self._request(
            "MSG",
            {"recipient": recipient, "text": text, "token": auth.token},
        )
        if response_type != "MSG_OK":
            raise ValueError(payload["error"])
        return payload

    def fetch_messages(self) -> list[dict[str, str]]:
        auth = self._require_auth()
        response_type, payload = self._request("FETCH", {"token": auth.token})
        if response_type != "FETCH_OK":
            raise ValueError(payload["error"])
        messages = payload["messages"]
        for msg in messages:
            expected = msg.get("sha256", "")
            actual = sha256_bytes(msg["text"].encode("utf-8"))
            msg["integrity"] = "verified" if actual == expected else "TAMPERED"
        return messages

    def logout(self) -> dict:
        response_type, payload = self._request("LOGOUT", {})
        if response_type != "LOGOUT_OK":
            raise ValueError(payload["error"])
        self.auth = None
        return payload

    def _request(self, message_type: str, payload: dict) -> tuple[str, dict]:
        if self.socket is None or self.session is None:
            raise RuntimeError("Client is not connected")
        send_protected_message(self.socket, self.session, message_type, payload, self.wiretap)
        response_type, envelope, _ = recv_protected_message(self.socket, self.session)
        payload = envelope.get("payload", envelope)
        return response_type, payload

    def _require_auth(self) -> AuthState:
        if self.auth is None:
            raise RuntimeError("Client is not authenticated")
        return self.auth
