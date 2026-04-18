"""Deterministic fast runner orchestration."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qa_z.artifacts import load_contract_context
from qa_z.config import get_nested
from qa_z.diffing.models import ChangeSet
from qa_z.diffing.parser import parse_unified_diff
from qa_z.reporters.review_packet import find_latest_contract
from qa_z.runners.checks import resolve_fast_checks
from qa_z.runners.models import CheckPlan, CheckResult, CheckSpec, RunSummary
from qa_z.runners.selection import build_fast_selection
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
    diff_path: Path | None = None,
    output_dir: Path | None = None,
    strict_no_tests: bool = False,
    selection_mode: str = "full",
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
    specs = resolve_fast_checks(config)
    change_set = resolve_fast_change_set(
        root=root,
        contract_path=resolved_contract,
        diff_path=diff_path,
    )
    plans, selection = build_fast_selection(
        check_specs=specs,
        change_set=change_set,
        repo_root=root,
        selection_mode=selection_mode,
        full_run_threshold=full_run_threshold(config),
        high_risk_paths=high_risk_paths(config),
    )
    effective_strict_no_tests = strict_no_tests or bool(
        get_nested(config, "fast", "strict_no_tests", default=False)
    )
    contract_title = extract_contract_title(resolved_contract)

    if not specs:
        finished_at = utc_now()
        summary = RunSummary(
            mode="fast",
            contract_path=format_path(resolved_contract, root),
            contract_title=contract_title,
            project_root=str(root),
            status="unsupported",
            started_at=started_at,
            finished_at=finished_at,
            checks=[],
            artifact_dir=format_path(run_dir / "fast", root),
            message="No supported fast checks are configured.",
            schema_version=2,
            selection=selection,
        )
        return FastRun(summary=summary, exit_code=FAST_EXIT_UNSUPPORTED)

    results = [
        run_check_plan(
            plan,
            spec,
            root=root,
            no_tests_policy="fail" if effective_strict_no_tests else spec.no_tests,
            missing_tool_fails=fail_on_missing_tool(config),
        )
        for plan, spec in zip(plans, specs)
    ]
    status, exit_code = summarize_status(results)
    finished_at = utc_now()

    summary = RunSummary(
        mode="fast",
        contract_path=format_path(resolved_contract, root),
        contract_title=contract_title,
        project_root=str(root),
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        checks=results,
        artifact_dir=format_path(run_dir / "fast", root),
        schema_version=2,
        selection=selection,
    )
    return FastRun(summary=summary, exit_code=exit_code)


def run_check_plan(
    plan: CheckPlan,
    spec: CheckSpec,
    *,
    root: Path,
    no_tests_policy: str,
    missing_tool_fails: bool,
) -> CheckResult:
    """Execute or skip one selected check plan."""
    if plan.execution_mode == "skipped":
        return CheckResult(
            id=plan.id,
            tool=plan.tool,
            command=plan.resolved_command,
            kind=plan.kind,
            status="skipped",
            exit_code=None,
            duration_ms=0,
            message=plan.selection_reason,
            execution_mode=plan.execution_mode,
            target_paths=list(plan.target_paths),
            selection_reason=plan.selection_reason,
            high_risk_reasons=list(plan.high_risk_reasons),
        )

    planned_spec = CheckSpec(
        id=spec.id,
        command=list(plan.resolved_command),
        kind=spec.kind,
        enabled=spec.enabled,
        no_tests=spec.no_tests,
        timeout_seconds=spec.timeout_seconds,
    )
    result = normalize_check_result(
        run_check(planned_spec, cwd=root),
        no_tests_policy=no_tests_policy,
        fail_on_missing_tool=missing_tool_fails,
    )
    result.execution_mode = plan.execution_mode
    result.target_paths = list(plan.target_paths)
    result.selection_reason = plan.selection_reason
    result.high_risk_reasons = list(plan.high_risk_reasons)
    return result


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

    if result.kind == "test" and is_no_tests_result(result):
        result.message = "No tests were collected."
        result.status = "failed" if no_tests_policy.lower() == "fail" else "warning"
    return result


def is_no_tests_result(result: CheckResult) -> bool:
    """Return whether a test runner result represents an empty test selection."""
    if result.exit_code == 5:
        return True
    output = f"{result.stdout_tail}\n{result.stderr_tail}".lower()
    return "no test files found" in output or "no tests found" in output


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


def full_run_threshold(config: dict[str, Any]) -> int:
    """Return the smart-selection full-run threshold."""
    value = get_nested(config, "fast", "selection", "full_run_threshold", default=None)
    if value is None:
        value = get_nested(
            config, "checks", "selection", "max_changed_files", default=40
        )
    try:
        threshold = int(value)
    except (TypeError, ValueError):
        return 40
    return threshold if threshold >= 0 else 40


def high_risk_paths(config: dict[str, Any]) -> list[str]:
    """Return configured paths that should force full check execution."""
    paths: list[str] = []
    for source in (
        get_nested(config, "fast", "selection", "high_risk_paths", default=[]),
        get_nested(config, "project", "critical_paths", default=[]),
        get_nested(config, "gates", "escalate_on", default=[]),
    ):
        if isinstance(source, list):
            paths.extend(str(item) for item in source if str(item).strip())
    return paths


def resolve_fast_change_set(
    *,
    root: Path,
    contract_path: Path,
    diff_path: Path | None,
) -> ChangeSet | None:
    """Resolve change metadata for fast selection, preferring CLI diff input."""
    if diff_path is not None:
        try:
            diff_text = diff_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise FileNotFoundError(f"Diff not found: {diff_path}") from exc
        return parse_unified_diff(diff_text, source="cli_diff")

    contract = load_contract_context(contract_path, root)
    if contract.change_set is None:
        return ChangeSet(source="none", files=[])
    return ChangeSet(source="contract", files=contract.change_set.files)


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
    for line in contract_path.read_text(encoding="utf-8").splitlines():
        match = re.match(r"#\s+QA Contract:\s+(?P<title>.+)", line)
        if match:
            return match.group("title").strip()
        metadata_match = re.match(r"title:\s*(?P<title>.+)", line)
        if metadata_match:
            return metadata_match.group("title").strip().strip("'\"")
    return None


def summary_json(summary: RunSummary) -> str:
    """Render a run summary for machine-readable stdout."""
    return json.dumps(summary.to_dict(), indent=2, sort_keys=True) + "\n"
