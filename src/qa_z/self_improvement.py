"""Self-inspection and improvement backlog artifacts for QA-Z."""

from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.executor_dry_run_logic import build_dry_run_summary

SELF_INSPECTION_KIND = "qa_z.self_inspection"
BACKLOG_KIND = "qa_z.improvement_backlog"
SELECTED_TASKS_KIND = "qa_z.selected_tasks"
LOOP_HISTORY_KIND = "qa_z.loop_history_entry"
SELF_IMPROVEMENT_SCHEMA_VERSION = 1

OPEN_STATUSES = {"open", "selected", "in_progress"}
INCOMPLETE_SESSION_STATES = {
    "created",
    "handoff_ready",
    "waiting_for_external_repair",
    "candidate_generated",
    "verification_complete",
    "failed",
}
VERIFICATION_PROBLEM_VERDICTS = {"mixed", "regressed", "verification_failed"}
EXPECTED_COMMAND_DOC_TERMS = ("self-inspect", "select-next", "backlog")
REPORT_EVIDENCE_FILES = {
    "current_state": Path("docs/reports/current-state-analysis.md"),
    "roadmap": Path("docs/reports/next-improvement-roadmap.md"),
    "worktree_triage": Path("docs/reports/worktree-triage.md"),
    "worktree_commit_plan": Path("docs/reports/worktree-commit-plan.md"),
}
EMPTY_LOOP_CHAIN_LENGTH = 3
RECENT_SELECTION_WINDOW = 2
DIRTY_WORKTREE_MODIFIED_THRESHOLD = 10
DIRTY_WORKTREE_TOTAL_THRESHOLD = 30
FALLBACK_REPEAT_WINDOW = 3
INTRA_SELECTION_FAMILY_PENALTY = 2
BENCHMARK_RESULT_ARTIFACTS = (
    Path("benchmarks/results/summary.json"),
    Path("benchmarks/results/report.md"),
)
GENERATED_ARTIFACT_POLICY_DOC = Path("docs/generated-vs-frozen-evidence-policy.md")
GENERATED_ARTIFACT_POLICY_RULES = (
    ".qa-z/",
    "benchmarks/results/work/",
    "benchmarks/results/summary.json",
    "benchmarks/results/report.md",
)
GENERATED_ARTIFACT_POLICY_TERMS = (
    ".qa-z",
    "benchmarks/results/work",
    "benchmarks/results/summary.json",
    "benchmarks/results/report.md",
    "local by default",
    "intentional frozen evidence",
    "benchmarks/fixtures",
)
FALLBACK_FAMILY_BY_CATEGORY = {
    "autonomy_selection_gap": "loop_health",
    "backlog_reseeding_gap": "loop_health",
    "coverage_gap": "benchmark_expansion",
    "docs_drift": "docs_sync",
    "schema_drift": "docs_sync",
    "workflow_gap": "workflow_remediation",
    "integration_gap": "workflow_remediation",
    "provenance_gap": "workflow_remediation",
    "partial_completion_gap": "workflow_remediation",
    "no_op_safeguard_gap": "workflow_remediation",
    "worktree_risk": "cleanup",
    "commit_isolation_gap": "cleanup",
    "artifact_hygiene_gap": "cleanup",
    "runtime_artifact_cleanup_gap": "cleanup",
    "deferred_cleanup_gap": "cleanup",
    "evidence_freshness_gap": "cleanup",
}


@dataclass(frozen=True)
class BacklogCandidate:
    """Evidence-backed improvement candidate before backlog merge."""

    id: str
    title: str
    category: str
    evidence: list[dict[str, Any]]
    impact: int
    likelihood: int
    confidence: int
    repair_cost: int
    recommendation: str
    signals: list[str]
    recurrence_count: int = 1

    def to_dict(self) -> dict[str, Any]:
        """Render the candidate as JSON-safe data."""
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "evidence": list(self.evidence),
            "impact": self.impact,
            "likelihood": self.likelihood,
            "confidence": self.confidence,
            "repair_cost": self.repair_cost,
            "priority_score": score_candidate(self),
            "recommendation": self.recommendation,
            "signals": list(self.signals),
            "recurrence_count": self.recurrence_count,
        }


@dataclass(frozen=True)
class SelfInspectionArtifactPaths:
    """Paths written by a self-inspection pass."""

    self_inspection_path: Path
    backlog_path: Path


@dataclass(frozen=True)
class SelectionArtifactPaths:
    """Paths written by a select-next pass."""

    selected_tasks_path: Path
    loop_plan_path: Path
    history_path: Path


def run_self_inspection(
    *, root: Path, now: str | None = None, loop_id: str | None = None
) -> SelfInspectionArtifactPaths:
    """Inspect local QA-Z artifacts and update the improvement backlog."""
    root = root.resolve()
    generated_at = now or utc_now()
    resolved_loop_id = loop_id or default_loop_id("inspect", generated_at)
    existing_backlog = load_backlog(root)
    candidates = discover_candidates(root, existing=existing_backlog)
    report = {
        "kind": SELF_INSPECTION_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "loop_id": resolved_loop_id,
        "generated_at": generated_at,
        "evidence_sources": evidence_sources(candidates),
        "candidates": [candidate.to_dict() for candidate in candidates],
    }
    backlog = merge_backlog(
        existing=existing_backlog,
        candidates=candidates,
        now=generated_at,
    )

    latest_dir = root / ".qa-z" / "loops" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    self_inspection_path = latest_dir / "self_inspect.json"
    backlog_path = backlog_file(root)
    write_json(self_inspection_path, report)
    write_json(backlog_path, backlog)
    return SelfInspectionArtifactPaths(
        self_inspection_path=self_inspection_path,
        backlog_path=backlog_path,
    )


def select_next_tasks(
    *,
    root: Path,
    count: int = 3,
    now: str | None = None,
    loop_id: str | None = None,
) -> SelectionArtifactPaths:
    """Select the next highest-value open backlog items and persist loop memory."""
    root = root.resolve()
    generated_at = now or utc_now()
    resolved_loop_id = loop_id or default_loop_id("loop", generated_at)
    backlog = load_backlog(root)
    selected_count = min(max(count, 1), 3)
    open_items = [
        item
        for item in backlog.get("items", [])
        if isinstance(item, dict) and str(item.get("status", "open")) in OPEN_STATUSES
    ]
    history_path = root / ".qa-z" / "loops" / "history.jsonl"
    recent_entries = load_history_entries(history_path)[-RECENT_SELECTION_WINDOW:]
    scored_items = [
        apply_selection_penalty(
            item, recent_entries=recent_entries, open_items=open_items
        )
        for item in open_items
    ]
    selected_items = select_items_with_batch_diversity(
        scored_items=scored_items,
        count=selected_count,
    )

    latest_dir = root / ".qa-z" / "loops" / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    selected_tasks_path = latest_dir / "selected_tasks.json"
    loop_plan_path = latest_dir / "loop_plan.md"

    selected_artifact = {
        "kind": SELECTED_TASKS_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "loop_id": resolved_loop_id,
        "generated_at": generated_at,
        "source_backlog": format_path(backlog_file(root), root),
        "selected_tasks": selected_items,
    }
    write_json(selected_tasks_path, selected_artifact)
    loop_plan_path.write_text(
        render_loop_plan(
            loop_id=resolved_loop_id,
            generated_at=generated_at,
            selected_items=selected_items,
        ),
        encoding="utf-8",
    )
    append_history(
        history_path,
        loop_id=resolved_loop_id,
        generated_at=generated_at,
        selected_items=selected_items,
        open_items=scored_items,
    )
    return SelectionArtifactPaths(
        selected_tasks_path=selected_tasks_path,
        loop_plan_path=loop_plan_path,
        history_path=history_path,
    )


def load_backlog(root: Path) -> dict[str, Any]:
    """Load the improvement backlog, returning an empty stable artifact if absent."""
    path = backlog_file(root)
    if not path.is_file():
        return empty_backlog()
    loaded = read_json_object(path)
    if loaded.get("kind") != BACKLOG_KIND:
        return empty_backlog()
    items = loaded.get("items")
    if not isinstance(items, list):
        loaded["items"] = []
    return loaded


def score_candidate(candidate: BacklogCandidate) -> int:
    """Score one candidate using deterministic impact and evidence bonuses."""
    score = (
        candidate.impact * candidate.likelihood * candidate.confidence
    ) - candidate.repair_cost
    signals = set(candidate.signals)
    if "benchmark_fail" in signals:
        score += 2
    if {"verify_regressed", "verify_mixed"} & signals:
        score += 2
    if "schema_doc_drift" in signals:
        score += 1
    if "executor_validation_failed" in signals:
        score += 2
    if "executor_result_no_op" in signals:
        score += 1
    if "executor_result_failed" in signals:
        score += 1
    if "executor_dry_run_blocked" in signals:
        score += 2
    if "executor_dry_run_attention" in signals:
        score += 1
    if "mixed_surface_realism_gap" in signals:
        score += 2
    if "recent_empty_loop_chain" in signals:
        score += 2
    if "recent_fallback_family_repeat" in signals:
        score += 2
    if "worktree_integration_risk" in signals:
        score += 1
    if "dirty_worktree_large" in signals:
        score += 2
    if "commit_order_dependency_exists" in signals:
        score += 2
    if "deferred_cleanup_repeated" in signals:
        score += 1
    if "generated_artifact_policy_ambiguity" in signals:
        score += 1
    if "service_readiness_gap" in signals:
        score += 2
    if "roadmap_gap" in signals:
        score += 2
    if candidate.recurrence_count >= 2:
        score += 1
    if "regression_prevention" in signals:
        score += 1
    return int(score)


def discover_candidates(
    root: Path, existing: dict[str, Any] | None = None
) -> list[BacklogCandidate]:
    """Find evidence-backed improvement candidates in local artifacts."""
    backlog = existing or empty_backlog()
    live_signals = collect_live_repository_signals(root)
    candidates: list[BacklogCandidate] = []
    candidates.extend(discover_benchmark_candidates(root))
    candidates.extend(discover_verification_candidates(root))
    candidates.extend(discover_session_candidates(root))
    candidates.extend(discover_executor_result_candidates(root))
    candidates.extend(discover_executor_ingest_candidates(root))
    candidates.extend(discover_executor_history_candidates(root))
    candidates.extend(discover_artifact_consistency_candidates(root))
    candidates.extend(discover_docs_drift_candidates(root))
    candidates.extend(discover_coverage_gap_candidates(root))
    candidates.extend(discover_executor_contract_candidates(root))
    candidates.extend(discover_worktree_risk_candidates(root, live_signals))
    candidates.extend(discover_deferred_cleanup_candidates(root, live_signals))
    candidates.extend(discover_commit_isolation_candidates(root, live_signals))
    candidates.extend(discover_artifact_hygiene_candidates(root, live_signals))
    candidates.extend(discover_runtime_artifact_cleanup_candidates(root, live_signals))
    candidates.extend(discover_evidence_freshness_candidates(root, live_signals))
    candidates.extend(discover_integration_gap_candidates(root))
    candidates.extend(discover_empty_loop_candidates(root))
    candidates.extend(discover_repeated_fallback_family_candidates(root))
    candidates.extend(discover_backlog_reseeding_candidates(root, backlog, candidates))
    return unique_candidates(sorted(candidates, key=lambda candidate: candidate.id))


def discover_benchmark_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from failed benchmark summary artifacts."""
    candidates: list[BacklogCandidate] = []
    for path, summary in benchmark_summaries(root):
        failed_count = int_value(summary.get("fixtures_failed"))
        if failed_count <= 0:
            continue
        candidate_count_before = len(candidates)
        snapshot = benchmark_summary_snapshot(summary)
        fixtures = summary.get("fixtures")
        failed_names = [
            str(name)
            for name in summary.get("failed_fixtures", [])
            if str(name).strip()
        ]
        if isinstance(fixtures, list):
            for fixture in fixtures:
                if not isinstance(fixture, dict) or fixture.get("passed") is not False:
                    continue
                name = str(fixture.get("name") or "unknown").strip()
                failures = [
                    str(item)
                    for item in fixture.get("failures", [])
                    if str(item).strip()
                ]
                candidates.append(
                    benchmark_candidate(
                        root,
                        path,
                        name,
                        failures=failures,
                        snapshot=snapshot,
                    )
                )
        else:
            for name in failed_names:
                candidates.append(
                    benchmark_candidate(
                        root,
                        path,
                        name,
                        failures=[],
                        snapshot=snapshot,
                    )
                )
        if len(candidates) == candidate_count_before:
            fixture_word = "fixture" if failed_count == 1 else "fixtures"
            candidates.append(
                benchmark_candidate(
                    root,
                    path,
                    "summary",
                    failures=[
                        (
                            f"benchmark summary reports {failed_count} failed "
                            f"{fixture_word} without fixture details"
                        )
                    ],
                    snapshot=snapshot,
                )
            )
    return unique_candidates(candidates)


def benchmark_candidate(
    root: Path,
    path: Path,
    fixture_name: str,
    *,
    failures: list[str],
    snapshot: str = "",
) -> BacklogCandidate:
    """Build a benchmark-gap candidate from one failed fixture."""
    name = fixture_name or "unknown"
    summary = (
        f"fixture={name}; failures={'; '.join(failures[:3])}"
        if failures
        else f"fixture={name} failed"
    )
    if snapshot:
        summary = f"snapshot={snapshot}; {summary}"
    return BacklogCandidate(
        id=f"benchmark_gap-{slugify(name)}",
        title=f"Fix benchmark fixture failure: {name}",
        category="benchmark_gap",
        evidence=[
            {
                "source": "benchmark",
                "path": format_path(path, root),
                "summary": summary,
            }
        ],
        impact=4,
        likelihood=4,
        confidence=4,
        repair_cost=4,
        recommendation="add_benchmark_fixture",
        signals=["benchmark_fail"],
    )


def benchmark_summary_snapshot(summary: dict[str, Any]) -> str:
    """Return compact benchmark snapshot text when available."""
    snapshot = str(summary.get("snapshot") or "").strip()
    if snapshot:
        return snapshot
    passed = summary.get("fixtures_passed")
    total = summary.get("fixtures_total")
    overall_rate = summary.get("overall_rate")
    if passed is None or total is None or overall_rate is None:
        return ""
    overall_rate_text = str(overall_rate).strip()
    if not overall_rate_text:
        return ""
    return (
        f"{int_value(passed)}/{int_value(total)} fixtures, "
        f"overall_rate {overall_rate_text}"
    )


def discover_verification_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from problematic verification verdicts."""
    candidates: list[BacklogCandidate] = []
    qa_root = root / ".qa-z"
    if not qa_root.exists():
        return candidates
    for path in sorted(qa_root.rglob("verify/summary.json")):
        summary = read_json_object(path)
        if summary.get("kind") != "qa_z.verify_summary":
            continue
        verdict = str(summary.get("verdict") or "")
        if verdict not in VERIFICATION_PROBLEM_VERDICTS:
            continue
        run_id = path.parent.parent.name
        signals = ["regression_prevention"]
        if verdict == "mixed":
            signals.append("verify_mixed")
        else:
            signals.append("verify_regressed")
        candidates.append(
            BacklogCandidate(
                id=f"verify_regression-{slugify(run_id)}",
                title=f"Stabilize verification verdict: {verdict} in {run_id}",
                category="verify_regression",
                evidence=[
                    {
                        "source": "verification",
                        "path": format_path(path, root),
                        "summary": (
                            f"verdict={verdict}; "
                            f"regressions={int_value(summary.get('regression_count'))}; "
                            f"new_issues={int_value(summary.get('new_issue_count'))}"
                        ),
                    }
                ],
                impact=5 if verdict == "regressed" else 4,
                likelihood=4,
                confidence=4,
                repair_cost=4,
                recommendation="stabilize_verification_surface",
                signals=signals,
            )
        )
    return unique_candidates(candidates)


def discover_session_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from incomplete repair sessions."""
    sessions_root = root / ".qa-z" / "sessions"
    if not sessions_root.is_dir():
        return []
    candidates: list[BacklogCandidate] = []
    for path in sorted(sessions_root.glob("*/session.json")):
        manifest = read_json_object(path)
        if manifest.get("kind") != "qa_z.repair_session":
            continue
        state = str(manifest.get("state") or "")
        if state not in INCOMPLETE_SESSION_STATES:
            continue
        session_id = str(manifest.get("session_id") or path.parent.name)
        candidates.append(
            BacklogCandidate(
                id=f"session_gap-{slugify(session_id)}",
                title=f"Resolve incomplete repair session: {session_id}",
                category="session_gap",
                evidence=[
                    {
                        "source": "repair_session",
                        "path": format_path(path, root),
                        "summary": f"state={state}",
                    }
                ],
                impact=3,
                likelihood=4,
                confidence=4,
                repair_cost=3,
                recommendation="create_repair_session",
                signals=[],
            )
        )
    return candidates


def discover_executor_result_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from stored executor-result artifacts."""
    sessions_root = root / ".qa-z" / "sessions"
    if not sessions_root.is_dir():
        return []
    candidates: list[BacklogCandidate] = []
    for path in sorted(sessions_root.glob("*/session.json")):
        manifest = read_json_object(path)
        if manifest.get("kind") != "qa_z.repair_session":
            continue
        session_id = str(manifest.get("session_id") or path.parent.name)
        result_status = str(manifest.get("executor_result_status") or "").strip()
        if result_status not in {"partial", "failed", "no_op"}:
            continue
        result_path_text = str(manifest.get("executor_result_path") or "").strip()
        result_path = resolve_optional_artifact_path(root, result_path_text)
        result = (
            read_json_object(result_path)
            if result_path is not None and result_path.is_file()
            else {}
        )
        validation = result.get("validation")
        validation_status = (
            str(validation.get("status") or "").strip()
            if isinstance(validation, dict)
            else str(manifest.get("executor_result_validation_status") or "").strip()
        )
        verification_hint = str(result.get("verification_hint") or "").strip() or "skip"
        recommendation = recommendation_for_executor_result(result_status)
        title = title_for_executor_result(result_status, session_id)
        signals = [f"executor_result_{result_status}"]
        if validation_status == "failed":
            signals.append("executor_validation_failed")
        candidates.append(
            BacklogCandidate(
                id=f"executor_result_gap-{slugify(session_id)}",
                title=title,
                category="executor_result_gap",
                evidence=[
                    {
                        "source": "executor_result",
                        "path": (
                            format_path(result_path, root)
                            if result_path is not None
                            else format_path(path, root)
                        ),
                        "summary": (
                            f"status={result_status}; "
                            f"validation={validation_status or 'unknown'}; "
                            f"hint={verification_hint}"
                        ),
                    }
                ],
                impact=4 if result_status in {"failed", "no_op"} else 3,
                likelihood=4,
                confidence=4 if validation_status else 3,
                repair_cost=3,
                recommendation=recommendation,
                signals=signals,
            )
        )
    return unique_candidates(candidates)


def discover_executor_ingest_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from stored executor ingest outcomes and implications."""
    ingest_root = root / ".qa-z" / "executor-results"
    if not ingest_root.is_dir():
        return []
    candidates: list[BacklogCandidate] = []
    for path in sorted(ingest_root.glob("*/ingest.json")):
        ingest = read_json_object(path)
        if ingest.get("kind") != "qa_z.executor_result_ingest":
            continue
        implications = ingest.get("backlog_implications")
        if not isinstance(implications, list):
            continue
        for implication in implications:
            if not isinstance(implication, dict):
                continue
            candidate_id = str(implication.get("id") or "").strip()
            category = str(implication.get("category") or "").strip()
            recommendation = str(implication.get("recommendation") or "").strip()
            title = str(implication.get("title") or "").strip()
            if not candidate_id or not category or not recommendation or not title:
                continue
            signals = implication_signals(implication.get("signals"))
            candidates.append(
                BacklogCandidate(
                    id=candidate_id,
                    title=title,
                    category=category,
                    evidence=[
                        {
                            "source": "executor_result_ingest",
                            "path": format_path(path, root),
                            "summary": str(
                                implication.get("summary")
                                or ingest.get("ingest_status")
                                or "executor ingest implication"
                            ),
                        }
                    ],
                    impact=max(int_value(implication.get("impact")), 1),
                    likelihood=max(int_value(implication.get("likelihood")), 1),
                    confidence=max(int_value(implication.get("confidence")), 1),
                    repair_cost=max(int_value(implication.get("repair_cost")), 1),
                    recommendation=recommendation,
                    signals=signals,
                )
            )
    return unique_candidates(candidates)


def discover_executor_history_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from repeated executor-result attempt history patterns."""
    sessions_root = root / ".qa-z" / "sessions"
    if not sessions_root.is_dir():
        return []
    candidates: list[BacklogCandidate] = []
    for path in sorted(sessions_root.glob("*/executor_results/history.json")):
        history = read_json_object(path)
        if history.get("kind") != "qa_z.executor_result_history":
            continue
        session_id = str(history.get("session_id") or path.parent.parent.name)
        attempts = [
            item for item in history.get("attempts", []) if isinstance(item, dict)
        ]
        dry_run_path = path.parent / "dry_run_summary.json"
        dry_run, dry_run_is_fallback = load_or_synthesize_executor_dry_run_summary(
            root=root,
            history_path=path,
            summary_path=dry_run_path,
            session_id=session_id,
            attempts=attempts,
        )
        if not attempts and not dry_run:
            continue
        partial_count = sum(
            1 for item in attempts if str(item.get("result_status") or "") == "partial"
        )
        noop_count = sum(
            1
            for item in attempts
            if str(item.get("result_status") or "") in {"no_op", "not_applicable"}
        )
        rejected_count = sum(
            1
            for item in attempts
            if str(item.get("ingest_status") or "").startswith("rejected_")
        )
        latest = attempts[-1] if attempts else {}
        signal_set = dry_run_signal_set(dry_run)
        dry_run_verdict = str(dry_run.get("verdict") or "").strip()
        summary = history_evidence_summary(
            attempt_count=len(attempts),
            latest_result_status=str(latest.get("result_status") or "unknown"),
            latest_ingest_status=str(latest.get("ingest_status") or "unknown"),
            dry_run=dry_run,
        )
        evidence = [
            {
                "source": "executor_result_history",
                "path": format_path(path, root),
                "summary": summary,
            }
        ]
        if dry_run:
            evidence.append(
                {
                    "source": (
                        "executor_result_dry_run_fallback"
                        if dry_run_is_fallback
                        else "executor_result_dry_run"
                    ),
                    "path": format_path(
                        path if dry_run_is_fallback else dry_run_path, root
                    ),
                    "summary": dry_run_evidence_summary(dry_run),
                }
            )
        if partial_count >= 2 or "repeated_partial_attempts" in signal_set:
            signals = ["executor_result_partial", "regression_prevention"]
            if dry_run_verdict == "attention_required":
                signals.append("executor_dry_run_attention")
            candidates.append(
                BacklogCandidate(
                    id=f"partial_completion_gap-{slugify(session_id)}-history",
                    title=f"Inspect repeated partial executor attempts: {session_id}",
                    category="partial_completion_gap",
                    evidence=evidence,
                    impact=4,
                    likelihood=4,
                    confidence=4,
                    repair_cost=3,
                    recommendation="harden_partial_completion_handling",
                    signals=signals,
                )
            )
        if (
            noop_count >= 2
            or {
                "repeated_no_op_attempts",
                "missing_no_op_explanation",
            }
            & signal_set
        ):
            signals = ["executor_result_no_op", "regression_prevention"]
            if dry_run_verdict == "attention_required":
                signals.append("executor_dry_run_attention")
            candidates.append(
                BacklogCandidate(
                    id=f"no_op_safeguard_gap-{slugify(session_id)}-history",
                    title=f"Inspect repeated no-op executor attempts: {session_id}",
                    category="no_op_safeguard_gap",
                    evidence=evidence,
                    impact=3,
                    likelihood=4,
                    confidence=4,
                    repair_cost=3,
                    recommendation="harden_executor_no_op_safeguards",
                    signals=signals,
                )
            )
        if (
            rejected_count >= 2
            or (
                str(latest.get("result_status") or "") == "completed"
                and (
                    str(latest.get("verify_resume_status") or "") == "verify_blocked"
                    or str(latest.get("verification_verdict") or "")
                    in {"mixed", "regressed", "verification_failed"}
                )
            )
            or str(dry_run.get("verdict") or "") == "blocked"
            or {
                "repeated_rejected_attempts",
                "completed_verify_blocked",
                "scope_validation_failed",
                "validation_conflict",
            }
            & signal_set
        ):
            signals = ["service_readiness_gap", "regression_prevention"]
            if dry_run_verdict == "blocked":
                signals.append("executor_dry_run_blocked")
            elif dry_run_verdict == "attention_required":
                signals.append("executor_dry_run_attention")
            candidates.append(
                BacklogCandidate(
                    id=f"workflow_gap-{slugify(session_id)}-history",
                    title=f"Audit repeated executor attempt friction: {session_id}",
                    category="workflow_gap",
                    evidence=evidence,
                    impact=3,
                    likelihood=4,
                    confidence=4,
                    repair_cost=3,
                    recommendation="audit_executor_contract",
                    signals=signals,
                )
            )
    return unique_candidates(candidates)


def load_executor_dry_run_summary(path: Path) -> dict[str, Any]:
    """Load one session dry-run summary when it exists and looks valid."""
    if not path.is_file():
        return {}
    summary = read_json_object(path)
    if summary.get("kind") != "qa_z.executor_result_dry_run":
        return {}
    return {
        **summary,
        "summary_source": summary.get("summary_source") or "materialized",
    }


def load_or_synthesize_executor_dry_run_summary(
    *,
    root: Path,
    history_path: Path,
    summary_path: Path,
    session_id: str,
    attempts: list[dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    """Load a dry-run summary or synthesize one from history when needed."""
    summary = load_executor_dry_run_summary(summary_path)
    if summary:
        return summary, False
    if not attempts:
        return {}, False
    return (
        {
            **build_dry_run_summary(
                session_id=session_id,
                history_path=format_path(history_path, root),
                report_path=format_path(
                    history_path.parent / "dry_run_report.md", root
                ),
                safety_package_id=None,
                attempts=attempts,
            ),
            "summary_source": "history_fallback",
        },
        True,
    )


def dry_run_signal_set(summary: dict[str, Any]) -> set[str]:
    """Return normalized dry-run signal ids."""
    return {
        str(item) for item in summary.get("history_signals", []) if str(item).strip()
    }


def history_evidence_summary(
    *,
    attempt_count: int,
    latest_result_status: str,
    latest_ingest_status: str,
    dry_run: dict[str, Any],
) -> str:
    """Render a compact history evidence summary for self-inspection."""
    parts = [
        f"attempts={attempt_count}",
        f"latest={latest_result_status or 'unknown'}",
        f"latest_ingest={latest_ingest_status or 'unknown'}",
    ]
    if dry_run:
        parts.append(f"dry_run={dry_run.get('verdict') or 'unknown'}")
        parts.append(f"source={dry_run.get('summary_source') or 'unknown'}")
        reason = str(dry_run.get("verdict_reason") or "").strip()
        if reason:
            parts.append(f"reason={reason}")
    return "; ".join(parts)


def dry_run_evidence_summary(summary: dict[str, Any]) -> str:
    """Render one compact dry-run evidence summary for self-inspection."""
    signals = ",".join(dry_run_signal_set(summary)) or "none"
    return (
        f"dry_run={summary.get('verdict') or 'unknown'}; "
        f"source={summary.get('summary_source') or 'unknown'}; "
        f"reason={summary.get('verdict_reason') or 'unknown'}; "
        f"signals={signals}; "
        f"next={summary.get('next_recommendation') or 'inspect executor attempt history'}"
    )


def recommendation_for_executor_result(result_status: str) -> str:
    """Return the deterministic next action for an executor-result status."""
    if result_status == "partial":
        return "resume_executor_repair"
    if result_status == "failed":
        return "triage_executor_failure"
    return "inspect_executor_no_op"


def title_for_executor_result(result_status: str, session_id: str) -> str:
    """Return a human-readable backlog title for executor-result follow-up."""
    if result_status == "partial":
        return f"Resume partial executor result: {session_id}"
    if result_status == "failed":
        return f"Triage failed executor result: {session_id}"
    return f"Inspect executor no-op result: {session_id}"


def implication_signals(value: object) -> list[str]:
    """Return stable implication signals from a JSON-safe value."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def discover_artifact_consistency_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates when related local artifacts are missing."""
    candidates: list[BacklogCandidate] = []
    qa_root = root / ".qa-z"
    if not qa_root.exists():
        return candidates
    for summary_path in sorted(qa_root.rglob("verify/summary.json")):
        missing = [
            sibling.name
            for sibling in (
                summary_path.parent / "compare.json",
                summary_path.parent / "report.md",
            )
            if not sibling.is_file()
        ]
        if not missing:
            continue
        candidates.append(
            BacklogCandidate(
                id=f"artifact_consistency-{slugify(summary_path.parent.parent.name)}",
                title=(
                    "Restore verification companion artifacts for "
                    f"{summary_path.parent.parent.name}"
                ),
                category="artifact_consistency",
                evidence=[
                    {
                        "source": "verification",
                        "path": format_path(summary_path, root),
                        "summary": "missing companions: " + ", ".join(missing),
                    }
                ],
                impact=3,
                likelihood=3,
                confidence=4,
                repair_cost=2,
                recommendation="sync_contract_and_docs",
                signals=[],
            )
        )
    return candidates


def discover_docs_drift_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates when public docs omit the self-improvement surface."""
    candidates: list[BacklogCandidate] = []
    readme = root / "README.md"
    if readme.is_file():
        text = read_text(readme)
        missing = [term for term in EXPECTED_COMMAND_DOC_TERMS if term not in text]
        if missing:
            candidates.append(
                BacklogCandidate(
                    id="docs_drift-self_improvement_commands",
                    title="Document self-improvement CLI commands",
                    category="docs_drift",
                    evidence=[
                        {
                            "source": "docs",
                            "path": format_path(readme, root),
                            "summary": "missing terms: " + ", ".join(missing),
                        }
                    ],
                    impact=3,
                    likelihood=3,
                    confidence=3,
                    repair_cost=2,
                    recommendation="sync_contract_and_docs",
                    signals=["schema_doc_drift"],
                )
            )

    schema_doc = root / "docs" / "artifact-schema-v1.md"
    if schema_doc.is_file() and "Self-Improvement" not in read_text(schema_doc):
        candidates.append(
            BacklogCandidate(
                id="schema_drift-self_improvement_artifacts",
                title="Document self-improvement artifact schemas",
                category="schema_drift",
                evidence=[
                    {
                        "source": "schema_doc",
                        "path": format_path(schema_doc, root),
                        "summary": "self-improvement artifacts are not documented",
                    }
                ],
                impact=3,
                likelihood=3,
                confidence=3,
                repair_cost=2,
                recommendation="sync_contract_and_docs",
                signals=["schema_doc_drift"],
            )
        )
    report_evidence = docs_drift_report_evidence(root)
    if report_evidence:
        candidates.append(
            BacklogCandidate(
                id="docs_drift-current_truth_sync",
                title="Run a current-truth docs and schema sync audit",
                category="docs_drift",
                evidence=report_evidence,
                impact=2,
                likelihood=3,
                confidence=4,
                repair_cost=2,
                recommendation="sync_contract_and_docs",
                signals=["roadmap_gap", "schema_doc_drift"],
            )
        )
    return candidates


def discover_coverage_gap_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from benchmark realism and coverage gaps."""
    evidence = mixed_surface_coverage_evidence(root)
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="coverage_gap-mixed-surface-benchmark-realism",
            title="Expand executed mixed-surface benchmark realism",
            category="coverage_gap",
            evidence=evidence,
            impact=4,
            likelihood=4,
            confidence=3,
            repair_cost=3,
            recommendation="add_benchmark_fixture",
            signals=[
                "mixed_surface_realism_gap",
                "roadmap_gap",
                "service_readiness_gap",
            ],
        )
    ]


def discover_executor_contract_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from executor contract and ingest/resume gaps."""
    evidence = executor_contract_gap_evidence(root)
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="workflow_gap-executor-contract-completeness",
            title="Audit executor contract completeness and resume coverage",
            category="workflow_gap",
            evidence=evidence,
            impact=3,
            likelihood=3,
            confidence=3,
            repair_cost=3,
            recommendation="audit_executor_contract",
            signals=["roadmap_gap", "service_readiness_gap"],
        )
    ]


def discover_worktree_risk_candidates(
    root: Path, live_signals: dict[str, Any]
) -> list[BacklogCandidate]:
    """Create candidates from large live dirty-worktree signals."""
    modified = int_value(live_signals.get("modified_count"))
    untracked = int_value(live_signals.get("untracked_count"))
    staged = int_value(live_signals.get("staged_count"))
    total_dirty = modified + untracked
    if modified < DIRTY_WORKTREE_MODIFIED_THRESHOLD and (
        total_dirty <= DIRTY_WORKTREE_TOTAL_THRESHOLD
    ):
        return []
    dirty_paths = list_signal_paths(live_signals, "modified_paths") + list_signal_paths(
        live_signals, "untracked_paths"
    )
    sample_paths = sample_signal_paths(dirty_paths)
    summary = f"modified={modified}; untracked={untracked}; staged={staged}"
    area_summary = worktree_area_summary(dirty_paths)
    if area_summary:
        summary += "; areas=" + area_summary
    if sample_paths:
        summary += "; sample=" + ", ".join(sample_paths)
    signals = ["dirty_worktree_large", "worktree_integration_risk"]
    if staged > 0:
        signals.append("staged_changes_present")
    return [
        BacklogCandidate(
            id="worktree_risk-dirty-worktree",
            title="Reduce dirty worktree integration risk",
            category="worktree_risk",
            evidence=[
                {
                    "source": "git_status",
                    "path": ".",
                    "summary": summary,
                }
            ],
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=3,
            recommendation="reduce_integration_risk",
            signals=signals,
        )
    ]


def discover_deferred_cleanup_candidates(
    root: Path, live_signals: dict[str, Any]
) -> list[BacklogCandidate]:
    """Create candidates from deferred cleanup notes and generated output drift."""
    evidence = deferred_cleanup_evidence(root)
    benchmark_paths = list_signal_paths(live_signals, "benchmark_result_paths")
    if benchmark_paths and evidence:
        evidence.append(
            {
                "source": "generated_outputs",
                "path": benchmark_paths[0],
                "summary": (
                    "generated benchmark outputs still present: "
                    + ", ".join(sample_signal_paths(benchmark_paths))
                ),
            }
        )
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="deferred_cleanup_gap-worktree-deferred-items",
            title="Triage deferred cleanup items before they drift further",
            category="deferred_cleanup_gap",
            evidence=evidence,
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=3,
            recommendation="triage_and_isolate_changes",
            signals=["deferred_cleanup_repeated", "worktree_integration_risk"],
        )
    ]


def discover_commit_isolation_candidates(
    root: Path, live_signals: dict[str, Any]
) -> list[BacklogCandidate]:
    """Create candidates from commit-order dependency evidence."""
    evidence = commit_isolation_evidence(root)
    modified = int_value(live_signals.get("modified_count"))
    untracked = int_value(live_signals.get("untracked_count"))
    if evidence and (modified or untracked):
        dirty_paths = list_signal_paths(
            live_signals, "modified_paths"
        ) + list_signal_paths(live_signals, "untracked_paths")
        summary = (
            f"dirty worktree still spans modified={modified}; untracked={untracked}"
        )
        area_summary = worktree_area_summary(dirty_paths)
        if area_summary:
            summary += "; areas=" + area_summary
        evidence.append(
            {
                "source": "git_status",
                "path": ".",
                "summary": summary,
            }
        )
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="commit_isolation_gap-foundation-order",
            title="Isolate the foundation commit before later batches",
            category="commit_isolation_gap",
            evidence=evidence,
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=4,
            recommendation="isolate_foundation_commit",
            signals=["commit_order_dependency_exists", "worktree_integration_risk"],
        )
    ]


def discover_artifact_hygiene_candidates(
    root: Path, live_signals: dict[str, Any]
) -> list[BacklogCandidate]:
    """Create candidates from runtime/source artifact separation gaps."""
    if generated_artifact_policy_is_explicit(live_signals) and not list_signal_paths(
        live_signals, "runtime_artifact_paths"
    ):
        return []
    evidence = artifact_hygiene_evidence(root)
    runtime_paths = list_signal_paths(live_signals, "runtime_artifact_paths")
    benchmark_paths = (
        []
        if generated_artifact_policy_is_explicit(live_signals)
        else list_signal_paths(live_signals, "benchmark_result_paths")
    )
    mixed_paths = sample_signal_paths(runtime_paths + benchmark_paths)
    if evidence or (runtime_paths and benchmark_paths):
        evidence.append(
            {
                "source": "runtime_artifacts",
                "path": mixed_paths[0] if mixed_paths else ".",
                "summary": (
                    "runtime or generated artifacts are still mixed into the "
                    "repository surface: "
                    + ", ".join(
                        mixed_paths or ["runtime artifact policy remains ambiguous"]
                    )
                ),
            }
        )
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="artifact_hygiene_gap-runtime-source-separation",
            title="Separate runtime artifacts from source-tracked evidence",
            category="artifact_hygiene_gap",
            evidence=evidence,
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=3,
            recommendation="separate_runtime_from_source_artifacts",
            signals=[
                "generated_artifact_policy_ambiguity",
                "worktree_integration_risk",
            ],
        )
    ]


def discover_runtime_artifact_cleanup_candidates(
    root: Path, live_signals: dict[str, Any]
) -> list[BacklogCandidate]:
    """Create candidates when generated benchmark/runtime artifacts need cleanup."""
    if generated_artifact_policy_is_explicit(live_signals) and not list_signal_paths(
        live_signals, "runtime_artifact_paths"
    ):
        return []
    runtime_paths = sample_signal_paths(
        list_signal_paths(live_signals, "runtime_artifact_paths")
        + (
            []
            if generated_artifact_policy_is_explicit(live_signals)
            else list_signal_paths(live_signals, "benchmark_result_paths")
        )
    )
    report_evidence = deferred_cleanup_evidence(root) or artifact_hygiene_evidence(root)
    if not runtime_paths or not report_evidence:
        return []
    evidence = list(report_evidence)
    evidence.append(
        {
            "source": "runtime_artifacts",
            "path": runtime_paths[0],
            "summary": "generated runtime artifacts need explicit cleanup handling: "
            + ", ".join(runtime_paths),
        }
    )
    return [
        BacklogCandidate(
            id="runtime_artifact_cleanup_gap-generated-results",
            title="Clean up generated runtime artifacts before source integration",
            category="runtime_artifact_cleanup_gap",
            evidence=evidence,
            impact=3,
            likelihood=4,
            confidence=4,
            repair_cost=3,
            recommendation="triage_and_isolate_changes",
            signals=[
                "generated_artifact_policy_ambiguity",
                "worktree_integration_risk",
            ],
        )
    ]


def discover_evidence_freshness_candidates(
    root: Path, live_signals: dict[str, Any]
) -> list[BacklogCandidate]:
    """Create candidates from ambiguous frozen-vs-generated evidence handling."""
    if generated_artifact_policy_is_explicit(live_signals) and not list_signal_paths(
        live_signals, "runtime_artifact_paths"
    ):
        return []
    evidence = evidence_freshness_evidence(root)
    benchmark_paths = (
        []
        if generated_artifact_policy_is_explicit(live_signals)
        else list_signal_paths(live_signals, "benchmark_result_paths")
    )
    policy_evidence = generated_artifact_policy_evidence(root, live_signals)
    if policy_evidence and (
        evidence or list_signal_paths(live_signals, "runtime_artifact_paths")
    ):
        evidence.extend(policy_evidence)
    if benchmark_paths and evidence:
        evidence.append(
            {
                "source": "benchmark_results",
                "path": benchmark_paths[0],
                "summary": (
                    "benchmark result artifacts exist without a clear frozen-evidence "
                    "decision: " + ", ".join(sample_signal_paths(benchmark_paths))
                ),
            }
        )
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="evidence_freshness_gap-generated-vs-frozen-policy",
            title="Clarify generated versus frozen evidence policy",
            category="evidence_freshness_gap",
            evidence=evidence,
            impact=3,
            likelihood=4,
            confidence=4,
            repair_cost=3,
            recommendation="clarify_generated_vs_frozen_evidence_policy",
            signals=["generated_artifact_policy_ambiguity"],
        )
    ]


def discover_integration_gap_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from worktree integration and cleanup risk evidence."""
    evidence = integration_gap_evidence(root)
    if not evidence:
        return []
    return [
        BacklogCandidate(
            id="integration_gap-worktree-integration-risk",
            title="Audit worktree integration and commit-split risk",
            category="integration_gap",
            evidence=evidence,
            impact=2,
            likelihood=3,
            confidence=4,
            repair_cost=2,
            recommendation="audit_worktree_integration",
            signals=["worktree_integration_risk"],
        )
    ]


def discover_empty_loop_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from repeated empty-loop history chains."""
    history_path = root / ".qa-z" / "loops" / "history.jsonl"
    entries = load_history_entries(history_path)
    if len(entries) < EMPTY_LOOP_CHAIN_LENGTH:
        return []
    recent = entries[-EMPTY_LOOP_CHAIN_LENGTH:]
    if not all(is_empty_loop_entry(entry) for entry in recent):
        return []
    states = [str(entry.get("state") or "unknown") for entry in recent]
    return [
        BacklogCandidate(
            id="autonomy_selection_gap-empty-loop-chain",
            title="Prevent repeated empty autonomy selection loops",
            category="autonomy_selection_gap",
            evidence=[
                {
                    "source": "loop_history",
                    "path": format_path(history_path, root),
                    "summary": (
                        f"recent_empty_loops={len(recent)}; states={', '.join(states)}"
                    ),
                }
            ],
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=2,
            recommendation="improve_empty_loop_handling",
            signals=["recent_empty_loop_chain", "service_readiness_gap"],
        )
    ]


def discover_repeated_fallback_family_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from repeated fallback-family reuse in recent loops."""
    history_path = root / ".qa-z" / "loops" / "history.jsonl"
    entries = load_history_entries(history_path)
    if len(entries) < FALLBACK_REPEAT_WINDOW:
        return []
    recent = entries[-FALLBACK_REPEAT_WINDOW:]
    families = [
        selected_task_fallback_families(entry, open_items=[]) for entry in recent
    ]
    if not all(len(item) == 1 for item in families):
        return []
    family = next(iter(families[0]))
    if not all(next(iter(item)) == family for item in families[1:]):
        return []
    states = [str(entry.get("state") or "unknown") for entry in recent]
    return [
        BacklogCandidate(
            id=f"autonomy_selection_gap-repeated-fallback-{slugify(family)}",
            title="Diversify repeated fallback selections across task families",
            category="autonomy_selection_gap",
            evidence=[
                {
                    "source": "loop_history",
                    "path": format_path(history_path, root),
                    "summary": (
                        f"recent_fallback_family={family}; loops={len(recent)}; "
                        f"states={', '.join(states)}"
                    ),
                }
            ],
            impact=4,
            likelihood=4,
            confidence=4,
            repair_cost=2,
            recommendation="improve_fallback_diversity",
            signals=["recent_fallback_family_repeat", "service_readiness_gap"],
        )
    ]


def discover_backlog_reseeding_candidates(
    root: Path, backlog: dict[str, Any], candidates: list[BacklogCandidate]
) -> list[BacklogCandidate]:
    """Create a backlog-reseeding candidate when open work would otherwise vanish."""
    open_items = open_backlog_items(backlog)
    if open_items:
        return []
    supporting = [
        candidate
        for candidate in candidates
        if candidate.category
        in {
            "coverage_gap",
            "docs_drift",
            "schema_drift",
            "workflow_gap",
            "integration_gap",
            "worktree_risk",
            "commit_isolation_gap",
            "artifact_hygiene_gap",
            "runtime_artifact_cleanup_gap",
            "deferred_cleanup_gap",
            "evidence_freshness_gap",
            "autonomy_selection_gap",
        }
    ]
    if not supporting:
        return []
    evidence = [
        {
            "source": "backlog",
            "path": format_path(backlog_file(root), root),
            "summary": "no open backlog items were available before reseeding",
        }
    ]
    for candidate in supporting[:2]:
        evidence.extend(candidate.evidence[:1])
    return [
        BacklogCandidate(
            id="backlog_reseeding_gap-empty-open-backlog",
            title="Reseed the self-improvement backlog from structural evidence",
            category="backlog_reseeding_gap",
            evidence=evidence,
            impact=3,
            likelihood=3,
            confidence=4,
            repair_cost=3,
            recommendation="improve_backlog_reseeding",
            signals=["roadmap_gap"],
        )
    ]


def mixed_surface_coverage_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect evidence that mixed-surface executed benchmark coverage is thin."""
    fixtures_root = root / "benchmarks" / "fixtures"
    evidence: list[dict[str, Any]] = []
    if fixtures_root.is_dir():
        names = {
            path.parent.name
            for path in fixtures_root.glob("*/expected.json")
            if path.parent.name.strip()
        }
        if names:
            has_executed_mixed_surface = any(
                "mixed" in name
                and any(term in name for term in ("fast", "deep", "handoff"))
                for name in names
            )
            if not has_executed_mixed_surface:
                evidence.append(
                    {
                        "source": "benchmark_fixtures",
                        "path": format_path(fixtures_root, root),
                        "summary": (
                            "mixed verification fixtures exist, but no fixture name "
                            "indicates executed mixed fast/deep/handoff coverage"
                        ),
                    }
                )
    evidence.extend(
        matching_report_evidence(
            root,
            sources={"current_state", "roadmap"},
            terms=(
                "mixed-surface executed benchmark expansion",
                "mixed-surface behavior",
                "mixed-language verification coverage exists, but executed mixed-surface",
                "current mixed coverage leans on seeded verification artifacts",
            ),
            summary="report calls out remaining executed mixed-surface benchmark realism work",
        )
    )
    return evidence


def docs_drift_report_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect current-truth drift and sync-audit evidence from reports."""
    return matching_report_evidence(
        root,
        sources={"current_state", "roadmap", "worktree_triage"},
        terms=(
            "current-truth drift risk",
            "current-truth sync audit",
            "current-truth audit",
            "stay in sync with the current command surface",
        ),
        summary="report calls out current-truth drift or an explicit sync audit",
    )


def executor_contract_gap_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for executor contract completeness work."""
    return matching_report_evidence(
        root,
        sources={"current_state", "roadmap"},
        terms=(
            "executor result contract",
            "executor result ingest",
            "ingest and resume workflow",
            "ingest or resume layer",
        ),
        summary="report calls out executor result contract or ingest/resume completeness work",
    )


def integration_gap_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for worktree integration risk."""
    return matching_report_evidence(
        root,
        sources={"worktree_triage", "worktree_commit_plan", "current_state"},
        terms=(
            "dirty worktree",
            "commit split",
            "commit plan",
            "integration caveats",
            "worktree triage",
        ),
        summary="report calls out worktree integration or commit-split risk",
    )


def deferred_cleanup_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for deferred cleanup work."""
    return matching_report_evidence(
        root,
        sources={"worktree_triage", "current_state"},
        terms=(
            "deferred cleanup",
            "defer or ignore",
            "generated runtime artifacts",
            "generated benchmark outputs",
            "deferred generated artifacts",
        ),
        summary="report calls out deferred cleanup work or generated outputs to isolate",
    )


def commit_isolation_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for commit-order isolation risk."""
    matches: list[dict[str, Any]] = []
    lowered_terms = tuple(
        term.lower()
        for term in (
            "commit order dependency",
            "corrected commit sequence",
            "foundation-before-benchmark",
            "commit split",
            "git add -p",
            "alpha closure readiness snapshot",
        )
    )
    for source, path, text in report_documents(root):
        if source not in {"worktree_commit_plan", "current_state"}:
            continue
        lowered = text.lower()
        if any(term in lowered for term in lowered_terms):
            summary = (
                closure_aware_commit_isolation_summary(path, text)
                or "report calls out commit-order dependency or commit-isolation work"
            )
            matches.append(
                {
                    "source": source,
                    "path": format_path(path, root),
                    "summary": summary,
                }
            )
    return matches


def alpha_closure_snapshot_is_present(text: str) -> bool:
    """Return whether a report pins the alpha closure gate snapshot."""
    lowered = text.lower()
    return all(
        term in lowered
        for term in (
            "alpha closure readiness snapshot",
            "latest full local gate pass",
            "split the worktree by this commit plan",
        )
    )


def closure_aware_commit_isolation_summary(path: Path, text: str) -> str | None:
    """Return a precise commit-isolation summary for closure-ready reports."""
    if path.name == "worktree-commit-plan.md" and alpha_closure_snapshot_is_present(
        text
    ):
        return (
            "alpha closure readiness snapshot pins full gate pass and "
            "commit-split action"
        )
    return None


def artifact_hygiene_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for runtime/source artifact separation gaps."""
    return matching_report_evidence(
        root,
        sources={"worktree_triage", "current_state", "roadmap"},
        terms=(
            "runtime artifacts",
            "generated artifact policy",
            "source-like areas",
            "tracked vs generated",
            "generated benchmark outputs",
        ),
        summary="report calls out runtime or generated artifacts mixed with source evidence",
    )


def evidence_freshness_evidence(root: Path) -> list[dict[str, Any]]:
    """Collect report evidence for generated-versus-frozen evidence ambiguity."""
    return matching_report_evidence(
        root,
        sources={"current_state", "worktree_triage", "roadmap"},
        terms=(
            "frozen evidence",
            "runtime result",
            "generated versus frozen",
            "generated vs frozen",
            "benchmark outputs",
        ),
        summary="report calls out ambiguity between runtime results and frozen evidence",
    )


def generated_artifact_policy_is_explicit(live_signals: dict[str, Any]) -> bool:
    """Return whether ignore rules and policy docs cover generated artifacts."""
    return bool(live_signals.get("generated_artifact_policy_explicit"))


def generated_artifact_policy_snapshot(root: Path) -> dict[str, Any]:
    """Return whether generated-artifact ignore and doc policies are present."""
    rules = gitignore_rules(root)
    missing_rules = [
        rule for rule in GENERATED_ARTIFACT_POLICY_RULES if rule not in rules
    ]
    missing_terms = generated_artifact_policy_missing_terms(root)
    ignore_policy_explicit = not missing_rules
    documented_policy_explicit = not missing_terms
    return {
        "generated_artifact_ignore_policy_explicit": ignore_policy_explicit,
        "generated_artifact_documented_policy_explicit": documented_policy_explicit,
        "generated_artifact_policy_explicit": (
            ignore_policy_explicit and documented_policy_explicit
        ),
        "missing_generated_artifact_policy_rules": missing_rules,
        "missing_generated_artifact_policy_terms": missing_terms,
        "generated_artifact_policy_doc_path": str(GENERATED_ARTIFACT_POLICY_DOC),
    }


def generated_artifact_policy_missing_terms(root: Path) -> list[str]:
    """Return missing terms from the generated-versus-frozen policy document."""
    path = root / GENERATED_ARTIFACT_POLICY_DOC
    if not path.is_file():
        return ["generated-vs-frozen evidence policy document is missing"]
    text = " ".join(read_text(path).lower().replace("\\", "/").split())
    return [
        f"policy document missing required term: {term}"
        for term in GENERATED_ARTIFACT_POLICY_TERMS
        if term.lower() not in text
    ]


def generated_artifact_policy_evidence(
    root: Path, live_signals: dict[str, Any]
) -> list[dict[str, Any]]:
    """Render missing generated-artifact policy pieces as inspection evidence."""
    evidence: list[dict[str, Any]] = []
    missing_rules = list_signal_paths(
        live_signals, "missing_generated_artifact_policy_rules"
    )
    if missing_rules:
        evidence.append(
            {
                "source": "generated_artifact_policy",
                "path": ".gitignore",
                "summary": "missing generated-artifact ignore rules: "
                + ", ".join(missing_rules),
            }
        )
    missing_terms = list_signal_paths(
        live_signals, "missing_generated_artifact_policy_terms"
    )
    if missing_terms:
        policy_doc_path = str(
            live_signals.get("generated_artifact_policy_doc_path")
            or GENERATED_ARTIFACT_POLICY_DOC
        )
        evidence.append(
            {
                "source": "generated_artifact_policy",
                "path": format_path(root / policy_doc_path, root),
                "summary": "; ".join(missing_terms),
            }
        )
    return evidence


def gitignore_rules(root: Path) -> set[str]:
    """Return normalized `.gitignore` rules for lightweight policy checks."""
    text = read_text(root / ".gitignore")
    return {
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def collect_live_repository_signals(root: Path) -> dict[str, Any]:
    """Collect live worktree, runtime-artifact, and generated-evidence signals."""
    benchmark_result_paths = [
        format_path(root / relative_path, root)
        for relative_path in BENCHMARK_RESULT_ARTIFACTS
        if (root / relative_path).exists()
    ]
    snapshot = git_worktree_snapshot(root)
    runtime_artifact_paths = [
        path
        for path in list_signal_paths(snapshot, "modified_paths")
        + list_signal_paths(snapshot, "untracked_paths")
        if is_runtime_artifact_path(path)
    ]
    snapshot["runtime_artifact_paths"] = runtime_artifact_paths
    snapshot["benchmark_result_paths"] = benchmark_result_paths
    snapshot.update(generated_artifact_policy_snapshot(root))
    return snapshot


def git_worktree_snapshot(root: Path) -> dict[str, Any]:
    """Return a lightweight git-status snapshot for the current repository."""
    command = ["git", "status", "--short", "--untracked-files=all"]
    try:
        completed = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return empty_live_repository_signals()
    if completed.returncode != 0:
        return empty_live_repository_signals()
    return parse_git_status_output(completed.stdout)


def parse_git_status_output(output: str) -> dict[str, Any]:
    """Parse `git status --short` output into stable count signals."""
    modified_paths: list[str] = []
    untracked_paths: list[str] = []
    staged_count = 0
    for line in output.splitlines():
        if len(line) < 3:
            continue
        status = line[:2]
        path_text = normalize_git_status_path(line[3:].strip())
        if not path_text:
            continue
        if status == "??":
            untracked_paths.append(path_text)
            continue
        if status == "!!":
            continue
        modified_paths.append(path_text)
        if status[0] not in {" ", "?", "!"}:
            staged_count += 1
    return {
        "modified_count": len(modified_paths),
        "untracked_count": len(untracked_paths),
        "staged_count": staged_count,
        "modified_paths": modified_paths,
        "untracked_paths": untracked_paths,
    }


def normalize_git_status_path(path_text: str) -> str:
    """Normalize one git-status path, preferring the destination on renames."""
    if " -> " in path_text:
        return path_text.split(" -> ", maxsplit=1)[1].strip()
    return path_text


def empty_live_repository_signals() -> dict[str, Any]:
    """Return an empty live repository signal snapshot."""
    return {
        "modified_count": 0,
        "untracked_count": 0,
        "staged_count": 0,
        "modified_paths": [],
        "untracked_paths": [],
    }


def list_signal_paths(signals: dict[str, Any], key: str) -> list[str]:
    """Return stable string paths from one live-signal field."""
    value = signals.get(key)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def sample_signal_paths(paths: list[str], limit: int = 3) -> list[str]:
    """Return a stable sample of signal paths for concise evidence text."""
    return sorted({path for path in paths if path.strip()})[:limit]


def classify_worktree_path_area(path_text: str) -> str:
    """Classify a dirty worktree path into a stable repository area."""
    normalized = path_text.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if is_runtime_artifact_path(normalized):
        return "runtime_artifact"
    if normalized.startswith(".github/workflows/"):
        return "workflow"
    if normalized.startswith("src/"):
        return "source"
    if normalized.startswith("tests/"):
        return "tests"
    if normalized == "README.md" or normalized.startswith("docs/"):
        return "docs"
    if normalized.startswith("benchmarks/") or normalized.startswith("benchmark/"):
        return "benchmark"
    if normalized.startswith("examples/"):
        return "examples"
    if normalized.startswith("templates/"):
        return "templates"
    if normalized in {".gitignore", "pyproject.toml", "qa-z.yaml.example"}:
        return "config"
    return "other"


def worktree_area_summary(paths: list[str], *, limit: int = 5) -> str:
    """Return concise dirty-path area counts for worktree triage evidence."""
    counts: dict[str, int] = {}
    for path in paths:
        if not str(path).strip():
            continue
        area = classify_worktree_path_area(str(path))
        counts[area] = counts.get(area, 0) + 1
    if not counts:
        return ""
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{area}:{count}" for area, count in ordered[:limit])


def is_runtime_artifact_path(path_text: str) -> bool:
    """Return whether a path points at local runtime or generated artifact output."""
    normalized = path_text.replace("\\", "/")
    return (
        normalized.startswith(".qa-z/")
        or normalized.startswith("benchmarks/results/")
        or normalized.startswith("benchmarks/results-")
    )


def merge_backlog(
    *, existing: dict[str, Any], candidates: list[BacklogCandidate], now: str
) -> dict[str, Any]:
    """Merge newly observed candidates into a persistent backlog artifact."""
    existing_items = [
        item for item in existing.get("items", []) if isinstance(item, dict)
    ]
    items_by_id = {str(item.get("id")): dict(item) for item in existing_items}
    observed_ids = {candidate.id for candidate in candidates}

    for candidate in candidates:
        previous = items_by_id.get(candidate.id)
        recurrence = int_value(previous.get("recurrence_count")) + 1 if previous else 1
        seen_candidate = replace(candidate, recurrence_count=recurrence)
        item = seen_candidate.to_dict()
        item.update(
            {
                "status": "open",
                "first_seen_at": (
                    str(previous.get("first_seen_at"))
                    if previous and previous.get("first_seen_at")
                    else now
                ),
                "last_seen_at": now,
            }
        )
        items_by_id[candidate.id] = item

    for item_id, item in items_by_id.items():
        if item_id in observed_ids:
            continue
        if str(item.get("status", "open")) != "open":
            continue
        item["status"] = "closed"
        item["closed_at"] = now
        item["closure_reason"] = "not_observed_in_latest_inspection"

    items = sorted(
        items_by_id.values(),
        key=lambda item: (
            0 if str(item.get("status", "open")) in OPEN_STATUSES else 1,
            -int_value(item.get("priority_score")),
            str(item.get("id", "")),
        ),
    )
    return {
        "kind": BACKLOG_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "updated_at": now,
        "items": items,
    }


def render_loop_plan(
    *, loop_id: str, generated_at: str, selected_items: list[dict[str, Any]]
) -> str:
    """Render a concise Markdown plan for the selected self-improvement tasks."""
    lines = [
        "# QA-Z Self-Improvement Loop Plan",
        "",
        f"- Loop id: `{loop_id}`",
        f"- Generated at: `{generated_at}`",
        "- Boundary: QA-Z selects evidence-backed work; an external executor edits code.",
        "- This plan does not call Codex or Claude APIs, schedule jobs, or repair code by itself.",
        "",
        "## Selected Tasks",
        "",
    ]
    if not selected_items:
        lines.append("- No open backlog tasks were selected.")
    for index, item in enumerate(selected_items, start=1):
        lines.extend(
            [
                f"{index}. {item.get('title', item.get('id', 'untitled'))}",
                f"   - id: `{item.get('id', '')}`",
                f"   - category: `{item.get('category', '')}`",
                f"   - recommendation: `{item.get('recommendation', '')}`",
                f"   - action: {selected_task_action_hint(item)}",
                f"   - validation: `{selected_task_validation_command(item)}`",
                f"   - priority score: {item.get('priority_score', 0)}",
            ]
        )
        if item.get("selection_priority_score") is not None:
            lines.append(
                f"   - selection score: {item.get('selection_priority_score', 0)}"
            )
        selection_penalty = item.get("selection_penalty")
        penalty_reasons = [
            str(reason)
            for reason in item.get("selection_penalty_reasons", [])
            if isinstance(reason, str) and reason.strip()
        ]
        if selection_penalty:
            if penalty_reasons:
                lines.append(
                    "   - selection penalty: "
                    f"{selection_penalty} "
                    f"({', '.join(f'`{reason}`' for reason in penalty_reasons)})"
                )
            else:
                lines.append(f"   - selection penalty: {selection_penalty}")
        lines.append("   - evidence:")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            lines.append("     - none recorded")
        else:
            for entry in evidence:
                if not isinstance(entry, dict):
                    continue
                lines.append(
                    "     - "
                    f"{entry.get('source', 'artifact')}: "
                    f"`{entry.get('path', 'unknown')}` "
                    f"{entry.get('summary', '')}".rstrip()
                )
        lines.append("")
    lines.extend(
        [
            "## Verification After External Repair",
            "",
            "- Run deterministic QA-Z verification commands that match the selected task evidence.",
            "- Feed the resulting verify, benchmark, or session artifacts into the next self-inspection loop.",
        ]
    )
    return "\n".join(lines).strip() + "\n"


def apply_selection_penalty(
    item: dict[str, Any],
    *,
    recent_entries: list[dict[str, Any]],
    open_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Attach a light reselection penalty using recent loop history."""
    enriched = dict(item)
    penalty, reasons = selection_penalty_for_item(
        item=item,
        recent_entries=recent_entries,
        open_items=open_items,
    )
    enriched["selection_penalty"] = penalty
    enriched["selection_penalty_reasons"] = reasons
    enriched["selection_priority_score"] = max(
        int_value(item.get("priority_score")) - penalty,
        0,
    )
    return enriched


def select_items_with_batch_diversity(
    *, scored_items: list[dict[str, Any]], count: int
) -> list[dict[str, Any]]:
    """Select tasks greedily while lightly diversifying fallback families."""
    remaining = [dict(item) for item in scored_items]
    selected: list[dict[str, Any]] = []
    while remaining and len(selected) < count:
        rescored = [
            apply_intra_selection_penalty(
                item,
                selected_items=selected,
                remaining_items=remaining,
            )
            for item in remaining
        ]
        chosen = sorted(
            rescored,
            key=lambda item: (
                -int_value(
                    item.get("selection_priority_score", item.get("priority_score"))
                ),
                int_value(item.get("selection_penalty")),
                str(item.get("category", "")),
                str(item.get("id", "")),
            ),
        )[0]
        selected.append(chosen)
        chosen_id = str(chosen.get("id") or "")
        remaining = [
            item for item in remaining if str(item.get("id") or "") != chosen_id
        ]
    return selected


def apply_intra_selection_penalty(
    item: dict[str, Any],
    *,
    selected_items: list[dict[str, Any]],
    remaining_items: list[dict[str, Any]],
) -> dict[str, Any]:
    """Apply a light within-batch family penalty when alternatives exist."""
    enriched = dict(item)
    if not selected_items:
        return enriched
    family = fallback_family_for_category(str(item.get("category") or ""))
    if not family:
        return enriched
    selected_families = set(fallback_families_for_items(selected_items))
    alternative_families = {
        other_family
        for other in remaining_items
        if str(other.get("id") or "") != str(item.get("id") or "")
        if (
            other_family := fallback_family_for_category(
                str(other.get("category") or "")
            )
        )
        if other_family != family
    }
    if family not in selected_families or not alternative_families:
        return enriched
    base_penalty = int_value(enriched.get("selection_penalty"))
    reasons = [
        str(reason)
        for reason in enriched.get("selection_penalty_reasons", [])
        if str(reason).strip()
    ]
    reasons.append("current_batch_fallback_family_reselected")
    enriched["selection_penalty"] = base_penalty + INTRA_SELECTION_FAMILY_PENALTY
    enriched["selection_penalty_reasons"] = reasons
    enriched["selection_priority_score"] = max(
        int_value(
            enriched.get("selection_priority_score", enriched.get("priority_score"))
        )
        - INTRA_SELECTION_FAMILY_PENALTY,
        0,
    )
    return enriched


def selection_penalty_for_item(
    *,
    item: dict[str, Any],
    recent_entries: list[dict[str, Any]],
    open_items: list[dict[str, Any]],
) -> tuple[int, list[str]]:
    """Return a deterministic diversity penalty for immediate reselection."""
    if len(recent_entries) < RECENT_SELECTION_WINDOW:
        return 0, []
    item_id = str(item.get("id") or "")
    category = str(item.get("category") or "")
    fallback_family = fallback_family_for_category(category)
    available_fallback_families = {
        family
        for open_item in open_items
        if (
            family := fallback_family_for_category(str(open_item.get("category") or ""))
        )
    }
    penalty = 0
    reasons: list[str] = []
    if item_id and all(item_id in selected_task_ids(entry) for entry in recent_entries):
        penalty += 2
        reasons.append("recent_task_reselected")
    if category and all(
        category in selected_task_categories(entry, open_items=open_items)
        for entry in recent_entries
    ):
        penalty += 1
        reasons.append("recent_category_reselected")
    if (
        fallback_family
        and len(available_fallback_families) > 1
        and all(
            fallback_family
            in selected_task_fallback_families(entry, open_items=open_items)
            for entry in recent_entries
        )
    ):
        penalty += 2
        reasons.append("recent_fallback_family_reselected")
    return penalty, reasons


def fallback_family_for_category(category: str) -> str | None:
    """Return the fallback family for one backlog category, when applicable."""
    return FALLBACK_FAMILY_BY_CATEGORY.get(category.strip())


def selected_task_ids(entry: dict[str, Any]) -> set[str]:
    """Return selected task ids from one loop-history entry."""
    selected_tasks = entry.get("selected_tasks")
    if not isinstance(selected_tasks, list):
        return set()
    return {str(item) for item in selected_tasks if str(item).strip()}


def selected_task_categories(
    entry: dict[str, Any], *, open_items: list[dict[str, Any]]
) -> set[str]:
    """Return selected categories from history, deriving them when needed."""
    selected_categories = entry.get("selected_categories")
    if isinstance(selected_categories, list):
        return {str(item) for item in selected_categories if str(item).strip()}
    categories_by_id = {
        str(item.get("id")): str(item.get("category") or "")
        for item in open_items
        if isinstance(item, dict) and item.get("id")
    }
    return {
        categories_by_id[item_id]
        for item_id in selected_task_ids(entry)
        if categories_by_id.get(item_id)
    }


def selected_task_fallback_families(
    entry: dict[str, Any], *, open_items: list[dict[str, Any]]
) -> set[str]:
    """Return selected fallback families from history, deriving them when needed."""
    selected_fallback_families = entry.get("selected_fallback_families")
    if isinstance(selected_fallback_families, list):
        return {str(item) for item in selected_fallback_families if str(item).strip()}
    return {
        family
        for category in selected_task_categories(entry, open_items=open_items)
        if (family := fallback_family_for_category(category))
    }


def fallback_families_for_items(items: list[dict[str, Any]]) -> list[str]:
    """Return stable fallback families represented by selected backlog items."""
    return sorted(
        {
            family
            for item in items
            if (family := fallback_family_for_category(str(item.get("category") or "")))
        }
    )


def append_history(
    history_path: Path,
    *,
    loop_id: str,
    generated_at: str,
    selected_items: list[dict[str, Any]],
    open_items: list[dict[str, Any]],
) -> None:
    """Append one JSONL loop-memory record."""
    history_path.parent.mkdir(parents=True, exist_ok=True)
    selected_ids = [str(item.get("id")) for item in selected_items]
    selected_id_set = set(selected_ids)
    entry = {
        "kind": LOOP_HISTORY_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "loop_id": loop_id,
        "created_at": generated_at,
        "selected_tasks": selected_ids,
        "selected_categories": [
            str(item.get("category") or "")
            for item in selected_items
            if str(item.get("category") or "").strip()
        ],
        "selected_fallback_families": fallback_families_for_items(selected_items),
        "evidence_used": evidence_paths(selected_items),
        "resulting_session_id": None,
        "verify_verdict": None,
        "benchmark_delta": None,
        "next_candidates": [
            str(item.get("id"))
            for item in sorted(
                open_items,
                key=lambda item: (
                    -int_value(
                        item.get("selection_priority_score", item.get("priority_score"))
                    ),
                    int_value(item.get("selection_penalty")),
                    str(item.get("id", "")),
                ),
            )
            if str(item.get("id")) not in selected_id_set
        ],
    }
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, sort_keys=True) + "\n")


def benchmark_summaries(root: Path) -> list[tuple[Path, dict[str, Any]]]:
    """Return known benchmark summary artifacts."""
    candidates = [root / "benchmarks" / "results" / "summary.json"]
    results: list[tuple[Path, dict[str, Any]]] = []
    for path in candidates:
        if not path.is_file():
            continue
        summary = read_json_object(path)
        if summary.get("kind") == "qa_z.benchmark_summary":
            results.append((path, summary))
    return results


def evidence_sources(candidates: list[BacklogCandidate]) -> list[dict[str, str]]:
    """Return unique artifact sources used by candidates."""
    sources: dict[tuple[str, str], dict[str, str]] = {}
    for candidate in candidates:
        for entry in candidate.evidence:
            source = str(entry.get("source") or "artifact")
            path = str(entry.get("path") or "")
            if not path:
                continue
            sources[(source, path)] = {"source": source, "path": path}
    return [sources[key] for key in sorted(sources)]


def evidence_paths(items: list[dict[str, Any]]) -> list[str]:
    """Return unique evidence paths from backlog items."""
    paths: set[str] = set()
    for item in items:
        evidence = item.get("evidence")
        if not isinstance(evidence, list):
            continue
        for entry in evidence:
            if isinstance(entry, dict) and entry.get("path"):
                paths.add(str(entry["path"]))
    return sorted(paths)


def compact_backlog_evidence_summary(item: dict[str, Any]) -> str:
    """Return one compact evidence summary for a backlog item."""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return "none recorded"
    entry = compact_evidence_entry(evidence)
    if entry is None:
        return "none recorded"
    source = str(entry.get("source") or "artifact").strip() or "artifact"
    summary = str(entry.get("summary") or "").strip()
    path = str(entry.get("path") or "").strip()
    if summary:
        compact_summary = f"{source}: {summary}"
        basis = compact_action_basis(item, compact_summary)
        if basis:
            return f"{compact_summary}; action basis: {basis}"
        return compact_summary
    if path:
        compact_summary = f"{source}: {path}"
        basis = compact_action_basis(item, compact_summary)
        if basis:
            return f"{compact_summary}; action basis: {basis}"
        return compact_summary
    return "none recorded"


def compact_action_basis(item: dict[str, Any], primary_summary: str) -> str:
    """Return secondary evidence that explains specialized action hints."""
    area_basis = compact_area_action_basis(item, primary_summary)
    if area_basis:
        return area_basis
    return compact_generated_action_basis(item, primary_summary)


def compact_area_action_basis(item: dict[str, Any], primary_summary: str) -> str:
    """Return secondary area evidence that explains area-aware action hints."""
    if "areas=" in primary_summary:
        return ""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return ""
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        summary = str(entry.get("summary") or "").strip()
        if "areas=" not in summary:
            continue
        source = str(entry.get("source") or "artifact").strip() or "artifact"
        return f"{source}: {summary}"
    return ""


def compact_generated_action_basis(
    item: dict[str, Any],
    primary_summary: str,
) -> str:
    """Return generated artifact evidence behind deferred cleanup actions."""
    recommendation = str(item.get("recommendation") or "").strip()
    if recommendation != "triage_and_isolate_changes":
        return ""
    if (
        "generated_outputs:" in primary_summary
        or "runtime_artifacts:" in primary_summary
    ):
        return ""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return ""
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        source = str(entry.get("source") or "artifact").strip() or "artifact"
        if source not in {"generated_outputs", "runtime_artifacts"}:
            continue
        summary = str(entry.get("summary") or "").strip()
        path = str(entry.get("path") or "").strip()
        if summary:
            return f"{source}: {summary}"
        if path:
            return f"{source}: {path}"
    return ""


def selected_task_action_hint(item: dict[str, Any]) -> str:
    """Return a deterministic first action hint for a selected task."""
    recommendation = str(item.get("recommendation") or "").strip()
    if recommendation == "reduce_integration_risk":
        area_phrase = join_action_areas(worktree_action_areas(item))
        if area_phrase:
            return (
                f"triage {area_phrase} changes first, separate generated artifacts, "
                "then rerun self-inspection"
            )
    if recommendation == "isolate_foundation_commit":
        area_phrase = join_action_areas(worktree_action_areas(item))
        if area_phrase:
            return (
                "follow docs/reports/worktree-commit-plan.md and isolate "
                f"{area_phrase} changes into the foundation split, "
                "then rerun self-inspection"
            )
    hints = {
        "reduce_integration_risk": (
            "inspect the dirty worktree and separate generated artifacts, "
            "then rerun self-inspection"
        ),
        "triage_and_isolate_changes": (
            "decide whether generated artifacts stay local-only or become intentional "
            "frozen evidence, separate them from source changes, then rerun "
            "self-inspection"
        ),
        "isolate_foundation_commit": (
            "follow docs/reports/worktree-commit-plan.md to split the foundation "
            "commit, then rerun self-inspection"
        ),
        "audit_worktree_integration": (
            "inspect current-state, triage, and commit-plan reports, then rerun "
            "self-inspection"
        ),
    }
    if recommendation in hints:
        return hints[recommendation]
    if recommendation:
        return f"turn {recommendation.replace('_', ' ')} into a scoped repair plan"
    return "turn selected evidence into a scoped repair plan"


def selected_task_validation_command(item: dict[str, Any]) -> str:
    """Return the deterministic command for refreshing evidence after a task."""
    recommendation = str(item.get("recommendation") or "").strip()
    commands = {
        "add_benchmark_fixture": "python -m qa_z benchmark --json",
        "reduce_integration_risk": "python -m qa_z self-inspect",
        "isolate_foundation_commit": "python -m qa_z self-inspect",
        "audit_worktree_integration": "python -m qa_z self-inspect",
        "improve_fallback_diversity": "python -m qa_z autonomy --loops 1",
        "stabilize_verification_surface": (
            "python -m qa_z verify --baseline-run <baseline> "
            "--candidate-run <candidate>"
        ),
        "create_repair_session": (
            "python -m qa_z repair-session status --session <session>"
        ),
    }
    return commands.get(recommendation, "python -m qa_z self-inspect")


def worktree_action_areas(item: dict[str, Any]) -> list[str]:
    """Return ordered dirty worktree areas from compact evidence summaries."""
    evidence = item.get("evidence")
    if not isinstance(evidence, list):
        return []
    for entry in evidence:
        if not isinstance(entry, dict):
            continue
        summary = str(entry.get("summary") or "")
        marker = "areas="
        if marker not in summary:
            continue
        area_segment = summary.split(marker, maxsplit=1)[1].split(";", maxsplit=1)[0]
        areas: list[str] = []
        for pair in area_segment.split(","):
            if ":" not in pair:
                continue
            name = pair.strip().split(":", maxsplit=1)[0].strip()
            if name:
                areas.append(name)
        return areas
    return []


def join_action_areas(areas: list[str], *, limit: int = 2) -> str:
    """Join the first dirty worktree areas for a concise action hint."""
    selected = [area for area in areas if area.strip()][:limit]
    if not selected:
        return ""
    if len(selected) == 1:
        return selected[0]
    return " and ".join(selected)


def compact_evidence_entry(evidence: list[Any]) -> dict[str, Any] | None:
    """Pick the best evidence entry for one-line human summaries."""
    entries = [entry for entry in evidence if isinstance(entry, dict)]
    if not entries:
        return None
    return sorted(
        enumerate(entries),
        key=lambda pair: (compact_evidence_priority(pair[1]), pair[0]),
    )[0][1]


def compact_evidence_priority(entry: dict[str, Any]) -> int:
    """Return a lower priority value for more useful compact evidence."""
    summary = str(entry.get("summary") or "").lower()
    if "alpha closure readiness snapshot" in summary:
        return 0
    return 1


def matching_report_evidence(
    root: Path,
    *,
    sources: set[str],
    terms: tuple[str, ...],
    summary: str,
) -> list[dict[str, Any]]:
    """Collect report evidence that matches any of the given terms."""
    matches: list[dict[str, Any]] = []
    lowered_terms = tuple(term.lower() for term in terms)
    for source, path, text in report_documents(root):
        if source not in sources:
            continue
        lowered = text.lower()
        if any(term in lowered for term in lowered_terms):
            matches.append(
                {
                    "source": source,
                    "path": format_path(path, root),
                    "summary": summary,
                }
            )
    return matches


def report_documents(root: Path) -> list[tuple[str, Path, str]]:
    """Return known report documents that can seed structural candidates."""
    documents: list[tuple[str, Path, str]] = []
    for source, relative_path in REPORT_EVIDENCE_FILES.items():
        path = root / relative_path
        text = read_text(path)
        if text:
            documents.append((source, path, text))
    return documents


def load_history_entries(path: Path) -> list[dict[str, Any]]:
    """Read loop history JSONL entries."""
    if not path.is_file():
        return []
    entries: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("kind") == LOOP_HISTORY_KIND:
            entries.append(data)
    return entries


def is_empty_loop_entry(entry: dict[str, Any]) -> bool:
    """Return whether a history entry represents an empty loop."""
    selected_tasks = entry.get("selected_tasks")
    if isinstance(selected_tasks, list) and selected_tasks:
        return False
    state = str(entry.get("state") or "")
    return state in {"blocked_no_candidates", "completed", "fallback_selected", ""}


def unique_candidates(candidates: list[BacklogCandidate]) -> list[BacklogCandidate]:
    """Deduplicate candidates by stable id."""
    by_id: dict[str, BacklogCandidate] = {}
    for candidate in candidates:
        by_id.setdefault(candidate.id, candidate)
    return [by_id[key] for key in sorted(by_id)]


def empty_backlog() -> dict[str, Any]:
    """Return an empty backlog object."""
    return {
        "kind": BACKLOG_KIND,
        "schema_version": SELF_IMPROVEMENT_SCHEMA_VERSION,
        "updated_at": None,
        "items": [],
    }


def backlog_file(root: Path) -> Path:
    """Return the default improvement backlog path."""
    return root / ".qa-z" / "improvement" / "backlog.json"


def open_backlog_items(backlog: dict[str, Any]) -> list[dict[str, Any]]:
    """Return open backlog items from a backlog artifact."""
    return [
        item
        for item in backlog.get("items", [])
        if isinstance(item, dict) and str(item.get("status", "open")) in OPEN_STATUSES
    ]


def resolve_optional_artifact_path(root: Path, value: str) -> Path | None:
    """Resolve an optional artifact path relative to the repository root."""
    text = value.strip()
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON object artifact."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_json_object(path: Path) -> dict[str, Any]:
    """Read a JSON object, returning an empty mapping for optional bad artifacts."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def read_text(path: Path) -> str:
    """Read text for optional documentation checks."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def slugify(value: str) -> str:
    """Create a stable id fragment from human text."""
    slug = re.sub(r"[^A-Za-z0-9_]+", "-", value.strip().lower()).strip("-")
    return slug or "unknown"


def int_value(value: object) -> int:
    """Return an integer value, or zero when absent or invalid."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0


def utc_now() -> str:
    """Return a stable UTC timestamp."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def default_loop_id(prefix: str, generated_at: str) -> str:
    """Build a compact loop id from a timestamp."""
    compact = generated_at.replace("-", "").replace(":", "").replace("T", "-")
    compact = compact.removesuffix("Z")
    return f"{prefix}-{compact}"
