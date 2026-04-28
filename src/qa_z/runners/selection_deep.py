"""Deep-check smart selection planning."""

from __future__ import annotations

from qa_z.diffing.models import ChangeSet
from qa_z.runners.models import CheckPlan, CheckSpec, SelectionSummary
from qa_z.runners.selection import evaluate_high_risk, is_docs_only, summarize_selection
from qa_z.runners.selection_common import (
    full_check_plan,
    skipped_check_plan,
    targeted_check_plan,
)
from qa_z.runners.semgrep import SEMGREP_CHECK_ID, semgrep_targeted_command


def build_deep_selection(
    *,
    check_specs: list[CheckSpec],
    change_set: ChangeSet | None,
    selection_mode: str,
    full_run_threshold: int,
    high_risk_paths: list[str],
) -> tuple[list[CheckPlan], SelectionSummary]:
    """Build deep check execution plans and persisted selection metadata."""
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
    language_reasons = evaluate_deep_language_risk(change_set)
    all_high_risk_reasons = [*high_risk_reasons, *language_reasons]
    docs_only = is_docs_only(change_set)

    plans: list[CheckPlan] = []
    for spec in check_specs:
        if all_high_risk_reasons:
            plans.append(
                full_check_plan(
                    spec,
                    "full run required because high-risk files changed",
                    all_high_risk_reasons,
                )
            )
        elif docs_only:
            plans.append(skipped_check_plan(spec, "docs-only change"))
        elif spec.id == SEMGREP_CHECK_ID:
            plans.append(build_semgrep_plan(spec, change_set))
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
        high_risk_reasons=all_high_risk_reasons,
        plans=plans,
    )


def evaluate_deep_language_risk(change_set: ChangeSet) -> list[str]:
    """Return deep-specific reasons that force full Semgrep execution."""
    source_languages = {
        changed.language
        for changed in change_set.files
        if changed.kind in {"source", "test"}
        and changed.language in {"python", "typescript"}
    }
    if len(source_languages) > 1:
        return ["mixed python and typescript source/test changes"]
    return []


def build_semgrep_plan(spec: CheckSpec, change_set: ChangeSet) -> CheckPlan:
    """Build a smart selection plan for Semgrep."""
    targets = [
        changed.path
        for changed in change_set.files
        if changed.kind in {"source", "test"}
        and changed.language in {"python", "typescript"}
    ]
    if not targets:
        return full_check_plan(
            spec,
            "no semgrep-targetable source files found; falling back to full",
            [],
        )
    return targeted_check_plan(
        spec,
        semgrep_targeted_command(spec.command, targets),
        targets,
        "source files changed",
        [],
    )
