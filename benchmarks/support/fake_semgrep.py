"""Deterministic Semgrep stand-in used by QA-Z benchmark fixtures."""

from __future__ import annotations

import json
from pathlib import Path


def main() -> int:
    """Print fixture-provided Semgrep JSON and return its configured exit code."""
    payload_path = Path.cwd() / ".qa-z-benchmark" / "semgrep.json"
    if not payload_path.is_file():
        print(json.dumps({"results": []}))
        return 0

    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    results = payload.get("results", []) if isinstance(payload, dict) else []
    errors = payload.get("errors", []) if isinstance(payload, dict) else []
    exit_code = payload.get("exit_code", 1 if results else 0)
    print(json.dumps({"results": results, "errors": errors}))
    try:
        return int(exit_code)
    except (TypeError, ValueError):
        return 1 if results else 0


if __name__ == "__main__":
    raise SystemExit(main())
