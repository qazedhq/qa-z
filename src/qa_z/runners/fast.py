"""Deterministic fast runner orchestration."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qa_z.config import get_nested
from qa_z.reporters.review_packet import find_latest_contract
from qa_z.runners.models import CheckResult, RunSummary
from qa_z.runners.python import resolve_python_fast_checks
from qa_z.runners.subprocess import run_check

FAST_EXIT_PASSED = 0
FAST_EXIT_FAILED = 1
FAST_EXIT_USAGE = 2
FAST_EXIT_MISSING_TOOL = 3
FAST_EXIT_UNSUPPORTED = 4


@dataclass
class FastRun:
    """Result of a fast-runner invocation."""

    summary: RunSummary
    exit_code: int


def run_fast(
    *,
    root: Path,
    config: dict[str, Any],
    contract_path: Path | None = None,
    output_dir: Path | None = None,
    strict_no_tests: bool = False,
) -> FastRun:
    """Run configured fast checks and return a normalized summary."""
    started_at = utc_now()
    resolved_contract = (
        contract_path
        if contract_path is not None
        else find_latest_contract(root, config)
    )
    resolved_contract = resolved_contract.resolve()
    run_dir = resolve_run_dir(root, config, output_dir)
    specs = resolve_python_fast_checks(config)
    effective_strict_no_tests = strict_no_tests or bool(
        get_nested(config, "fast", "strict_no_tests", default=False)
    )

    if not specs:
        finished_at = utc_now()
        summary = RunSummary(
            mode="fast",
            contract_path=format_path(resolved_contract, root),
            contract_title=extract_contract_title(resolved_contract),
            project_root=str(root),
            status="unsupported",
            started_at=started_at,
            finished_at=finished_at,
            checks=[],
            artifact_dir=format_path(run_dir / "fast", root),
            message="No supported fast checks are configured.",
        )
        return FastRun(summary=summary, exit_code=FAST_EXIT_UNSUPPORTED)

    results = [
        normalize_check_result(
            run_check(spec, cwd=root),
            no_tests_policy="fail" if effective_strict_no_tests else spec.no_tests,
            fail_on_missing_tool=fail_on_missing_tool(config),
        )
        for spec in specs
    ]
    status, exit_code = summarize_status(results)
    finished_at = utc_now()

    summary = RunSummary(
        mode="fast",
        contract_path=format_path(resolved_contract, root),
        contract_title=extract_contract_title(resolved_contract),
        project_root=str(root),
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        checks=results,
        artifact_dir=format_path(run_dir / "fast", root),
    )
    return FastRun(summary=summary, exit_code=exit_code)


def normalize_check_result(
    result: CheckResult,
    *,
    no_tests_policy: str,
    fail_on_missing_tool: bool,
) -> CheckResult:
    """Apply QA-Z policies to raw subprocess results."""
    if result.error_type == "missing_tool" and not fail_on_missing_tool:
        result.status = "skipped"
        result.message = (
            result.message or "Required tool is missing; check skipped by policy."
        )
        return result

    if result.kind == "test" and result.exit_code == 5:
        result.message = "No tests were collected."
        result.status = "failed" if no_tests_policy.lower() == "fail" else "warning"
    return result


def summarize_status(results: list[CheckResult]) -> tuple[str, int]:
    """Compute the run status and CLI exit code."""
    if any(result.status == "error" for result in results):
        return "error", FAST_EXIT_MISSING_TOOL
    if any(result.status == "failed" for result in results):
        return "failed", FAST_EXIT_FAILED
    return "passed", FAST_EXIT_PASSED


def resolve_run_dir(
    root: Path, config: dict[str, Any], output_dir: Path | None
) -> Path:
    """Resolve the run directory for this invocation."""
    if output_dir is not None:
        return output_dir.expanduser().resolve()

    configured = Path(
        str(get_nested(config, "fast", "output_dir", default=".qa-z/runs"))
    )
    if not configured.is_absolute():
        configured = root / configured
    return configured / utc_now().replace(":", "-")


def fail_on_missing_tool(config: dict[str, Any]) -> bool:
    """Return whether missing subprocess tools should fail the run."""
    return bool(get_nested(config, "fast", "fail_on_missing_tool", default=True))


def utc_now() -> str:
    """Return a compact UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_path(path: Path, root: Path) -> str:
    """Format a path relative to the project root when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def extract_contract_title(contract_path: Path) -> str | None:
    """Extract the first QA contract heading when available."""
    if not contract_path.exists():
        return None
    first_lines = contract_path.read_text(encoding="utf-8").splitlines()[:10]
    for line in first_lines:
        match = re.match(r"#\s+QA Contract:\s+(?P<title>.+)", line)
        if match:
            return match.group("title").strip()
    return None


def summary_json(summary: RunSummary) -> str:
    """Render a run summary for machine-readable stdout."""
    return json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n"
