"""End-to-end tests for the secure messaging flow."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from secure_suite.net.client import SecureClient
from secure_suite.net.server import SecureServer


class TamperingSocket:
    """Wrap a socket and flip one protected byte on the next send."""

    def __init__(self, inner):
        self.inner = inner
        self._tamper_next = True

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def sendall(self, data: bytes) -> None:
        if self._tamper_next and len(data) > 20:
            mutated = bytearray(data)
            mutated[20] ^= 0x01
            self._tamper_next = False
            self.inner.sendall(bytes(mutated))
            return
        self.inner.sendall(data)


class IntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.wire_bytes: list[bytes] = []
        self.server = SecureServer(port=0, data_dir=self.tmpdir.name, wiretap=self.wire_bytes.append)
        self.server.start()
        time.sleep(0.1)

    def tearDown(self) -> None:
        self.server.stop()
        self.tmpdir.cleanup()

    def _client(self) -> SecureClient:
        client = SecureClient(port=self.server.port, wiretap=self.wire_bytes.append)
        client.connect()
        return client

    def test_end_to_end_message_delivery_without_plaintext_on_wire(self) -> None:
        alice = self._client()
        bob = self._client()
        try:
            alice.register("alice", "alice-password")
            bob.register("bob", "bob-password")
            alice.login("alice", "alice-password")
            bob.login("bob", "bob-password")

            alice.send_message("bob", "hello")
            messages = bob.fetch_messages()

            self.assertEqual(messages, [{"from": "alice", "text": "hello"}])
            combined = b"".join(self.wire_bytes)
            self.assertNotIn(b"hello", combined)
        finally:
            alice.close()
            bob.close()

    def test_tampering_causes_disconnect(self) -> None:
        alice = self._client()
        try:
            alice.register("alice", "alice-password")
            alice.login("alice", "alice-password")
            assert alice.socket is not None
            alice.socket = TamperingSocket(alice.socket)
            with self.assertRaises(Exception):
                alice.send_message("bob", "tampered")
        finally:
            alice.close()


if __name__ == "__main__":
    unittest.main()
