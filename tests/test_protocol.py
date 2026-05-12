"""Tests for framing and record protection."""

from __future__ import annotations

import socket
import threading
import unittest

from secure_suite.net.protocol import (
    ProtocolError,
    SessionContext,
    build_protected_payload,
    frame_payload,
    parse_protected_payload,
    recv_frame,
)


class ProtocolTests(unittest.TestCase):
    def test_frame_round_trip(self) -> None:
        left, right = socket.socketpair()
        try:
            payload = frame_payload(b"example")
            left.sendall(payload)
            self.assertEqual(recv_frame(right), b"example")
        finally:
            left.close()
            right.close()

    def test_truncated_frame_raises(self) -> None:
        left, right = socket.socketpair()
        try:
            left.sendall((10).to_bytes(4, "big") + b"short")
            left.close()
            with self.assertRaises(EOFError):
                recv_frame(right)
        finally:
            right.close()

    def test_replay_is_rejected(self) -> None:
        sender = SessionContext(b"1" * 32)
        receiver = SessionContext(b"1" * 32)
        protected = build_protected_payload(sender, "MSG", {"text": "hello"})
        parse_protected_payload(receiver, protected)
        with self.assertRaises(ProtocolError):
            parse_protected_payload(receiver, protected)


if __name__ == "__main__":
    unittest.main()
