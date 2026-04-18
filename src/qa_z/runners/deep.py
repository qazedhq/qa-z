"""Deep runner orchestration skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    fast_runs_dir,
    load_run_summary,
    resolve_run_source,
)
from qa_z.config import get_nested
from qa_z.diffing.models import ChangeSet
from qa_z.diffing.parser import parse_unified_diff
from qa_z.runners.fast import format_path, utc_now
from qa_z.runners.models import (
    CheckPlan,
    CheckResult,
    CheckSpec,
    RunSummary,
    SemgrepCheckPolicy,
)
from qa_z.runners.python import coerce_timeout
from qa_z.runners.selection_deep import build_deep_selection
from qa_z.runners.semgrep import (
    SEMGREP_CHECK_ID,
    default_semgrep_spec_for_name,
    normalize_semgrep_result,
    semgrep_command_with_config,
    semgrep_policy_from_config,
)
from qa_z.runners.subprocess import run_check

DEEP_EXIT_PASSED = 0
DEEP_EXIT_FAILED = 1
DEEP_EXIT_USAGE = 2
DEEP_EXIT_ERROR = 3


@dataclass(frozen=True)
class DeepRunResolution:
    """Resolved locations for a deep-runner invocation."""

    run_dir: Path
    deep_dir: Path
    attached_to_fast_run: bool
    fast_summary_path: Path | None = None


@dataclass(frozen=True)
class DeepRun:
    """Result of a deep-runner invocation."""

    summary: RunSummary
    exit_code: int
    resolution: DeepRunResolution


def run_deep(
    *,
    root: Path,
    config: dict[str, Any],
    output_dir: Path | None = None,
    from_run: str | None = None,
    diff_path: Path | None = None,
    selection_mode: str = "full",
) -> DeepRun:
    """Run configured deep checks and return a normalized summary."""
    started_at = utc_now()
    resolution = resolve_deep_run_dir(
        root=root,
        config=config,
        output_dir=output_dir,
        from_run=from_run,
    )
    fast_summary = (
        load_run_summary(resolution.fast_summary_path)
        if resolution.fast_summary_path is not None
        else None
    )
    specs = resolve_deep_checks(config)
    change_set = resolve_deep_change_set(
        diff_path=diff_path,
        fast_summary=fast_summary,
    )
    plans, selection = build_deep_selection(
        check_specs=specs,
        change_set=change_set,
        selection_mode=selection_mode,
        full_run_threshold=full_run_threshold(config),
        high_risk_paths=high_risk_paths(config),
    )
    results = [
        run_deep_check_plan(
            plan,
            spec,
            root=root,
            missing_tool_fails=fail_on_missing_tool(config),
        )
        for plan, spec in zip(plans, specs)
    ]
    status, exit_code = summarize_deep_status(results)
    finished_at = utc_now()
    summary = RunSummary(
        mode="deep",
        contract_path=fast_summary.contract_path if fast_summary else None,
        contract_title=fast_summary.contract_title if fast_summary else None,
        project_root=str(root),
        status=status,
        started_at=started_at,
        finished_at=finished_at,
        checks=results,
        artifact_dir=format_path(resolution.deep_dir, root),
        message=deep_message(resolution.attached_to_fast_run, bool(specs)),
        schema_version=2,
        selection=selection,
        policy=deep_policy_summary(specs),
    )
    return DeepRun(
        summary=summary,
        exit_code=exit_code,
        resolution=resolution,
    )


def resolve_deep_run_dir(
    *,
    root: Path,
    config: dict[str, Any],
    output_dir: Path | None,
    from_run: str | None,
) -> DeepRunResolution:
    """Resolve the run and deep artifact directories for a deep invocation."""
    if output_dir is not None:
        run_dir = output_dir.expanduser().resolve()
        return DeepRunResolution(
            run_dir=run_dir,
            deep_dir=run_dir / "deep",
            attached_to_fast_run=False,
        )

    if from_run:
        source = resolve_run_source(root, config, from_run)
        ensure_fast_summary_is_valid(source.summary_path)
        return DeepRunResolution(
            run_dir=source.run_dir,
            deep_dir=source.run_dir / "deep",
            attached_to_fast_run=True,
            fast_summary_path=source.summary_path,
        )

    try:
        source = resolve_run_source(root, config, "latest")
        ensure_fast_summary_is_valid(source.summary_path)
    except (ArtifactLoadError, ArtifactSourceNotFound):
        run_dir = fast_runs_dir(root, config) / utc_now().replace(":", "-")
        return DeepRunResolution(
            run_dir=run_dir,
            deep_dir=run_dir / "deep",
            attached_to_fast_run=False,
        )

    return DeepRunResolution(
        run_dir=source.run_dir,
        deep_dir=source.run_dir / "deep",
        attached_to_fast_run=True,
        fast_summary_path=source.summary_path,
    )


def ensure_fast_summary_is_valid(summary_path: Path) -> None:
    """Raise when a candidate fast summary cannot be consumed by deep."""
    summary = load_run_summary(summary_path)
    if summary.mode != "fast":
        raise ArtifactLoadError(f"Expected a fast summary at {summary_path}.")


def resolve_deep_checks(config: dict[str, Any]) -> list[CheckSpec]:
    """Resolve configured deep checks into executable subprocess specs."""
    specs: list[CheckSpec] = []
    global_exclude_paths = deep_exclude_paths(config)
    for item in configured_deep_checks(config):
        spec = resolve_deep_check_item(item, global_exclude_paths=global_exclude_paths)
        if spec is not None and spec.enabled:
            specs.append(spec)
    return specs


def configured_deep_checks(config: dict[str, Any]) -> list[Any]:
    """Return explicit deep check configuration."""
    deep_config = config.get("deep")
    if isinstance(deep_config, dict) and "checks" in deep_config:
        checks = deep_config.get("checks") or []
        return checks if isinstance(checks, list) else []
    return []


def resolve_deep_check_item(
    item: Any, *, global_exclude_paths: list[str] | None = None
) -> CheckSpec | None:
    """Resolve one deep config item to a supported check spec."""
    if isinstance(item, str):
        spec = default_semgrep_spec_for_name(item)
        if spec is not None and spec.id == SEMGREP_CHECK_ID:
            spec.semgrep_policy = SemgrepCheckPolicy(
                exclude_paths=list(global_exclude_paths or [])
            )
        return spec
    if not isinstance(item, dict):
        return None

    check_id = str(item.get("id", "")).strip()
    if not check_id:
        return None

    command = item.get("run")
    if command is None:
        default = default_semgrep_spec_for_name(check_id)
        command = default.command if default else None
    if not isinstance(command, list) or not all(
        isinstance(part, str) for part in command
    ):
        return None

    semgrep_policy = None
    resolved_command = list(command)
    if check_id == SEMGREP_CHECK_ID:
        semgrep_policy = semgrep_policy_from_config(
            item, global_exclude_paths=global_exclude_paths
        )
        resolved_command = semgrep_command_with_config(
            resolved_command, semgrep_policy.config
        )

    return CheckSpec(
        id=check_id,
        command=resolved_command,
        kind=str(item.get("kind", default_deep_kind(check_id))),
        enabled=bool(item.get("enabled", True)),
        timeout_seconds=coerce_timeout(item.get("timeout_seconds")),
        semgrep_policy=semgrep_policy,
    )


def default_deep_kind(check_id: str) -> str:
    """Infer a supported deep check kind."""
    default = default_semgrep_spec_for_name(check_id)
    if default:
        return default.kind
    return "custom"


def run_deep_check(
    spec: CheckSpec, *, root: Path, missing_tool_fails: bool
) -> CheckResult:
    """Execute and normalize one deep check."""
    result = run_check(spec, cwd=root)
    if result.error_type == "missing_tool" and not missing_tool_fails:
        result.status = "skipped"
        result.message = (
            result.message or "Required tool is missing; check skipped by policy."
        )
        return result

    if spec.id == SEMGREP_CHECK_ID:
        return normalize_semgrep_result(result, spec.semgrep_policy)
    return result


def run_deep_check_plan(
    plan: CheckPlan,
    spec: CheckSpec,
    *,
    root: Path,
    missing_tool_fails: bool,
) -> CheckResult:
    """Execute or skip one selected deep check plan."""
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
            policy=(
                spec.semgrep_policy.to_dict() if spec.semgrep_policy is not None else {}
            ),
        )

    planned_spec = CheckSpec(
        id=spec.id,
        command=list(plan.resolved_command),
        kind=spec.kind,
        enabled=spec.enabled,
        timeout_seconds=spec.timeout_seconds,
        semgrep_policy=spec.semgrep_policy,
    )
    result = run_deep_check(
        planned_spec,
        root=root,
        missing_tool_fails=missing_tool_fails,
    )
    result.execution_mode = plan.execution_mode
    result.target_paths = list(plan.target_paths)
    result.selection_reason = plan.selection_reason
    result.high_risk_reasons = list(plan.high_risk_reasons)
    return result


def summarize_deep_status(results: list[CheckResult]) -> tuple[str, int]:
    """Compute the deep run status and CLI exit code."""
    if any(result.status == "error" for result in results):
        return "error", DEEP_EXIT_ERROR
    if any(result.status == "failed" for result in results):
        return "failed", DEEP_EXIT_FAILED
    return "passed", DEEP_EXIT_PASSED


def fail_on_missing_tool(config: dict[str, Any]) -> bool:
    """Return whether missing deep tools should fail the run."""
    return bool(get_nested(config, "deep", "fail_on_missing_tool", default=True))


def full_run_threshold(config: dict[str, Any]) -> int:
    """Return the smart-selection full-run threshold for deep checks."""
    value = get_nested(config, "deep", "selection", "full_run_threshold", default=None)
    if value is None:
        value = get_nested(
            config, "checks", "selection", "max_changed_files", default=15
        )
    try:
        threshold = int(value)
    except (TypeError, ValueError):
        return 15
    return threshold if threshold >= 0 else 15


def high_risk_paths(config: dict[str, Any]) -> list[str]:
    """Return configured paths that should force full deep execution."""
    paths: list[str] = []
    for source in (
        get_nested(config, "deep", "selection", "high_risk_paths", default=[]),
        get_nested(config, "project", "critical_paths", default=[]),
        get_nested(config, "gates", "escalate_on", default=[]),
    ):
        if isinstance(source, list):
            paths.extend(str(item) for item in source if str(item).strip())
    return paths


def deep_exclude_paths(config: dict[str, Any]) -> list[str]:
    """Return configured deep selection exclude path patterns."""
    value = get_nested(config, "deep", "selection", "exclude_paths", default=[])
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]


def deep_policy_summary(specs: list[CheckSpec]) -> dict[str, Any]:
    """Return top-level policy metadata for deep summary artifacts."""
    for spec in specs:
        if spec.id == SEMGREP_CHECK_ID and spec.semgrep_policy is not None:
            return spec.semgrep_policy.to_dict()
    return {}


def resolve_deep_change_set(
    *,
    diff_path: Path | None,
    fast_summary: RunSummary | None,
) -> ChangeSet | None:
    """Resolve change metadata for deep selection."""
    if diff_path is not None:
        try:
            diff_text = diff_path.read_text(encoding="utf-8")
        except OSError as exc:
            raise FileNotFoundError(f"Diff not found: {diff_path}") from exc
        return parse_unified_diff(diff_text, source="cli_diff")

    if fast_summary is not None and fast_summary.selection is not None:
        source = fast_summary.selection.input_source
        if source not in {"cli_diff", "contract", "none"}:
            source = "none"
        return ChangeSet(
            source=source,  # type: ignore[arg-type]
            files=list(fast_summary.selection.changed_files),
        )

    return ChangeSet(source="none", files=[])


def deep_message(attached_to_fast_run: bool, checks_configured: bool) -> str:
    """Return a short skeleton-status message."""
    if checks_configured:
        if attached_to_fast_run:
            return "Deep checks completed and attached to an existing fast run."
        return "Deep checks completed without an attachable fast run."
    if attached_to_fast_run:
        return "Deep summary skeleton attached to an existing fast run."
    return "Deep summary skeleton created without an attachable fast run."
