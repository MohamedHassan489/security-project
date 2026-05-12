"""Wire framing and protected record helpers."""

from __future__ import annotations

import base64
import json
import socket
from dataclasses import dataclass
from typing import Any, Callable

from secure_suite.crypto.block_cipher import GCM_TAG_SIZE, aes_gcm_decrypt, aes_gcm_encrypt


VERSION = 1
COUNTER_SIZE = 8
NONCE_SIZE = 12
HEADER_SIZE = 1 + 1 + COUNTER_SIZE
MIN_RECORD_SIZE = HEADER_SIZE + NONCE_SIZE + GCM_TAG_SIZE

TYPE_MAP = {
    "HELLO": 1,
    "KEX": 2,
    "REGISTER": 3,
    "REGISTER_OK": 4,
    "LOGIN": 5,
    "LOGIN_OK": 6,
    "MSG": 7,
    "MSG_OK": 8,
    "FETCH": 9,
    "FETCH_OK": 10,
    "LOGOUT": 11,
    "LOGOUT_OK": 12,
    "ERR": 13,
}
TYPE_MAP_REVERSE = {value: key for key, value in TYPE_MAP.items()}


class ProtocolError(Exception):
    """Raised when the wire protocol is invalid."""


@dataclass
class SessionContext:
    """Track per-session counters."""

    key: bytes
    send_counter: int = 0
    recv_counter: int = -1

    def next_counter(self) -> int:
        counter = self.send_counter
        self.send_counter += 1
        return counter

    def accept_counter(self, counter: int) -> None:
        if counter <= self.recv_counter:
            raise ProtocolError("Replay detected")
        self.recv_counter = counter


def encode_json(payload: dict[str, Any]) -> bytes:
    return json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")


def decode_json(data: bytes) -> dict[str, Any]:
    return json.loads(data.decode("utf-8"))


def _capture(frame: bytes, wiretap: Callable[[bytes], None] | None) -> None:
    if wiretap is not None:
        wiretap(frame)


def frame_payload(payload: bytes) -> bytes:
    return len(payload).to_bytes(4, "big") + payload


def send_frame(
    sock: socket.socket, payload: bytes, wiretap: Callable[[bytes], None] | None = None
) -> None:
    framed = frame_payload(payload)
    sock.sendall(framed)
    _capture(framed, wiretap)


def recv_exact(sock: socket.socket, size: int) -> bytes:
    chunks = []
    remaining = size
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise EOFError("Connection closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def recv_frame(sock: socket.socket) -> bytes:
    header = recv_exact(sock, 4)
    size = int.from_bytes(header, "big")
    if size < 0:
        raise ProtocolError("Negative frame size")
    return recv_exact(sock, size)


def send_json_frame(
    sock: socket.socket, payload: dict[str, Any], wiretap: Callable[[bytes], None] | None = None
) -> None:
    send_frame(sock, encode_json(payload), wiretap)


def recv_json_frame(sock: socket.socket) -> dict[str, Any]:
    return decode_json(recv_frame(sock))


def _header(message_type: str, counter: int) -> bytes:
    return (
        VERSION.to_bytes(1, "big")
        + TYPE_MAP[message_type].to_bytes(1, "big")
        + counter.to_bytes(COUNTER_SIZE, "big")
    )


def build_protected_payload(context: SessionContext, message_type: str, payload: dict[str, Any]) -> bytes:
    counter = context.next_counter()
    header = _header(message_type, counter)
    nonce, ciphertext, tag = aes_gcm_encrypt(context.key, encode_json(payload), header)
    return header + nonce + ciphertext + tag


def parse_protected_payload(
    context: SessionContext, payload: bytes
) -> tuple[str, dict[str, Any], int]:
    if len(payload) < MIN_RECORD_SIZE:
        raise ProtocolError("Protected payload too short")
    version = payload[0]
    type_id = payload[1]
    counter = int.from_bytes(payload[2 : 2 + COUNTER_SIZE], "big")
    nonce_start = HEADER_SIZE
    nonce_end = nonce_start + NONCE_SIZE
    nonce = payload[nonce_start:nonce_end]
    ciphertext = payload[nonce_end:-GCM_TAG_SIZE]
    tag = payload[-GCM_TAG_SIZE:]
    if version != VERSION:
        raise ProtocolError("Unsupported protocol version")
    message_type = TYPE_MAP_REVERSE.get(type_id)
    if message_type is None:
        raise ProtocolError("Unknown message type")
    header = payload[:HEADER_SIZE]
    try:
        plaintext = aes_gcm_decrypt(context.key, nonce, ciphertext, tag, header)
    except ValueError as exc:
        raise ProtocolError("Record authentication failed") from exc
    context.accept_counter(counter)
    return message_type, decode_json(plaintext), counter


def send_protected_message(
    sock: socket.socket,
    context: SessionContext,
    message_type: str,
    payload: dict[str, Any],
    wiretap: Callable[[bytes], None] | None = None,
) -> None:
    send_frame(sock, build_protected_payload(context, message_type, payload), wiretap)


def recv_protected_message(sock: socket.socket, context: SessionContext) -> tuple[str, dict[str, Any], int]:
    return parse_protected_payload(context, recv_frame(sock))


def b64encode_bytes(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def b64decode_text(data: str) -> bytes:
    return base64.b64decode(data.encode("ascii"))
