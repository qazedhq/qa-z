"""Fast-check selection planning."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path, PurePosixPath

from qa_z.diffing.models import ChangedFile, ChangeSet
from qa_z.runners.models import CheckPlan, CheckSpec, SelectionSummary
from qa_z.runners.selection_typescript import (
    TYPESCRIPT_BUILTIN_IDS,
    build_typescript_check_plan,
)

PYTHON_BUILTIN_IDS = {"py_lint", "py_format", "py_type", "py_test"}


def build_fast_selection(
    *,
    check_specs: list[CheckSpec],
    change_set: ChangeSet | None,
    repo_root: Path,
    selection_mode: str,
    full_run_threshold: int,
    high_risk_paths: list[str],
) -> tuple[list[CheckPlan], SelectionSummary]:
    """Build check execution plans and a selection summary."""
    normalized_mode = "smart" if selection_mode == "smart" else "full"
    input_source = change_set.source if change_set is not None else "none"

    if normalized_mode == "full":
        full_plans = [
            full_check_plan(spec, "full selection requested", [])
            for spec in check_specs
        ]
        return full_plans, summarize_selection(
            mode=normalized_mode,
            input_source=input_source,
            changed_files=change_set.files if change_set is not None else [],
            high_risk_reasons=[],
            plans=full_plans,
        )

    if change_set is None:
        high_risk_reasons = ["diff/changes parse failed"]
        parse_failure_plans = [
            full_check_plan(
                spec,
                "full run required because change information could not be parsed",
                high_risk_reasons,
            )
            for spec in check_specs
        ]
        return parse_failure_plans, summarize_selection(
            mode=normalized_mode,
            input_source=input_source,
            changed_files=[],
            high_risk_reasons=high_risk_reasons,
            plans=parse_failure_plans,
        )

    if change_set.is_empty:
        empty_change_plans = [
            full_check_plan(
                spec,
                "full run required because no changed files were found",
                [],
            )
            for spec in check_specs
        ]
        return empty_change_plans, summarize_selection(
            mode=normalized_mode,
            input_source=input_source,
            changed_files=[],
            high_risk_reasons=[],
            plans=empty_change_plans,
        )

    high_risk_reasons = evaluate_high_risk(
        change_set,
        full_run_threshold=full_run_threshold,
        high_risk_paths=high_risk_paths,
    )
    docs_only = is_docs_only(change_set)
    plans: list[CheckPlan] = []
    for spec in check_specs:
        if high_risk_reasons:
            plans.append(
                full_check_plan(
                    spec,
                    "full run required because high-risk files changed",
                    high_risk_reasons,
                )
            )
        elif docs_only:
            plans.append(skipped_check_plan(spec, "docs-only change"))
        elif spec.id in PYTHON_BUILTIN_IDS:
            plans.append(
                build_python_check_plan(
                    spec,
                    change_set,
                    repo_root,
                    high_risk_reasons,
                )
            )
        elif spec.id in TYPESCRIPT_BUILTIN_IDS:
            plans.append(
                build_typescript_check_plan(
                    spec,
                    change_set,
                    repo_root,
                    high_risk_reasons,
                )
            )
        else:
            plans.append(
                full_check_plan(
                    spec,
                    "custom check has no targeted selector; falling back to full",
                    [],
                )
            )

    return plans, summarize_selection(
        mode=normalized_mode,
        input_source=input_source,
        changed_files=change_set.files,
        high_risk_reasons=high_risk_reasons,
        plans=plans,
    )


def evaluate_high_risk(
    change_set: ChangeSet,
    *,
    full_run_threshold: int,
    high_risk_paths: list[str],
) -> list[str]:
    """Return reasons that force full check execution."""
    reasons: list[str] = []
    if any(changed.status == "deleted" for changed in change_set.files):
        reasons.append("deleted files changed")
    if any(changed.status == "renamed" for changed in change_set.files):
        reasons.append("renamed files changed")
    for pattern in high_risk_paths:
        matched = first_matching_high_risk_path(change_set.files, pattern)
        if matched:
            reasons.append(f"high-risk path changed: {matched}")
    if full_run_threshold >= 0 and len(change_set.files) > full_run_threshold:
        reasons.append(
            f"changed file count {len(change_set.files)} exceeds threshold {full_run_threshold}"
        )
    if any(changed.kind == "config" for changed in change_set.files):
        reasons.append("config files changed")
    if any(changed.kind == "other" for changed in change_set.files):
        reasons.append("files with unknown kind changed")
    return unique_preserve_order(reasons)


def is_docs_only(change_set: ChangeSet) -> bool:
    """Return whether all changed files are documentation files."""
    return bool(change_set.files) and all(
        changed.kind == "docs" for changed in change_set.files
    )


def build_python_check_plan(
    spec: CheckSpec,
    change_set: ChangeSet,
    repo_root: Path,
    high_risk_reasons: list[str],
) -> CheckPlan:
    """Build a smart selection plan for one built-in Python check."""
    python_changed = [
        changed
        for changed in change_set.files
        if changed.language == "python" and changed.kind in {"source", "test"}
    ]
    changed_tests = [changed for changed in python_changed if changed.kind == "test"]
    changed_sources = [
        changed for changed in python_changed if changed.kind == "source"
    ]

    if not python_changed:
        return skipped_check_plan(spec, "no python source/test changes")

    if spec.id == "py_lint":
        targets = [changed.path for changed in python_changed]
        if targets:
            return targeted_check_plan(
                spec,
                ["ruff", "check", *targets],
                targets,
                "python source/test files changed",
                high_risk_reasons,
            )
    if spec.id == "py_format":
        targets = [changed.path for changed in python_changed]
        if targets:
            return targeted_check_plan(
                spec,
                ["ruff", "format", "--check", *targets],
                targets,
                "python source/test files changed",
                high_risk_reasons,
            )
    if spec.id == "py_type":
        if python_changed:
            return full_check_plan(
                spec,
                "type checking remains full for python changes",
                high_risk_reasons,
            )
    if spec.id == "py_test":
        if changed_tests:
            targets = [changed.path for changed in changed_tests]
            return targeted_check_plan(
                spec,
                ["pytest", "-q", *targets],
                targets,
                "changed test files selected directly",
                high_risk_reasons,
            )
        if changed_sources:
            targets, reason = resolve_python_test_targets(changed_sources, repo_root)
            if targets:
                return targeted_check_plan(
                    spec,
                    ["pytest", "-q", *targets],
                    targets,
                    reason or "mapped changed source files to candidate tests",
                    high_risk_reasons,
                )
            return full_check_plan(
                spec,
                "no candidate tests resolved; falling back to full",
                high_risk_reasons,
            )

    return full_check_plan(
        spec,
        "custom check has no targeted selector; falling back to full",
        high_risk_reasons,
    )


def resolve_python_test_targets(
    changed_files: list[ChangedFile],
    repo_root: Path,
) -> tuple[list[str], str | None]:
    """Map changed Python source files to candidate test files."""
    candidates: list[str] = []
    for changed in changed_files:
        for candidate in candidate_test_paths(changed.path):
            if (repo_root / candidate).is_file() and candidate not in candidates:
                candidates.append(candidate)
    if not candidates:
        return [], None
    return candidates, "mapped changed source files to candidate tests"


def candidate_test_paths(path: str) -> list[str]:
    """Return likely pytest files for a Python source path."""
    normalized = path.replace("\\", "/")
    pure = PurePosixPath(normalized)
    stem = pure.stem
    if stem == "__init__":
        stem = pure.parent.name

    module_parts = list(pure.with_suffix("").parts)
    if module_parts and module_parts[0] in {"src", "app", "lib"}:
        module_parts = module_parts[1:]
    module_dir = PurePosixPath(*module_parts[:-1]) if len(module_parts) > 1 else None

    candidates = [
        f"tests/test_{stem}.py",
        f"tests/{stem}_test.py",
    ]
    if module_dir is not None:
        candidates.extend(
            [
                f"tests/{module_dir}/test_{stem}.py",
                f"tests/{module_dir}/{stem}_test.py",
            ]
        )
    return unique_preserve_order(candidates)


def full_check_plan(
    spec: CheckSpec, selection_reason: str, high_risk_reasons: list[str]
) -> CheckPlan:
    """Create a full execution plan."""
    return CheckPlan(
        id=spec.id,
        kind=spec.kind,
        tool=spec.tool,
        enabled=spec.enabled,
        execution_mode="full",
        base_command=list(spec.command),
        resolved_command=list(spec.command),
        target_paths=[],
        selection_reason=selection_reason,
        high_risk_reasons=list(high_risk_reasons),
    )


def targeted_check_plan(
    spec: CheckSpec,
    resolved_command: list[str],
    target_paths: list[str],
    selection_reason: str,
    high_risk_reasons: list[str],
) -> CheckPlan:
    """Create a targeted execution plan."""
    return CheckPlan(
        id=spec.id,
        kind=spec.kind,
        tool=Path(resolved_command[0]).name if resolved_command else spec.tool,
        enabled=spec.enabled,
        execution_mode="targeted",
        base_command=list(spec.command),
        resolved_command=resolved_command,
        target_paths=target_paths,
        selection_reason=selection_reason,
        high_risk_reasons=list(high_risk_reasons),
    )


def skipped_check_plan(spec: CheckSpec, selection_reason: str) -> CheckPlan:
    """Create a skipped execution plan."""
    return CheckPlan(
        id=spec.id,
        kind=spec.kind,
        tool=spec.tool,
        enabled=spec.enabled,
        execution_mode="skipped",
        base_command=list(spec.command),
        resolved_command=list(spec.command),
        target_paths=[],
        selection_reason=selection_reason,
        high_risk_reasons=[],
    )


def summarize_selection(
    *,
    mode: str,
    input_source: str,
    changed_files: list[ChangedFile],
    high_risk_reasons: list[str],
    plans: list[CheckPlan],
) -> SelectionSummary:
    """Build the persisted selection summary from check plans."""
    return SelectionSummary(
        mode=mode,
        input_source=input_source,
        changed_files=changed_files,
        high_risk_reasons=high_risk_reasons,
        selected_checks=[plan.id for plan in plans if plan.execution_mode != "skipped"],
        full_checks=[plan.id for plan in plans if plan.execution_mode == "full"],
        targeted_checks=[
            plan.id for plan in plans if plan.execution_mode == "targeted"
        ],
        skipped_checks=[plan.id for plan in plans if plan.execution_mode == "skipped"],
    )


def first_matching_high_risk_path(
    changed_files: list[ChangedFile], pattern: str
) -> str | None:
    """Return the first path matching one high-risk pattern."""
    normalized_pattern = pattern.replace("\\", "/")
    for changed in changed_files:
        for candidate in [changed.path, changed.old_path]:
            if candidate and matches_path(candidate, normalized_pattern):
                return candidate
    return None


def matches_path(path: str, pattern: str) -> bool:
    """Match exact, glob, and simple directory-prefix high-risk patterns."""
    normalized = path.replace("\\", "/")
    if normalized == pattern:
        return True
    if fnmatch(normalized, pattern):
        return True
    if pattern.endswith("/**") and normalized.startswith(
        pattern[:-3].rstrip("/") + "/"
    ):
        return True
    return False


def unique_preserve_order(items: list[str]) -> list[str]:
    """Return unique strings in first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
