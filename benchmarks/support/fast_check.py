"""Deterministic fast-check helper used by QA-Z benchmark fixtures."""

from __future__ import annotations

import sys


def main() -> int:
    """Emit optional evidence and return the requested status."""
    status = sys.argv[1] if len(sys.argv) > 1 else "pass"
    message = sys.argv[2] if len(sys.argv) > 2 else ""
    if message:
        print(message)
    if status == "pass":
        return 0
    if status == "no-tests":
        return 5
    try:
        return int(status)
    except ValueError:
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
