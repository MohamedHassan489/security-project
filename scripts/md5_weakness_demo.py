"""Standalone demonstration that MD5 is weak and excluded from production paths."""

from __future__ import annotations

import hashlib


def main() -> int:
    sample_a = b"This project discusses MD5 weaknesses."
    sample_b = b"This project discusses MD5 weaknessf."
    print("Sample A MD5:", hashlib.md5(sample_a).hexdigest())
    print("Sample B MD5:", hashlib.md5(sample_b).hexdigest())
    print("Sample A SHA-256:", hashlib.sha256(sample_a).hexdigest())
    print("Sample B SHA-256:", hashlib.sha256(sample_b).hexdigest())
    print("Conclusion: MD5 is retained only for discussion/demo, not for production use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
