"""Post-repair verification comparison and artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from qa_z.artifacts import (
    RunSource,
    format_path,
    load_run_summary,
    resolve_run_source,
)
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.runners.models import CheckResult, RunSummary

VERIFY_COMPARE_KIND = "qa_z.verify_compare"
VERIFY_SUMMARY_KIND = "qa_z.verify_summary"
VERIFY_SCHEMA_VERSION = 1

VerificationVerdict = Literal[
    "improved",
    "unchanged",
    "mixed",
    "regressed",
    "verification_failed",
]
VerificationCategory = Literal[
    "resolved",
    "still_failing",
    "regressed",
    "newly_introduced",
    "skipped_or_not_comparable",
]

BLOCKING_CHECK_STATUSES = {"failed", "error"}
NON_BLOCKING_CHECK_STATUSES = {"passed", "warning"}
SKIPPED_CHECK_STATUSES = {"skipped", "unsupported"}


@dataclass(frozen=True)
class VerificationRun:
    """Loaded evidence for one baseline or candidate run."""

    run_id: str
    run_dir: str
    fast_summary: RunSummary
    deep_summary: RunSummary | None = None


@dataclass(frozen=True)
class FastCheckDelta:
    """Comparison result for one fast check id."""

    id: str
    classification: VerificationCategory
    baseline_status: str | None
    candidate_status: str | None
    baseline_exit_code: int | None
    candidate_exit_code: int | None
    kind: str | None = None
    message: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Render this fast-check delta as JSON-safe data."""
        data: dict[str, Any] = {
            "id": self.id,
            "classification": self.classification,
            "baseline_status": self.baseline_status,
            "candidate_status": self.candidate_status,
            "baseline_exit_code": self.baseline_exit_code,
            "candidate_exit_code": self.candidate_exit_code,
        }
        if self.kind:
            data["kind"] = self.kind
        if self.message:
            data["message"] = self.message
        return data


@dataclass(frozen=True)
class VerificationFinding:
    """Normalized deep finding identity used for deterministic comparison."""

    source: str
    rule_id: str
    severity: str
    path: str
    line: int | None
    message: str
    blocking: bool
    grouped: bool = False
    occurrences: int | None = None

    @property
    def id(self) -> str:
        """Return the stable human and JSON id for this finding."""
        location = self.path or "unknown"
        if self.line is not None:
            location = f"{location}:{self.line}"
        return f"{self.source}:{self.rule_id}:{location}"

    @property
    def strict_key(self) -> tuple[str, str, str, int | None, str, bool]:
        """Return the strict identity including the normalized message."""
        return (
            self.source,
            self.rule_id,
            self.path,
            self.line,
            normalize_message(self.message),
            self.grouped,
        )

    @property
    def relaxed_key(self) -> tuple[str, str, str, int | None, bool]:
        """Return the conservative relaxed identity excluding message text."""
        line = None if self.grouped else self.line
        return (self.source, self.rule_id, self.path, line, self.grouped)

    def to_dict(self) -> dict[str, Any]:
        """Render this finding as JSON-safe data."""
        data: dict[str, Any] = {
            "id": self.id,
            "source": self.source,
            "rule_id": self.rule_id,
            "severity": self.severity,
            "path": self.path,
            "line": self.line,
            "message": self.message,
            "blocking": self.blocking,
            "grouped": self.grouped,
        }
        if self.occurrences is not None:
            data["occurrences"] = self.occurrences
        return data


@dataclass(frozen=True)
class VerificationFindingDelta:
    """Comparison result for one deep finding identity."""

    id: str
    classification: VerificationCategory
    source: str
    rule_id: str
    path: str
    line: int | None
    baseline_severity: str | None = None
    candidate_severity: str | None = None
    baseline_blocking: bool | None = None
    candidate_blocking: bool | None = None
    message: str = ""
    match: Literal["strict", "relaxed", "none"] = "none"

    def to_dict(self) -> dict[str, Any]:
        """Render this finding delta as JSON-safe data."""
        return {
            "id": self.id,
            "classification": self.classification,
            "source": self.source,
            "rule_id": self.rule_id,
            "path": self.path,
            "line": self.line,
            "baseline_severity": self.baseline_severity,
            "candidate_severity": self.candidate_severity,
            "baseline_blocking": self.baseline_blocking,
            "candidate_blocking": self.candidate_blocking,
            "message": self.message,
            "match": self.match,
        }


@dataclass(frozen=True)
class VerificationComparison:
    """Full comparison result for a baseline and candidate run."""

    baseline: VerificationRun
    candidate: VerificationRun
    verdict: VerificationVerdict
    fast_checks: dict[VerificationCategory, list[FastCheckDelta]]
    deep_findings: dict[VerificationCategory, list[VerificationFindingDelta]]
    summary: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        """Render the comparison as deterministic JSON-safe data."""
        return {
            "kind": VERIFY_COMPARE_KIND,
            "schema_version": VERIFY_SCHEMA_VERSION,
            "baseline_run_id": self.baseline.run_id,
            "candidate_run_id": self.candidate.run_id,
            "baseline": {
                "run_dir": self.baseline.run_dir,
                "fast_status": self.baseline.fast_summary.status,
                "deep_status": (
                    self.baseline.deep_summary.status
                    if self.baseline.deep_summary is not None
                    else None
                ),
            },
            "candidate": {
                "run_dir": self.candidate.run_dir,
                "fast_status": self.candidate.fast_summary.status,
                "deep_status": (
                    self.candidate.deep_summary.status
                    if self.candidate.deep_summary is not None
                    else None
                ),
            },
            "verdict": self.verdict,
            "fast_checks": {
                category: [delta.to_dict() for delta in deltas]
                for category, deltas in self.fast_checks.items()
            },
            "deep_findings": {
                category: [delta.to_dict() for delta in deltas]
                for category, deltas in self.deep_findings.items()
            },
            "summary": dict(self.summary),
        }


@dataclass(frozen=True)
class VerificationArtifactPaths:
    """Paths written for a verification comparison."""

    summary_path: Path
    compare_path: Path
    report_path: Path


def load_verification_run(
    *, root: Path, config: dict[str, Any], from_run: str | None
) -> tuple[VerificationRun, RunSource]:
    """Load fast and optional sibling deep evidence for a verification run."""
    source = resolve_run_source(root, config, from_run)
    fast_summary = load_run_summary(source.summary_path)
    if fast_summary.mode != "fast":
        raise ValueError(f"Expected a fast summary at {source.summary_path}.")
    deep_summary = load_sibling_deep_summary(source)
    return (
        VerificationRun(
            run_id=source.run_dir.name,
            run_dir=format_path(source.run_dir, root),
            fast_summary=fast_summary,
            deep_summary=deep_summary,
        ),
        source,
    )


def compare_verification_runs(
    baseline: VerificationRun, candidate: VerificationRun
) -> VerificationComparison:
    """Compare baseline and candidate QA-Z run evidence."""
    fast_checks = compare_fast_checks(
        baseline.fast_summary.checks, candidate.fast_summary.checks
    )
    deep_findings = compare_deep_findings(baseline.deep_summary, candidate.deep_summary)
    summary = build_comparison_summary(
        baseline=baseline,
        candidate=candidate,
        fast_checks=fast_checks,
        deep_findings=deep_findings,
    )
    verdict = derive_verdict(summary)
    return VerificationComparison(
        baseline=baseline,
        candidate=candidate,
        verdict=verdict,
        fast_checks=fast_checks,
        deep_findings=deep_findings,
        summary=summary,
    )


def compare_fast_checks(
    baseline_checks: list[CheckResult], candidate_checks: list[CheckResult]
) -> dict[VerificationCategory, list[FastCheckDelta]]:
    """Classify fast check status changes by check id."""
    categories = empty_categories(FastCheckDelta)
    baseline_by_id = {check.id: check for check in baseline_checks}
    candidate_by_id = {check.id: check for check in candidate_checks}
    check_ids = sorted(set(baseline_by_id) | set(candidate_by_id))

    for check_id in check_ids:
        baseline = baseline_by_id.get(check_id)
        candidate = candidate_by_id.get(check_id)
        classification = classify_fast_check(baseline, candidate)
        if classification is None:
            continue
        reference = candidate or baseline
        categories[classification].append(
            FastCheckDelta(
                id=check_id,
                classification=classification,
                baseline_status=baseline.status if baseline else None,
                candidate_status=candidate.status if candidate else None,
                baseline_exit_code=baseline.exit_code if baseline else None,
                candidate_exit_code=candidate.exit_code if candidate else None,
                kind=reference.kind if reference else None,
                message=fast_delta_message(classification, baseline, candidate),
            )
        )

    return categories


def classify_fast_check(
    baseline: CheckResult | None, candidate: CheckResult | None
) -> VerificationCategory | None:
    """Return the verification category for one fast check transition."""
    baseline_blocking = is_blocking_check(baseline)
    candidate_blocking = is_blocking_check(candidate)
    baseline_status = baseline.status if baseline else None
    candidate_status = candidate.status if candidate else None

    if baseline_blocking and candidate_status in NON_BLOCKING_CHECK_STATUSES:
        return "resolved"
    if baseline_blocking and candidate_blocking:
        return "still_failing"
    if baseline_status in NON_BLOCKING_CHECK_STATUSES and candidate_blocking:
        return "regressed"
    if baseline is None and candidate_blocking:
        return "newly_introduced"
    if baseline_blocking and (
        candidate is None or candidate_status in SKIPPED_CHECK_STATUSES
    ):
        return "skipped_or_not_comparable"
    if (
        baseline_status in SKIPPED_CHECK_STATUSES
        or candidate_status in SKIPPED_CHECK_STATUSES
    ):
        return "skipped_or_not_comparable"
    if baseline is None or candidate is None:
        return "skipped_or_not_comparable"
    return None


def compare_deep_findings(
    baseline_summary: RunSummary | None, candidate_summary: RunSummary | None
) -> dict[VerificationCategory, list[VerificationFindingDelta]]:
    """Classify deep finding changes using strict then relaxed matching."""
    categories = empty_categories(VerificationFindingDelta)
    if baseline_summary is None and candidate_summary is None:
        return categories
    if baseline_summary is None or candidate_summary is None:
        categories["skipped_or_not_comparable"].append(
            VerificationFindingDelta(
                id="deep:summary",
                classification="skipped_or_not_comparable",
                source="deep",
                rule_id="summary",
                path="",
                line=None,
                message=(
                    "Deep comparison requires both baseline and candidate "
                    "deep/summary.json artifacts, or neither."
                ),
            )
        )
        return categories

    baseline_findings = extract_deep_findings(baseline_summary)
    candidate_findings = extract_deep_findings(candidate_summary)
    matched_candidate_indexes: set[int] = set()

    for baseline in baseline_findings:
        candidate_index, match_kind = find_matching_candidate(
            baseline,
            candidate_findings,
            matched_candidate_indexes,
        )
        if candidate_index is None:
            if baseline.blocking:
                categories["resolved"].append(
                    finding_delta(
                        "resolved",
                        baseline=baseline,
                        candidate=None,
                        match="none",
                    )
                )
            continue

        matched_candidate_indexes.add(candidate_index)
        candidate = candidate_findings[candidate_index]
        classification = classify_matched_finding(baseline, candidate)
        if classification is None:
            continue
        categories[classification].append(
            finding_delta(
                classification,
                baseline=baseline,
                candidate=candidate,
                match=match_kind,
            )
        )

    for index, candidate in enumerate(candidate_findings):
        if index in matched_candidate_indexes or not candidate.blocking:
            continue
        categories["newly_introduced"].append(
            finding_delta(
                "newly_introduced",
                baseline=None,
                candidate=candidate,
                match="none",
            )
        )

    return categories


def find_matching_candidate(
    baseline: VerificationFinding,
    candidates: list[VerificationFinding],
    matched_candidate_indexes: set[int],
) -> tuple[int | None, Literal["strict", "relaxed", "none"]]:
    """Find a deterministic strict or relaxed candidate match."""
    strict_matches = [
        index
        for index, candidate in enumerate(candidates)
        if index not in matched_candidate_indexes
        and candidate.strict_key == baseline.strict_key
    ]
    if len(strict_matches) == 1:
        return strict_matches[0], "strict"

    relaxed_matches = [
        index
        for index, candidate in enumerate(candidates)
        if index not in matched_candidate_indexes
        and candidate.relaxed_key == baseline.relaxed_key
    ]
    if len(relaxed_matches) == 1:
        return relaxed_matches[0], "relaxed"
    return None, "none"


def classify_matched_finding(
    baseline: VerificationFinding, candidate: VerificationFinding
) -> VerificationCategory | None:
    """Return the category for a matched deep finding."""
    if baseline.blocking and candidate.blocking:
        return "still_failing"
    if baseline.blocking and not candidate.blocking:
        return "resolved"
    if not baseline.blocking and candidate.blocking:
        return "regressed"
    return None


def finding_delta(
    classification: VerificationCategory,
    *,
    baseline: VerificationFinding | None,
    candidate: VerificationFinding | None,
    match: Literal["strict", "relaxed", "none"],
) -> VerificationFindingDelta:
    """Build a serialized finding delta from baseline/candidate evidence."""
    reference = candidate or baseline
    if reference is None:
        raise ValueError("A finding delta requires baseline or candidate evidence.")
    return VerificationFindingDelta(
        id=reference.id,
        classification=classification,
        source=reference.source,
        rule_id=reference.rule_id,
        path=reference.path,
        line=reference.line,
        baseline_severity=baseline.severity if baseline else None,
        candidate_severity=candidate.severity if candidate else None,
        baseline_blocking=baseline.blocking if baseline else None,
        candidate_blocking=candidate.blocking if candidate else None,
        message=reference.message,
        match=match,
    )


def extract_deep_findings(summary: RunSummary) -> list[VerificationFinding]:
    """Extract normalized active or grouped findings from a deep summary."""
    findings: list[VerificationFinding] = []
    for check in summary.checks:
        blocking = blocking_severities(summary, check)
        if check.findings:
            findings.extend(
                normalize_active_finding(raw, check=check, blocking=blocking)
                for raw in check.findings
                if isinstance(raw, dict)
            )
            continue
        findings.extend(
            normalize_grouped_finding(raw, check=check, blocking=blocking)
            for raw in check.grouped_findings
            if isinstance(raw, dict)
        )
    return findings


def normalize_active_finding(
    raw: dict[str, Any], *, check: CheckResult, blocking: set[str]
) -> VerificationFinding:
    """Normalize one active finding from a deep check."""
    severity = first_nonempty(raw.get("severity"), "UNKNOWN").upper()
    return VerificationFinding(
        source=check.id,
        rule_id=first_nonempty(raw.get("rule_id"), check.id, "unknown"),
        severity=severity,
        path=normalize_path(first_nonempty(raw.get("path"), "")),
        line=coerce_positive_int(raw.get("line")),
        message=first_nonempty(raw.get("message"), ""),
        blocking=severity in blocking,
    )


def normalize_grouped_finding(
    raw: dict[str, Any], *, check: CheckResult, blocking: set[str]
) -> VerificationFinding:
    """Normalize one grouped finding from a deep check."""
    severity = first_nonempty(raw.get("severity"), "UNKNOWN").upper()
    return VerificationFinding(
        source=check.id,
        rule_id=first_nonempty(raw.get("rule_id"), check.id, "unknown"),
        severity=severity,
        path=normalize_path(first_nonempty(raw.get("path"), "")),
        line=coerce_positive_int(raw.get("representative_line")),
        message=first_nonempty(raw.get("message"), ""),
        blocking=severity in blocking,
        grouped=True,
        occurrences=coerce_positive_int(raw.get("count")) or 1,
    )


def blocking_severities(summary: RunSummary, check: CheckResult) -> set[str]:
    """Return configured blocking severities for a deep check."""
    policy = check.policy or summary.policy
    if not isinstance(policy, dict):
        return {"ERROR"}
    raw = policy.get("fail_on_severity")
    if not isinstance(raw, list):
        return {"ERROR"}
    severities = {str(item).strip().upper() for item in raw if str(item).strip()}
    return severities or {"ERROR"}


def build_comparison_summary(
    *,
    baseline: VerificationRun,
    candidate: VerificationRun,
    fast_checks: dict[VerificationCategory, list[FastCheckDelta]],
    deep_findings: dict[VerificationCategory, list[VerificationFindingDelta]],
) -> dict[str, int]:
    """Build compact numeric summary data for verdict derivation."""
    fast_before = count_blocking_checks(baseline.fast_summary)
    fast_after = count_blocking_checks(candidate.fast_summary)
    deep_before = count_blocking_deep_findings(baseline.deep_summary)
    deep_after = count_blocking_deep_findings(candidate.deep_summary)
    regression_count = len(fast_checks["regressed"]) + len(deep_findings["regressed"])
    new_issue_count = (
        regression_count
        + len(fast_checks["newly_introduced"])
        + len(deep_findings["newly_introduced"])
    )
    return {
        "blocking_before": fast_before + deep_before,
        "blocking_after": fast_after + deep_after,
        "fast_blocking_before": fast_before,
        "fast_blocking_after": fast_after,
        "deep_blocking_before": deep_before,
        "deep_blocking_after": deep_after,
        "resolved_count": len(fast_checks["resolved"]) + len(deep_findings["resolved"]),
        "still_failing_count": len(fast_checks["still_failing"])
        + len(deep_findings["still_failing"]),
        "new_issue_count": new_issue_count,
        "regression_count": regression_count,
        "not_comparable_count": len(fast_checks["skipped_or_not_comparable"])
        + len(deep_findings["skipped_or_not_comparable"]),
        "verification_error_count": sum(
            1
            for delta in deep_findings["skipped_or_not_comparable"]
            if delta.id == "deep:summary"
        ),
        "deep_findings_before": count_deep_findings(baseline.deep_summary),
        "deep_findings_after": count_deep_findings(candidate.deep_summary),
    }


def derive_verdict(summary: dict[str, int]) -> VerificationVerdict:
    """Derive the final repair verification verdict."""
    if summary.get("verification_error_count", 0) > 0:
        return "verification_failed"
    if summary["new_issue_count"] > 0 and summary["resolved_count"] > 0:
        return "mixed"
    if summary["new_issue_count"] > 0:
        return "regressed"
    if summary["resolved_count"] > 0:
        return "improved"
    return "unchanged"


def write_verification_artifacts(
    comparison: VerificationComparison, output_dir: Path
) -> VerificationArtifactPaths:
    """Write summary, compare, and Markdown report artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "summary.json"
    compare_path = output_dir / "compare.json"
    report_path = output_dir / "report.md"

    summary_path.write_text(
        json.dumps(verification_summary_dict(comparison), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    compare_path.write_text(
        json.dumps(comparison.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report_path.write_text(render_verification_report(comparison), encoding="utf-8")
    return VerificationArtifactPaths(
        summary_path=summary_path,
        compare_path=compare_path,
        report_path=report_path,
    )


def verification_summary_dict(comparison: VerificationComparison) -> dict[str, Any]:
    """Return compact summary JSON for a verification comparison."""
    summary = comparison.summary
    return {
        "kind": VERIFY_SUMMARY_KIND,
        "schema_version": VERIFY_SCHEMA_VERSION,
        "repair_improved": comparison.verdict == "improved",
        "verdict": comparison.verdict,
        "blocking_before": summary["blocking_before"],
        "blocking_after": summary["blocking_after"],
        "resolved_count": summary["resolved_count"],
        "remaining_issue_count": summary["still_failing_count"],
        "new_issue_count": summary["new_issue_count"],
        "regression_count": summary["regression_count"],
        "not_comparable_count": summary["not_comparable_count"],
    }


def render_verification_report(comparison: VerificationComparison) -> str:
    """Render a human-readable verification report."""
    lines = [
        "# QA-Z Repair Verification",
        "",
        f"- Final verdict: `{comparison.verdict}`",
        f"- Baseline run: `{comparison.baseline.run_dir}`",
        f"- Candidate run: `{comparison.candidate.run_dir}`",
        f"- Blocking before: {comparison.summary['blocking_before']}",
        f"- Blocking after: {comparison.summary['blocking_after']}",
        f"- Resolved: {comparison.summary['resolved_count']}",
        f"- New or regressed issues: {comparison.summary['new_issue_count']}",
        "",
        "## Fast Checks",
        "",
    ]
    lines.extend(render_fast_category("Resolved", comparison.fast_checks["resolved"]))
    lines.extend(
        render_fast_category("Still failing", comparison.fast_checks["still_failing"])
    )
    lines.extend(render_fast_category("Regressed", comparison.fast_checks["regressed"]))
    lines.extend(
        render_fast_category(
            "Newly introduced", comparison.fast_checks["newly_introduced"]
        )
    )
    lines.extend(
        render_fast_category(
            "Skipped or not comparable",
            comparison.fast_checks["skipped_or_not_comparable"],
        )
    )
    lines.extend(["## Deep Findings", ""])
    lines.extend(
        render_finding_category("Resolved", comparison.deep_findings["resolved"])
    )
    lines.extend(
        render_finding_category(
            "Still failing", comparison.deep_findings["still_failing"]
        )
    )
    lines.extend(
        render_finding_category("Regressed", comparison.deep_findings["regressed"])
    )
    lines.extend(
        render_finding_category(
            "Newly introduced", comparison.deep_findings["newly_introduced"]
        )
    )
    lines.extend(
        render_finding_category(
            "Skipped or not comparable",
            comparison.deep_findings["skipped_or_not_comparable"],
        )
    )
    lines.extend(
        [
            "## Reproduction",
            "",
            "Run the same fast and deep commands that produced the baseline and "
            "candidate summaries, then rerun `qa-z verify` with the same run ids.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def render_fast_category(title: str, deltas: list[FastCheckDelta]) -> list[str]:
    """Render one fast-check category."""
    lines = [f"### {title}", ""]
    if not deltas:
        return [*lines, "- none", ""]
    for delta in deltas:
        lines.append(
            f"- `{delta.id}`: {delta.baseline_status or 'missing'} -> "
            f"{delta.candidate_status or 'missing'}"
        )
    lines.append("")
    return lines


def render_finding_category(
    title: str, deltas: list[VerificationFindingDelta]
) -> list[str]:
    """Render one deep-finding category."""
    lines = [f"### {title}", ""]
    if not deltas:
        return [*lines, "- none", ""]
    for delta in deltas:
        location = f"{delta.path}:{delta.line}" if delta.line else delta.path
        lines.append(
            f"- `{delta.rule_id}` in `{location or 'unknown'}` "
            f"({delta.baseline_severity or 'missing'} -> "
            f"{delta.candidate_severity or 'missing'}, match: {delta.match})"
        )
    lines.append("")
    return lines


def verify_exit_code(verdict: VerificationVerdict) -> int:
    """Return the CLI exit code for a verification verdict."""
    if verdict == "improved":
        return 0
    if verdict == "verification_failed":
        return 2
    return 1


def comparison_json(comparison: VerificationComparison) -> str:
    """Render comparison JSON for stdout."""
    return json.dumps(comparison.to_dict(), indent=2, sort_keys=True) + "\n"


def count_blocking_checks(summary: RunSummary) -> int:
    """Count failed or errored fast checks."""
    return sum(1 for check in summary.checks if is_blocking_check(check))


def count_blocking_deep_findings(summary: RunSummary | None) -> int:
    """Count blocking deep findings from comparable deep evidence."""
    if summary is None:
        return 0
    return sum(1 for finding in extract_deep_findings(summary) if finding.blocking)


def count_deep_findings(summary: RunSummary | None) -> int:
    """Count deep findings for aggregate visibility."""
    if summary is None:
        return 0
    extracted = extract_deep_findings(summary)
    if extracted:
        return len(extracted)
    return sum(check.findings_count or 0 for check in summary.checks)


def is_blocking_check(check: CheckResult | None) -> bool:
    """Return whether a check status blocks verification success."""
    return bool(check is not None and check.status in BLOCKING_CHECK_STATUSES)


def fast_delta_message(
    classification: VerificationCategory,
    baseline: CheckResult | None,
    candidate: CheckResult | None,
) -> str:
    """Return a compact explanation for a fast-check delta."""
    if classification == "resolved":
        return "Previously blocking check now passes or warns."
    if classification == "still_failing":
        return "Check remains blocking after repair."
    if classification == "regressed":
        return "Previously non-blocking check is now blocking."
    if classification == "newly_introduced":
        return "Candidate run has a new blocking check."
    if baseline is None or candidate is None:
        return "Check exists in only one run and cannot be compared directly."
    return "Check was skipped in at least one run and cannot verify repair."


def normalize_path(path: str) -> str:
    """Normalize paths to stable slash-separated repository paths."""
    return path.replace("\\", "/").strip()


def normalize_message(message: str) -> str:
    """Normalize message text for strict identity without fuzzy matching."""
    return " ".join(message.split()).strip().lower()


def first_nonempty(*values: object) -> str:
    """Return the first non-empty value as text."""
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return ""


def coerce_positive_int(value: object) -> int | None:
    """Return a positive integer, otherwise None."""
    try:
        number = int(str(value))
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def empty_categories(
    _item_type: type[FastCheckDelta] | type[VerificationFindingDelta],
) -> dict[VerificationCategory, list[Any]]:
    """Return all verification categories with stable ordering."""
    return {
        "resolved": [],
        "still_failing": [],
        "regressed": [],
        "newly_introduced": [],
        "skipped_or_not_comparable": [],
    }
