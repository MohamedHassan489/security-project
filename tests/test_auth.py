"""Tests for authentication helpers."""

from __future__ import annotations

import tempfile
import time
import unittest
from pathlib import Path

from secure_suite.auth.user_db import UserDatabase


class AuthTests(unittest.TestCase):
    def test_register_and_verify_happy_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = UserDatabase(Path(tmpdir) / "users.json")
            db.register("alice", "correct horse battery staple", "pub")
            self.assertTrue(db.verify("alice", "correct horse battery staple"))

    def test_wrong_password_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = UserDatabase(Path(tmpdir) / "users.json")
            db.register("alice", "correct horse battery staple", "pub")
            self.assertFalse(db.verify("alice", "wrong password"))

    def test_constant_time_check_sanity(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            db = UserDatabase(Path(tmpdir) / "users.json")
            db.register("alice", "correct horse battery staple", "pub")
            start_ok = time.perf_counter()
            for _ in range(5):
                db.verify("alice", "correct horse battery staple")
            ok_time = time.perf_counter() - start_ok

            start_bad = time.perf_counter()
            for _ in range(5):
                db.verify("alice", "wrong password")
            bad_time = time.perf_counter() - start_bad

            ratio = max(ok_time, bad_time) / max(min(ok_time, bad_time), 1e-9)
            self.assertLess(ratio, 3.0)


if __name__ == "__main__":
    unittest.main()
