"""Subprocess execution helpers for deterministic runners."""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from qa_z.runners.models import CheckResult, CheckSpec

TAIL_LIMIT = 4000


def tail_text(value: str, limit: int = TAIL_LIMIT) -> str:
    """Keep the final part of subprocess output for compact artifacts."""
    if len(value) <= limit:
        return value
    return value[-limit:]


def run_check(spec: CheckSpec, cwd: Path) -> CheckResult:
    """Run a configured check and capture a normalized result."""
    started = time.perf_counter()
    if not spec.command:
        return CheckResult(
            id=spec.id,
            tool=spec.tool,
            command=spec.command,
            kind=spec.kind,
            status="error",
            exit_code=None,
            duration_ms=0,
            message="Check command is empty.",
            error_type="invalid_command",
        )

    try:
        completed = subprocess.run(
            spec.command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=spec.timeout_seconds,
            check=False,
        )
    except FileNotFoundError as exc:
        return CheckResult(
            id=spec.id,
            tool=spec.tool,
            command=spec.command,
            kind=spec.kind,
            status="error",
            exit_code=None,
            duration_ms=elapsed_ms(started),
            stderr_tail=str(exc),
            message=f"Missing required tool: {spec.command[0]}",
            error_type="missing_tool",
        )
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout if isinstance(exc.stdout, str) else ""
        stderr = exc.stderr if isinstance(exc.stderr, str) else ""
        return CheckResult(
            id=spec.id,
            tool=spec.tool,
            command=spec.command,
            kind=spec.kind,
            status="error",
            exit_code=None,
            duration_ms=elapsed_ms(started),
            stdout_tail=tail_text(stdout),
            stderr_tail=tail_text(stderr),
            message=f"Check timed out after {spec.timeout_seconds} seconds.",
            error_type="timeout",
        )

    status = "passed" if completed.returncode == 0 else "failed"
    return CheckResult(
        id=spec.id,
        tool=spec.tool,
        command=spec.command,
        kind=spec.kind,
        status=status,
        exit_code=completed.returncode,
        duration_ms=elapsed_ms(started),
        stdout_tail=tail_text(completed.stdout),
        stderr_tail=tail_text(completed.stderr),
    )


def elapsed_ms(started: float) -> int:
    """Return elapsed wall time in milliseconds."""
    return int((time.perf_counter() - started) * 1000)
