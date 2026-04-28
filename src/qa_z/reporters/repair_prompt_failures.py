"""Failure ordering helpers for repair prompts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_z.artifacts import extract_candidate_files, extract_contract_candidate_files

if TYPE_CHECKING:
    from qa_z.artifacts import ContractContext
    from qa_z.runners.models import CheckResult, RunSummary
    from qa_z.reporters.repair_prompt import FailureContext


FIX_KIND_PRIORITY = {
    "format": 0,
    "lint": 1,
    "typecheck": 2,
    "test": 3,
}


def sorted_failures(
    summary: "RunSummary", contract: "ContractContext"
) -> list["FailureContext"]:
    """Return failed or errored checks in deterministic repair order."""
    contract_candidates = extract_contract_candidate_files(contract)
    failure_checks = [
        check for check in summary.checks if check.status in {"failed", "error"}
    ]
    ordered_checks = sorted(
        enumerate(failure_checks),
        key=lambda item: (fix_priority(item[1]), item[0], item[1].id),
    )
    return [
        failure_context(check, contract_candidates) for _index, check in ordered_checks
    ]


def failure_context(
    check: "CheckResult", contract_candidates: list[str]
) -> "FailureContext":
    """Build repair context for one check result."""
    from qa_z.reporters.repair_prompt import FailureContext

    evidence = "\n".join(
        part for part in (check.stdout_tail, check.stderr_tail) if part
    )
    output_candidates = extract_candidate_files(evidence)
    candidate_files = ordered_candidate_files(contract_candidates, output_candidates)
    return FailureContext(
        id=check.id,
        kind=check.kind,
        tool=check.tool,
        command=check.command,
        exit_code=check.exit_code,
        duration_ms=check.duration_ms,
        summary=check.message or default_failure_summary(check),
        stdout_tail=check.stdout_tail,
        stderr_tail=check.stderr_tail,
        candidate_files=candidate_files,
    )


def ordered_candidate_files(
    contract_candidates: list[str], output_candidates: list[str]
) -> list[str]:
    """Merge candidate files with contract hints first, capped at ten files."""
    merged: list[str] = []
    for path in [*contract_candidates, *output_candidates]:
        if path not in merged:
            merged.append(path)
    return merged[:10]


def default_failure_summary(check: "CheckResult") -> str:
    """Render a compact deterministic failure summary."""
    if check.exit_code is None:
        return f"{check.tool} did not complete successfully."
    return f"{check.tool} exited with code {check.exit_code}."


def fix_priority(check: "CheckResult | FailureContext") -> int:
    """Return deterministic repair priority for a check."""
    kind_priority = FIX_KIND_PRIORITY.get(check.kind)
    if kind_priority is not None:
        return kind_priority
    lowered = check.id.lower()
    for kind, priority in FIX_KIND_PRIORITY.items():
        if kind in lowered:
            return priority
    return len(FIX_KIND_PRIORITY)
