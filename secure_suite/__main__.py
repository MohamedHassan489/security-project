"""Run the Secure Communication Suite package."""

from __future__ import annotations

import sys

from secure_suite.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
