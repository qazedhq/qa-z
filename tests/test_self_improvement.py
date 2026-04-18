"""Tests for QA-Z self-inspection and improvement backlog planning."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.cli import main
from qa_z.self_improvement import (
    BacklogCandidate,
    classify_worktree_path_area,
    collect_live_repository_signals,
    compact_backlog_evidence_summary,
    is_runtime_artifact_path,
    render_loop_plan,
    run_self_inspection,
    score_candidate,
    select_next_tasks,
    selected_task_action_hint,
    selected_task_validation_command,
    worktree_action_areas,
)


NOW = "2026-04-15T00:00:00Z"


def write_json(path: Path, payload: dict[str, object]) -> None:
    """Write a deterministic JSON object fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_report(root: Path, name: str, body: str) -> None:
    """Write a deterministic docs/report fixture."""
    path = root / "docs" / "reports" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.strip() + "\n", encoding="utf-8")


def write_gitignore(root: Path, lines: list[str]) -> None:
    """Write a deterministic `.gitignore` fixture."""
    (root / ".gitignore").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_generated_evidence_policy(root: Path) -> None:
    """Write the generated-versus-frozen evidence policy fixture."""
    path = root / "docs" / "generated-vs-frozen-evidence-policy.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """
        # Generated Versus Frozen Evidence Policy

        Root `.qa-z/**` artifacts are local runtime state.
        `benchmarks/results/work/**` is disposable benchmark scratch output.
        `benchmarks/results/summary.json` and `benchmarks/results/report.md`
        are local by default and may be committed only as intentional frozen
        evidence with surrounding documentation.
        `benchmarks/fixtures/**/repo/.qa-z/**` is allowed as fixture-local
        deterministic benchmark input.
        """.strip()
        + "\n",
        encoding="utf-8",
    )


def write_loop_history(root: Path, entries: list[dict[str, object]]) -> None:
    """Write deterministic loop history entries."""
    path = root / ".qa-z" / "loops" / "history.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(entry, sort_keys=True) for entry in entries) + "\n",
        encoding="utf-8",
    )


def write_benchmark_summary(root: Path) -> None:
    """Seed a benchmark summary with one failed fixture."""
    write_json(
        root / "benchmarks" / "results" / "summary.json",
        {
            "kind": "qa_z.benchmark_summary",
            "schema_version": 1,
            "fixtures_total": 2,
            "fixtures_passed": 1,
            "fixtures_failed": 1,
            "overall_rate": 0.5,
            "snapshot": "1/2 fixtures, overall_rate 0.5",
            "failed_fixtures": ["py_type_error"],
            "category_rates": {
                "detection": {"passed": 1, "total": 2, "rate": 0.5},
                "handoff": {"passed": 1, "total": 1, "rate": 1.0},
                "verify": {"passed": 0, "total": 0, "rate": 0.0},
                "artifact": {"passed": 0, "total": 0, "rate": 0.0},
                "policy": {"passed": 0, "total": 0, "rate": 0.0},
            },
            "fixtures": [
                {
                    "name": "py_type_error",
                    "passed": False,
                    "failures": ["fast.failed_checks missing expected values: py_type"],
                    "categories": {
                        "detection": False,
                        "handoff": True,
                        "verify": None,
                        "artifact": None,
                    },
                    "actual": {},
                    "artifacts": {"fast_summary": "work/py_type_error/summary.json"},
                }
            ],
        },
    )


def write_legacy_benchmark_summary_without_snapshot(root: Path) -> None:
    """Seed a legacy benchmark summary that predates the snapshot field."""
    write_benchmark_summary(root)
    path = root / "benchmarks" / "results" / "summary.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("snapshot", None)
    write_json(path, payload)


def write_aggregate_only_failed_benchmark_summary(root: Path) -> None:
    """Seed a failed benchmark summary without per-fixture failure details."""
    write_benchmark_summary(root)
    path = root / "benchmarks" / "results" / "summary.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload.pop("fixtures", None)
    payload.pop("failed_fixtures", None)
    write_json(path, payload)


def write_regressed_verify_summary(root: Path) -> None:
    """Seed a verification summary with a regression verdict."""
    write_json(
        root / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json",
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "repair_improved": False,
            "verdict": "regressed",
            "blocking_before": 0,
            "blocking_after": 1,
            "resolved_count": 0,
            "new_issue_count": 1,
            "regression_count": 1,
            "not_comparable_count": 0,
        },
    )


def write_incomplete_session(root: Path) -> None:
    """Seed a repair session that still needs an external executor."""
    write_json(
        root / ".qa-z" / "sessions" / "session-one" / "session.json",
        {
            "kind": "qa_z.repair_session",
            "schema_version": 1,
            "session_id": "session-one",
            "session_dir": ".qa-z/sessions/session-one",
            "state": "waiting_for_external_repair",
            "created_at": "2026-04-14T00:00:00Z",
            "updated_at": "2026-04-14T00:00:00Z",
            "baseline_run_dir": ".qa-z/runs/baseline",
            "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
            "handoff_dir": ".qa-z/sessions/session-one/handoff",
            "handoff_artifacts": {},
            "executor_guide_path": ".qa-z/sessions/session-one/executor_guide.md",
            "candidate_run_dir": None,
            "verify_dir": None,
            "verify_artifacts": {},
            "outcome_path": None,
            "summary_path": None,
            "provenance": {"repair_needed": True},
        },
    )


def write_executor_result_session(
    root: Path,
    *,
    session_id: str,
    state: str,
    result_status: str,
    validation_status: str,
    verification_hint: str,
) -> None:
    """Seed a repair session with a stored executor result artifact."""
    session_dir = root / ".qa-z" / "sessions" / session_id
    write_json(
        session_dir / "executor_result.json",
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": f"bridge-{session_id}",
            "source_session_id": session_id,
            "source_loop_id": None,
            "created_at": NOW,
            "status": result_status,
            "summary": f"{result_status} executor result for {session_id}",
            "verification_hint": verification_hint,
            "candidate_run_dir": None,
            "changed_files": [],
            "validation": {
                "status": validation_status,
                "commands": [["python", "-m", "pytest"]],
                "results": [],
            },
            "notes": [],
        },
    )
    write_json(
        session_dir / "session.json",
        {
            "kind": "qa_z.repair_session",
            "schema_version": 1,
            "session_id": session_id,
            "session_dir": f".qa-z/sessions/{session_id}",
            "state": state,
            "created_at": NOW,
            "updated_at": NOW,
            "baseline_run_dir": ".qa-z/runs/baseline",
            "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
            "handoff_dir": f".qa-z/sessions/{session_id}/handoff",
            "handoff_artifacts": {},
            "executor_guide_path": f".qa-z/sessions/{session_id}/executor_guide.md",
            "candidate_run_dir": None,
            "verify_dir": None,
            "verify_artifacts": {},
            "outcome_path": None,
            "summary_path": None,
            "provenance": {"repair_needed": True},
            "executor_result_path": f".qa-z/sessions/{session_id}/executor_result.json",
            "executor_result_status": result_status,
            "executor_result_validation_status": validation_status,
            "executor_result_bridge_id": f"bridge-{session_id}",
        },
    )


def write_executor_ingest_record(
    root: Path,
    *,
    record_id: str,
    ingest_status: str,
    result_status: str,
    verify_resume_status: str,
    backlog_implications: list[dict[str, object]],
) -> None:
    """Seed an executor ingest artifact with structural backlog implications."""
    write_json(
        root / ".qa-z" / "executor-results" / record_id / "ingest.json",
        {
            "kind": "qa_z.executor_result_ingest",
            "schema_version": 1,
            "result_id": record_id,
            "bridge_id": f"bridge-{record_id}",
            "session_id": None,
            "result_status": result_status,
            "ingest_status": ingest_status,
            "verify_resume_status": verify_resume_status,
            "warnings": [],
            "freshness_check": {"status": "passed", "details": []},
            "provenance_check": {"status": "passed", "details": []},
            "verification_hint": "skip",
            "verification_triggered": False,
            "verification_verdict": None,
            "verify_summary_path": None,
            "stored_result_path": None,
            "session_state": None,
            "backlog_implications": backlog_implications,
            "next_recommendation": "inspect ingest outcome",
        },
    )


def write_executor_result_history(
    root: Path,
    *,
    session_id: str,
    attempts: list[dict[str, object]],
) -> None:
    """Seed a session-scoped executor-result history artifact."""
    write_json(
        root / ".qa-z" / "sessions" / session_id / "executor_results" / "history.json",
        {
            "kind": "qa_z.executor_result_history",
            "schema_version": 1,
            "session_id": session_id,
            "updated_at": NOW,
            "attempt_count": len(attempts),
            "latest_attempt_id": attempts[-1]["attempt_id"] if attempts else None,
            "attempts": attempts,
        },
    )


def write_executor_dry_run_summary(
    root: Path,
    *,
    session_id: str,
    verdict: str,
    verdict_reason: str,
    history_signals: list[str],
    next_recommendation: str,
    latest_result_status: str,
    latest_ingest_status: str,
    rule_status_counts: dict[str, int] | None = None,
) -> None:
    """Seed a session-scoped executor dry-run summary artifact."""
    write_json(
        root
        / ".qa-z"
        / "sessions"
        / session_id
        / "executor_results"
        / "dry_run_summary.json",
        {
            "kind": "qa_z.executor_result_dry_run",
            "schema_version": 1,
            "session_id": session_id,
            "history_path": f".qa-z/sessions/{session_id}/executor_results/history.json",
            "safety_package_id": "qa_z.executor_safety.v1",
            "evaluated_attempt_count": 1,
            "latest_attempt_id": "attempt-one",
            "latest_result_status": latest_result_status,
            "latest_ingest_status": latest_ingest_status,
            "verdict": verdict,
            "verdict_reason": verdict_reason,
            "history_signals": history_signals,
            "rule_status_counts": rule_status_counts
            or {"attention": 0, "blocked": 0, "clear": 6},
            "rule_evaluations": [],
            "next_recommendation": next_recommendation,
            "report_path": f".qa-z/sessions/{session_id}/executor_results/dry_run_report.md",
        },
    )


def write_fixture_index(root: Path, names: list[str]) -> None:
    """Seed benchmark fixture expected.json files with the given names."""
    for name in names:
        write_json(
            root / "benchmarks" / "fixtures" / name / "expected.json",
            {"name": name, "run": {"fast": True}, "expect_fast": {"status": "failed"}},
        )


def stub_live_repository_signals(monkeypatch, **signals: object) -> None:
    """Patch live repository signal collection for deterministic tests."""

    def fake_signals(_root: Path) -> dict[str, object]:
        return dict(signals)

    monkeypatch.setattr(
        "qa_z.self_improvement.collect_live_repository_signals",
        fake_signals,
    )


def test_score_candidate_uses_formula_and_grounded_bonuses() -> None:
    candidate = BacklogCandidate(
        id="verify_regression-candidate",
        title="Stabilize regressed verification verdict",
        category="verify_regression",
        evidence=[
            {
                "source": "verification",
                "path": ".qa-z/runs/candidate/verify/summary.json",
                "summary": "verdict=regressed",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=3,
        repair_cost=5,
        recommendation="stabilize_verification_surface",
        signals=["verify_regressed", "regression_prevention"],
        recurrence_count=2,
    )

    score = score_candidate(candidate)

    assert score == 47


def test_classify_worktree_path_area_uses_stable_repository_buckets() -> None:
    assert classify_worktree_path_area(".github/workflows/ci.yml") == "workflow"
    assert classify_worktree_path_area("src/qa_z/cli.py") == "source"
    assert classify_worktree_path_area("tests/test_cli.py") == "tests"
    assert (
        classify_worktree_path_area("docs/reports/current-state-analysis.md") == "docs"
    )
    assert classify_worktree_path_area("README.md") == "docs"
    assert (
        classify_worktree_path_area("benchmarks/fixtures/example/expected.json")
        == "benchmark"
    )
    assert classify_worktree_path_area("benchmark/README.md") == "benchmark"
    assert classify_worktree_path_area("examples/fastapi-demo/README.md") == "examples"
    assert classify_worktree_path_area("templates/AGENTS.md") == "templates"
    assert classify_worktree_path_area("pyproject.toml") == "config"
    assert (
        classify_worktree_path_area(".qa-z/loops/latest/outcome.json")
        == "runtime_artifact"
    )
    assert classify_worktree_path_area("scripts/local-tool.py") == "other"


def test_self_inspection_writes_report_and_updates_backlog(tmp_path: Path) -> None:
    write_benchmark_summary(tmp_path)
    write_regressed_verify_summary(tmp_path)
    write_incomplete_session(tmp_path)
    write_fixture_index(tmp_path, ["py_type_error"])

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="loop-one")

    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))

    assert paths.self_inspection_path == (
        tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json"
    )
    assert report["kind"] == "qa_z.self_inspection"
    assert report["loop_id"] == "loop-one"
    assert {
        "benchmark_gap",
        "verify_regression",
        "session_gap",
        "coverage_gap",
    } <= {candidate["category"] for candidate in report["candidates"]}
    assert backlog["kind"] == "qa_z.improvement_backlog"
    assert backlog["updated_at"] == NOW
    assert all(item["status"] == "open" for item in backlog["items"])
    assert all(item["evidence"] for item in backlog["items"])
    assert all(isinstance(item["priority_score"], int) for item in backlog["items"])
    benchmark_item = next(
        item for item in backlog["items"] if item["id"] == "benchmark_gap-py_type_error"
    )
    assert (
        "snapshot=1/2 fixtures, overall_rate 0.5"
        in (benchmark_item["evidence"][0]["summary"])
    )
    assert compact_backlog_evidence_summary(benchmark_item).startswith(
        "benchmark: snapshot=1/2 fixtures, overall_rate 0.5; fixture=py_type_error"
    )


def test_self_inspection_synthesizes_snapshot_for_legacy_benchmark_summary(
    tmp_path: Path,
) -> None:
    write_legacy_benchmark_summary_without_snapshot(tmp_path)
    write_fixture_index(tmp_path, ["py_type_error"])

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="legacy-benchmark-loop")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    benchmark_item = next(
        item for item in backlog["items"] if item["id"] == "benchmark_gap-py_type_error"
    )

    assert (
        "snapshot=1/2 fixtures, overall_rate 0.5"
        in (benchmark_item["evidence"][0]["summary"])
    )


def test_self_inspection_creates_summary_candidate_for_aggregate_benchmark_failure(
    tmp_path: Path,
) -> None:
    write_aggregate_only_failed_benchmark_summary(tmp_path)

    paths = run_self_inspection(
        root=tmp_path, now=NOW, loop_id="aggregate-benchmark-loop"
    )
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    benchmark_item = next(
        item for item in backlog["items"] if item["id"] == "benchmark_gap-summary"
    )

    assert (
        "snapshot=1/2 fixtures, overall_rate 0.5"
        in (benchmark_item["evidence"][0]["summary"])
    )
    assert (
        "benchmark summary reports 1 failed fixture without fixture details"
        in (benchmark_item["evidence"][0]["summary"])
    )


def test_self_inspection_preserves_recurrence_from_existing_backlog(
    tmp_path: Path,
) -> None:
    write_benchmark_summary(tmp_path)
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-14T00:00:00Z",
            "items": [
                {
                    "id": "benchmark_gap-py_type_error",
                    "title": "Fix benchmark fixture failure: py_type_error",
                    "category": "benchmark_gap",
                    "evidence": [{"source": "benchmark"}],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 62,
                    "status": "open",
                    "recommendation": "add_benchmark_fixture",
                    "signals": ["benchmark_fail"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                }
            ],
        },
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="loop-two")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    benchmark_item = next(
        item for item in backlog["items"] if item["id"] == "benchmark_gap-py_type_error"
    )

    assert benchmark_item["first_seen_at"] == "2026-04-14T00:00:00Z"
    assert benchmark_item["last_seen_at"] == NOW
    assert benchmark_item["recurrence_count"] == 2
    assert benchmark_item["priority_score"] == 63


def test_self_inspection_with_no_evidence_writes_empty_artifacts(
    tmp_path: Path,
) -> None:
    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="empty-loop")

    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))

    assert report["candidates"] == []
    assert report["evidence_sources"] == []
    assert backlog["items"] == []


def test_self_inspection_closes_stale_open_backlog_items_not_reobserved(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-14T00:00:00Z",
            "items": [
                {
                    "id": "artifact_hygiene_gap-runtime-source-separation",
                    "title": "Separate runtime artifacts from source-tracked evidence",
                    "category": "artifact_hygiene_gap",
                    "evidence": [
                        {
                            "source": "roadmap",
                            "path": "docs/reports/next-improvement-roadmap.md",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 63,
                    "status": "open",
                    "recommendation": "separate_runtime_from_source_artifacts",
                    "signals": ["generated_artifact_policy_ambiguity"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                }
            ],
        },
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="close-stale-loop")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    item = backlog["items"][0]

    assert item["status"] == "closed"
    assert item["closed_at"] == NOW
    assert item["closure_reason"] == "not_observed_in_latest_inspection"
    assert item["last_seen_at"] == "2026-04-14T00:00:00Z"


def test_self_inspection_keeps_in_progress_backlog_items_when_not_reobserved(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-14T00:00:00Z",
            "items": [
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 63,
                    "status": "in_progress",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": "2026-04-14T00:00:00Z",
                    "last_seen_at": "2026-04-14T00:00:00Z",
                    "recurrence_count": 1,
                }
            ],
        },
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="keep-progress-loop")
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    item = backlog["items"][0]

    assert item["status"] == "in_progress"
    assert "closed_at" not in item
    assert "closure_reason" not in item


def test_self_inspection_discovers_executor_result_candidates(tmp_path: Path) -> None:
    write_executor_result_session(
        tmp_path,
        session_id="session-partial",
        state="candidate_generated",
        result_status="partial",
        validation_status="failed",
        verification_hint="skip",
    )
    write_executor_result_session(
        tmp_path,
        session_id="session-no-op",
        state="failed",
        result_status="no_op",
        validation_status="not_run",
        verification_hint="skip",
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="executor-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    executor_items = [
        candidate
        for candidate in report["candidates"]
        if candidate["category"] == "executor_result_gap"
    ]

    assert report["loop_id"] == "executor-loop"
    assert [item["id"] for item in executor_items] == [
        "executor_result_gap-session-no-op",
        "executor_result_gap-session-partial",
    ]
    assert {item["recommendation"] for item in executor_items} == {
        "inspect_executor_no_op",
        "resume_executor_repair",
    }
    assert any(
        "status=no_op; validation=not_run; hint=skip" in item["evidence"][0]["summary"]
        for item in executor_items
    )
    assert any(
        "status=partial; validation=failed; hint=skip" in item["evidence"][0]["summary"]
        for item in executor_items
    )


def test_self_inspection_discovers_repeated_executor_history_candidates(
    tmp_path: Path,
) -> None:
    write_executor_result_history(
        tmp_path,
        session_id="session-history",
        attempts=[
            {
                "attempt_id": "attempt-one",
                "recorded_at": NOW,
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-history/executor_results/attempts/attempt-one.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-one/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-one/ingest_report.md",
            },
            {
                "attempt_id": "attempt-two",
                "recorded_at": NOW,
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-history/executor_results/attempts/attempt-two.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-two/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-two/ingest_report.md",
            },
        ],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="history-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {candidate["category"] for candidate in report["candidates"]}

    assert "partial_completion_gap" in categories


def test_self_inspection_uses_blocked_dry_run_summary_for_single_attempt_history(
    tmp_path: Path,
) -> None:
    write_executor_result_history(
        tmp_path,
        session_id="session-blocked",
        attempts=[
            {
                "attempt_id": "attempt-one",
                "recorded_at": NOW,
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "completed",
                "ingest_status": "accepted_with_warning",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "rerun",
                "verification_triggered": False,
                "verification_verdict": "mixed",
                "validation_status": "failed",
                "warning_ids": ["completed_validation_failed"],
                "backlog_categories": ["workflow_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-blocked/executor_results/attempts/attempt-one.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-one/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-one/ingest_report.md",
            }
        ],
    )
    write_executor_dry_run_summary(
        tmp_path,
        session_id="session-blocked",
        verdict="blocked",
        verdict_reason="completed_attempt_not_verification_clean",
        history_signals=["completed_verify_blocked", "validation_conflict"],
        next_recommendation="resolve verification blocking evidence before another completed attempt",
        latest_result_status="completed",
        latest_ingest_status="accepted_with_warning",
        rule_status_counts={"attention": 1, "blocked": 1, "clear": 4},
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="dry-run-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    workflow_candidates = [
        item for item in report["candidates"] if item["category"] == "workflow_gap"
    ]

    assert workflow_candidates
    assert any(
        evidence["source"] == "executor_result_dry_run"
        and evidence["path"].endswith("dry_run_summary.json")
        for evidence in workflow_candidates[0]["evidence"]
    )
    assert "executor_dry_run_blocked" in workflow_candidates[0]["signals"]
    assert any(
        "dry_run=blocked" in evidence["summary"]
        and "source=materialized" in evidence["summary"]
        for evidence in workflow_candidates[0]["evidence"]
    )


def test_self_inspection_uses_dry_run_signal_for_missing_no_op_explanation(
    tmp_path: Path,
) -> None:
    write_executor_result_history(
        tmp_path,
        session_id="session-noop",
        attempts=[
            {
                "attempt_id": "attempt-one",
                "recorded_at": NOW,
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "no_op",
                "ingest_status": "accepted_no_op",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "not_run",
                "warning_ids": ["no_op_without_explanation"],
                "backlog_categories": ["no_op_safeguard_gap"],
                "changed_files_count": 0,
                "notes_count": 0,
                "attempt_path": ".qa-z/sessions/session-noop/executor_results/attempts/attempt-one.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-one/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-one/ingest_report.md",
            }
        ],
    )
    write_executor_dry_run_summary(
        tmp_path,
        session_id="session-noop",
        verdict="attention_required",
        verdict_reason="manual_retry_review_required",
        history_signals=["missing_no_op_explanation"],
        next_recommendation="inspect executor attempt history before another retry",
        latest_result_status="no_op",
        latest_ingest_status="accepted_no_op",
        rule_status_counts={"attention": 1, "blocked": 0, "clear": 5},
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="noop-dry-run-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    noop_candidates = [
        item
        for item in report["candidates"]
        if item["category"] == "no_op_safeguard_gap"
    ]

    assert noop_candidates
    assert "executor_dry_run_attention" in noop_candidates[0]["signals"]
    assert any(
        evidence["source"] == "executor_result_dry_run"
        and "source=materialized" in evidence["summary"]
        for evidence in noop_candidates[0]["evidence"]
    )


def test_self_inspection_synthesizes_dry_run_from_history_when_summary_is_missing(
    tmp_path: Path,
) -> None:
    write_executor_result_history(
        tmp_path,
        session_id="session-partial",
        attempts=[
            {
                "attempt_id": "attempt-one",
                "recorded_at": "2026-04-16T00:00:01Z",
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-partial/executor_results/attempts/attempt-one.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-one/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-one/ingest_report.md",
            },
            {
                "attempt_id": "attempt-two",
                "recorded_at": "2026-04-16T00:00:02Z",
                "bridge_id": "bridge-one",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-partial/executor_results/attempts/attempt-two.json",
                "ingest_artifact_path": ".qa-z/executor-results/attempt-two/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/attempt-two/ingest_report.md",
            },
        ],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="partial-fallback-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    partial_candidates = [
        item
        for item in report["candidates"]
        if item["category"] == "partial_completion_gap"
    ]

    assert partial_candidates
    assert "executor_dry_run_attention" in partial_candidates[0]["signals"]
    assert any(
        evidence["source"] == "executor_result_dry_run_fallback"
        and "dry_run=attention_required" in evidence["summary"]
        and "source=history_fallback" in evidence["summary"]
        for evidence in partial_candidates[0]["evidence"]
    )


def test_self_inspection_promotes_executor_ingest_backlog_implications(
    tmp_path: Path,
) -> None:
    write_executor_ingest_record(
        tmp_path,
        record_id="stale-one",
        ingest_status="rejected_stale",
        result_status="completed",
        verify_resume_status="stale_result",
        backlog_implications=[
            {
                "id": "evidence_freshness_gap-stale-one",
                "title": "Harden executor result freshness handling",
                "category": "evidence_freshness_gap",
                "recommendation": "harden_executor_result_freshness",
                "signals": ["executor_result_stale"],
                "impact": 3,
                "likelihood": 4,
                "confidence": 4,
                "repair_cost": 3,
                "summary": "stale result blocked verification resume",
            }
        ],
    )
    write_executor_ingest_record(
        tmp_path,
        record_id="mismatch-one",
        ingest_status="rejected_mismatch",
        result_status="completed",
        verify_resume_status="mismatch_detected",
        backlog_implications=[
            {
                "id": "provenance_gap-mismatch-one",
                "title": "Harden executor provenance validation",
                "category": "provenance_gap",
                "recommendation": "audit_executor_contract",
                "signals": ["executor_result_provenance_mismatch"],
                "impact": 4,
                "likelihood": 4,
                "confidence": 4,
                "repair_cost": 3,
                "summary": "bridge/session provenance mismatch rejected ingest",
            }
        ],
    )
    write_executor_ingest_record(
        tmp_path,
        record_id="partial-one",
        ingest_status="accepted_partial",
        result_status="partial",
        verify_resume_status="verify_blocked",
        backlog_implications=[
            {
                "id": "partial_completion_gap-partial-one",
                "title": "Harden partial completion ingest handling",
                "category": "partial_completion_gap",
                "recommendation": "harden_partial_completion_handling",
                "signals": ["executor_result_partial"],
                "impact": 3,
                "likelihood": 4,
                "confidence": 4,
                "repair_cost": 3,
                "summary": "partial result blocked immediate verify",
            }
        ],
    )
    write_executor_ingest_record(
        tmp_path,
        record_id="noop-one",
        ingest_status="accepted_no_op",
        result_status="no_op",
        verify_resume_status="verify_blocked",
        backlog_implications=[
            {
                "id": "no_op_safeguard_gap-noop-one",
                "title": "Harden no-op executor result safeguards",
                "category": "no_op_safeguard_gap",
                "recommendation": "harden_executor_no_op_safeguards",
                "signals": ["executor_result_no_op"],
                "impact": 3,
                "likelihood": 3,
                "confidence": 4,
                "repair_cost": 2,
                "summary": "no-op result lacked a strong explanation",
            }
        ],
    )
    write_executor_ingest_record(
        tmp_path,
        record_id="validation-one",
        ingest_status="accepted_with_warning",
        result_status="completed",
        verify_resume_status="verify_blocked",
        backlog_implications=[
            {
                "id": "workflow_gap-validation-one",
                "title": "Harden executor validation evidence consistency",
                "category": "workflow_gap",
                "recommendation": "audit_executor_contract",
                "signals": ["executor_validation_failed"],
                "impact": 3,
                "likelihood": 3,
                "confidence": 4,
                "repair_cost": 2,
                "summary": "validation metadata conflicted with detailed executor results",
            }
        ],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="ingest-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    categories = {item["category"] for item in report["candidates"]}

    assert "evidence_freshness_gap" in categories
    assert "provenance_gap" in categories
    assert "partial_completion_gap" in categories
    assert "no_op_safeguard_gap" in categories
    assert "workflow_gap" in categories
    assert any(
        item["recommendation"] == "audit_executor_contract"
        for item in report["candidates"]
        if item["category"] in {"provenance_gap", "workflow_gap"}
    )


def test_select_next_writes_selected_tasks_plan_and_history(tmp_path: Path) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "low",
                    "title": "Low priority",
                    "category": "workflow_gap",
                    "evidence": [{"source": "test", "path": "low.json"}],
                    "impact": 2,
                    "likelihood": 2,
                    "confidence": 2,
                    "repair_cost": 1,
                    "priority_score": 7,
                    "status": "open",
                    "recommendation": "create_repair_session",
                    "signals": [],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
                {
                    "id": "high",
                    "title": "High priority",
                    "category": "verify_regression",
                    "evidence": [{"source": "verify", "path": "high.json"}],
                    "impact": 5,
                    "likelihood": 5,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 101,
                    "status": "open",
                    "recommendation": "stabilize_verification_surface",
                    "signals": ["verify_regressed"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
                {
                    "id": "done",
                    "title": "Closed item",
                    "category": "benchmark_gap",
                    "evidence": [{"source": "benchmark", "path": "done.json"}],
                    "impact": 5,
                    "likelihood": 5,
                    "confidence": 5,
                    "repair_cost": 1,
                    "priority_score": 124,
                    "status": "completed",
                    "recommendation": "add_benchmark_fixture",
                    "signals": ["benchmark_fail"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )

    paths = select_next_tasks(root=tmp_path, count=2, now=NOW, loop_id="select-loop")

    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    history_lines = (
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    history = json.loads(history_lines[0])

    assert [task["id"] for task in selected["selected_tasks"]] == ["high", "low"]
    assert selected["loop_id"] == "select-loop"
    assert "High priority" in paths.loop_plan_path.read_text(encoding="utf-8")
    assert history["loop_id"] == "select-loop"
    assert history["selected_tasks"] == ["high", "low"]
    assert history["resulting_session_id"] is None


def test_score_candidate_boosts_executor_result_safety_signals() -> None:
    candidate = BacklogCandidate(
        id="executor_result_gap-session-no-op",
        title="Inspect executor no-op result: session-no-op",
        category="executor_result_gap",
        evidence=[
            {
                "source": "executor_result",
                "path": ".qa-z/sessions/session-no-op/executor_result.json",
                "summary": "status=no_op; validation=failed; hint=skip",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=3,
        repair_cost=5,
        recommendation="inspect_executor_no_op",
        signals=["executor_validation_failed", "executor_result_no_op"],
    )

    score = score_candidate(candidate)

    assert score == 46


def test_score_candidate_prioritizes_blocked_dry_run_over_attention() -> None:
    blocked_candidate = BacklogCandidate(
        id="workflow_gap-session-blocked",
        title="Audit repeated executor attempt friction: session-blocked",
        category="workflow_gap",
        evidence=[{"source": "executor_result_dry_run", "path": "blocked.json"}],
        impact=3,
        likelihood=4,
        confidence=4,
        repair_cost=3,
        recommendation="audit_executor_contract",
        signals=[
            "service_readiness_gap",
            "regression_prevention",
            "executor_dry_run_blocked",
        ],
    )
    attention_candidate = BacklogCandidate(
        id="no_op_safeguard_gap-session-noop",
        title="Inspect repeated no-op executor attempts: session-noop",
        category="no_op_safeguard_gap",
        evidence=[{"source": "executor_result_dry_run", "path": "attention.json"}],
        impact=3,
        likelihood=4,
        confidence=4,
        repair_cost=3,
        recommendation="harden_executor_no_op_safeguards",
        signals=[
            "executor_result_no_op",
            "regression_prevention",
            "executor_dry_run_attention",
        ],
    )

    assert score_candidate(blocked_candidate) > score_candidate(attention_candidate)


def test_score_candidate_boosts_reseed_and_service_readiness_signals() -> None:
    candidate = BacklogCandidate(
        id="coverage_gap-mixed-surface-benchmark-realism",
        title="Expand executed mixed-surface benchmark realism",
        category="coverage_gap",
        evidence=[
            {
                "source": "roadmap",
                "path": "docs/reports/next-improvement-roadmap.md",
                "summary": "mixed-surface executed benchmark expansion remains open",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=3,
        repair_cost=5,
        recommendation="add_benchmark_fixture",
        signals=[
            "mixed_surface_realism_gap",
            "roadmap_gap",
            "service_readiness_gap",
            "recent_empty_loop_chain",
        ],
        recurrence_count=2,
    )

    score = score_candidate(candidate)

    assert score == 52


def test_self_inspection_reseeds_backlog_from_reports_when_empty(
    tmp_path: Path,
) -> None:
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        ## Known Gaps

        ### Mixed-Surface Executed Benchmark Expansion

        Mixed-language verification coverage exists, but executed mixed-surface
        behavior across fast, deep, and repair handoff is still thin.

        ### Current-Truth Drift Risk

        README, artifact schema, config example, and CLI behavior still need a
        current-truth audit.
        """,
    )
    write_report(
        tmp_path,
        "next-improvement-roadmap.md",
        """
        # QA-Z Next Improvement Roadmap

        ## Priority 3: Mixed-Surface Executed Benchmark Expansion

        Add realistic mixed-surface fixtures that exercise fast, deep, and
        handoff behavior.

        ## Priority 4: Current-Truth Sync Audit

        Run one explicit sync audit across README, schema docs, config example,
        and CLI behavior.
        """,
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        README.md and docs/artifact-schema-v1.md should stay in sync with the
        current command surface before the alpha baseline hardens.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="report-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))

    assert report["loop_id"] == "report-loop"
    assert {
        "coverage_gap",
        "docs_drift",
        "backlog_reseeding_gap",
    } <= {candidate["category"] for candidate in report["candidates"]}
    assert any(
        entry["source"] == "roadmap"
        for candidate in report["candidates"]
        for entry in candidate["evidence"]
    )
    assert any(
        entry["source"] == "current_state"
        for candidate in report["candidates"]
        for entry in candidate["evidence"]
    )
    assert any(item["category"] == "backlog_reseeding_gap" for item in backlog["items"])


def test_self_inspection_skips_coverage_gap_when_executed_mixed_fixture_exists(
    tmp_path: Path,
) -> None:
    write_fixture_index(tmp_path, ["mixed_fast_handoff_functional_worktree_cleanup"])

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="mixed-executed-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    categories = {candidate["category"] for candidate in report["candidates"]}

    assert "coverage_gap" not in categories


def test_self_inspection_derives_autonomy_selection_gap_from_empty_loop_history(
    tmp_path: Path,
) -> None:
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": "2026-04-14T00:00:00Z",
                "selected_tasks": [],
                "evidence_used": [],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "blocked_no_candidates",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": "2026-04-14T00:05:00Z",
                "selected_tasks": [],
                "evidence_used": [],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "blocked_no_candidates",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-3",
                "created_at": "2026-04-14T00:10:00Z",
                "selected_tasks": [],
                "evidence_used": [],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "blocked_no_candidates",
            },
        ],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="history-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    candidate = next(
        item
        for item in report["candidates"]
        if item["category"] == "autonomy_selection_gap"
    )

    assert candidate["id"] == "autonomy_selection_gap-empty-loop-chain"
    assert "recent_empty_loop_chain" in candidate["signals"]
    assert candidate["recommendation"] == "improve_empty_loop_handling"


def test_self_inspection_promotes_dirty_worktree_risk_from_live_signals(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=12,
        untracked_count=24,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["docs/reports/worktree-triage.md", "src/qa_z/autonomy.py"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="worktree-risk-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    candidate = next(
        item for item in report["candidates"] if item["category"] == "worktree_risk"
    )

    assert candidate["id"] == "worktree_risk-dirty-worktree"
    assert candidate["recommendation"] == "reduce_integration_risk"
    assert "dirty_worktree_large" in candidate["signals"]
    assert "modified=12" in candidate["evidence"][0]["summary"]
    assert "untracked=24" in candidate["evidence"][0]["summary"]
    assert "areas=docs:2, source:2" in candidate["evidence"][0]["summary"]


def test_runtime_artifact_path_detects_benchmark_snapshot_siblings() -> None:
    assert is_runtime_artifact_path("benchmarks/results/report.md") is True
    assert is_runtime_artifact_path("benchmarks/results-p12-dry-run/report.md") is True
    assert (
        is_runtime_artifact_path("benchmarks/results-p12-dry-run/work/run.json") is True
    )
    assert (
        is_runtime_artifact_path("benchmarks/fixtures/py_test_failure/expected.json")
        is False
    )


def test_worktree_area_classifies_benchmark_snapshots_as_runtime_artifacts() -> None:
    assert (
        classify_worktree_path_area("benchmarks/results-p12-dry-run/report.md")
        == "runtime_artifact"
    )
    assert (
        classify_worktree_path_area("benchmarks/fixtures/py_test_failure/expected.json")
        == "benchmark"
    )


def test_self_inspection_promotes_deferred_cleanup_and_commit_isolation_gaps(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=3,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md"],
        untracked_paths=["docs/reports/worktree-triage.md"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Deferred cleanup items remain open. Generated benchmark summaries should
        stay deferred until intentionally frozen evidence is declared.
        """,
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation and `git add -p`.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="cleanup-gap-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" in categories
    assert "commit_isolation_gap" in categories
    deferred = next(
        item
        for item in report["candidates"]
        if item["category"] == "deferred_cleanup_gap"
    )
    isolation = next(
        item
        for item in report["candidates"]
        if item["category"] == "commit_isolation_gap"
    )
    assert deferred["recommendation"] == "triage_and_isolate_changes"
    assert isolation["recommendation"] == "isolate_foundation_commit"


def test_self_inspection_uses_alpha_closure_snapshot_for_commit_isolation_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=3,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["docs/reports/worktree-commit-plan.md"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation.

        ## Alpha Closure Readiness Snapshot

        The latest full local gate pass for this accumulated alpha baseline is:

        - `python -m pytest`: 297 passed, 1 skipped
        - `python -m qa_z benchmark --json`: 47/47 fixtures, overall_rate 1.0

        The next operator action is to split the worktree by this commit plan.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="closure-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    isolation = next(
        item
        for item in report["candidates"]
        if item["id"] == "commit_isolation_gap-foundation-order"
    )

    assert isolation["recommendation"] == "isolate_foundation_commit"
    assert {evidence["summary"] for evidence in isolation["evidence"]} >= {
        "alpha closure readiness snapshot pins full gate pass and commit-split action",
        "dirty worktree still spans modified=3; untracked=1; areas=docs:2, source:1",
    }


def test_self_inspection_promotes_artifact_hygiene_and_evidence_freshness_gaps(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=4,
        untracked_count=2,
        staged_count=0,
        modified_paths=[".gitignore"],
        untracked_paths=["benchmarks/results/summary.json"],
        runtime_artifact_paths=[".qa-z/loops/latest/outcome.json"],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Runtime artifacts are still mixed with source-like areas and the generated
        benchmark outputs need a clearer cleanup policy.
        """,
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Frozen evidence versus runtime result storage is still ambiguous in the
        current worktree, especially for benchmark outputs.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="artifact-gap-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "artifact_hygiene_gap" in categories
    assert "evidence_freshness_gap" in categories
    hygiene = next(
        item
        for item in report["candidates"]
        if item["category"] == "artifact_hygiene_gap"
    )
    freshness = next(
        item
        for item in report["candidates"]
        if item["category"] == "evidence_freshness_gap"
    )
    assert hygiene["recommendation"] == "separate_runtime_from_source_artifacts"
    assert freshness["recommendation"] == "clarify_generated_vs_frozen_evidence_policy"


def test_generated_artifact_policy_snapshot_requires_policy_doc(
    tmp_path: Path,
) -> None:
    write_gitignore(
        tmp_path,
        [
            ".qa-z/",
            "!benchmarks/fixtures/**/repo/.qa-z/",
            "!benchmarks/fixtures/**/repo/.qa-z/**",
            "benchmarks/results/work/",
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )

    signals = collect_live_repository_signals(tmp_path)

    assert signals["generated_artifact_ignore_policy_explicit"] is True
    assert signals["generated_artifact_documented_policy_explicit"] is False
    assert signals["generated_artifact_policy_explicit"] is False
    assert signals["missing_generated_artifact_policy_rules"] == []
    assert (
        "generated-vs-frozen evidence policy document is missing"
        in signals["missing_generated_artifact_policy_terms"]
    )


def test_self_inspection_promotes_policy_gap_when_doc_is_missing(
    tmp_path: Path,
) -> None:
    write_gitignore(
        tmp_path,
        [
            ".qa-z/",
            "!benchmarks/fixtures/**/repo/.qa-z/",
            "!benchmarks/fixtures/**/repo/.qa-z/**",
            "benchmarks/results/work/",
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Generated versus frozen evidence policy still needs one explicit source
        of truth for benchmark outputs and runtime result storage.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="missing-policy-doc")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    candidate = next(
        item
        for item in report["candidates"]
        if item["category"] == "evidence_freshness_gap"
    )

    assert candidate["recommendation"] == "clarify_generated_vs_frozen_evidence_policy"
    assert any(
        entry["source"] == "generated_artifact_policy"
        and "policy document is missing" in entry["summary"]
        for entry in candidate["evidence"]
    )


def test_self_inspection_skips_stale_artifact_policy_gaps_when_gitignore_is_explicit(
    tmp_path: Path, monkeypatch
) -> None:
    write_gitignore(
        tmp_path,
        [
            ".qa-z/",
            "!benchmarks/fixtures/**/repo/.qa-z/",
            "!benchmarks/fixtures/**/repo/.qa-z/**",
            "benchmarks/results/work/",
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    stub_live_repository_signals(
        monkeypatch,
        modified_count=1,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md"],
        untracked_paths=["docs/reports/worktree-triage.md"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
        generated_artifact_policy_explicit=True,
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Runtime artifacts are still mixed with source-like areas and the generated
        benchmark outputs need a clearer cleanup policy.
        """,
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Frozen evidence versus runtime result storage is still ambiguous in the
        current worktree, especially for benchmark outputs.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="explicit-ignore-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "artifact_hygiene_gap" not in categories
    assert "evidence_freshness_gap" not in categories
    assert "runtime_artifact_cleanup_gap" not in categories


def test_self_inspection_skips_policy_gaps_when_policy_doc_and_gitignore_are_explicit(
    tmp_path: Path,
) -> None:
    write_gitignore(
        tmp_path,
        [
            ".qa-z/",
            "!benchmarks/fixtures/**/repo/.qa-z/",
            "!benchmarks/fixtures/**/repo/.qa-z/**",
            "benchmarks/results/work/",
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_generated_evidence_policy(tmp_path)
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Frozen evidence versus runtime result storage was historically ambiguous
        in the current worktree, especially for benchmark outputs.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="explicit-policy-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "artifact_hygiene_gap" not in categories
    assert "evidence_freshness_gap" not in categories
    assert "runtime_artifact_cleanup_gap" not in categories


def test_self_improvement_cli_commands_write_expected_paths(
    tmp_path: Path,
    capsys,
) -> None:
    write_benchmark_summary(tmp_path)

    inspect_exit = main(["self-inspect", "--path", str(tmp_path), "--json"])
    inspect_output = json.loads(capsys.readouterr().out)
    select_exit = main(
        ["select-next", "--path", str(tmp_path), "--count", "1", "--json"]
    )
    select_output = json.loads(capsys.readouterr().out)
    backlog_exit = main(["backlog", "--path", str(tmp_path), "--json"])
    backlog_output = json.loads(capsys.readouterr().out)

    assert inspect_exit == 0
    assert inspect_output["kind"] == "qa_z.self_inspection"
    assert select_exit == 0
    assert select_output["kind"] == "qa_z.selected_tasks"
    assert backlog_exit == 0
    assert backlog_output["kind"] == "qa_z.improvement_backlog"
    assert (tmp_path / ".qa-z" / "loops" / "latest" / "selected_tasks.json").exists()
    assert (tmp_path / ".qa-z" / "loops" / "latest" / "loop_plan.md").exists()


def test_loop_plan_states_external_executor_boundary(tmp_path: Path) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "handoff-gap",
                    "title": "Create repair session for unresolved blocker",
                    "category": "session_gap",
                    "evidence": [{"source": "session", "path": ".qa-z/sessions/s"}],
                    "impact": 3,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 45,
                    "status": "open",
                    "recommendation": "create_repair_session",
                    "signals": ["regression_prevention"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                }
            ],
        },
    )

    paths = select_next_tasks(root=tmp_path, count=1, now=NOW, loop_id="boundary")
    plan = paths.loop_plan_path.read_text(encoding="utf-8")

    assert "does not call Codex or Claude APIs" in plan
    assert "external executor" in plan
    assert "create_repair_session" in plan


def test_loop_plan_preserves_selection_score_and_penalty_residue() -> None:
    plan = render_loop_plan(
        loop_id="loop-penalty",
        generated_at=NOW,
        selected_items=[
            {
                "id": "worktree_risk-dirty-worktree",
                "title": "Reduce dirty worktree integration risk",
                "category": "worktree_risk",
                "recommendation": "reduce_integration_risk",
                "priority_score": 65,
                "selection_priority_score": 60,
                "selection_penalty": 5,
                "selection_penalty_reasons": [
                    "recent_task_reselected",
                    "recent_category_reselected",
                ],
                "evidence": [
                    {
                        "source": "git_status",
                        "path": ".",
                        "summary": "modified=25; untracked=352; staged=0",
                    }
                ],
            }
        ],
    )

    assert "selection score: 60" in plan
    assert (
        "selection penalty: 5 (`recent_task_reselected`, "
        "`recent_category_reselected`)" in plan
    )


def test_selected_task_action_hint_specializes_closure_recommendations() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "isolate_foundation_commit",
            "evidence": [
                {
                    "source": "worktree_commit_plan",
                    "path": "docs/reports/worktree-commit-plan.md",
                    "summary": "alpha closure readiness snapshot pins full gate pass",
                }
            ],
        }
    ) == (
        "follow docs/reports/worktree-commit-plan.md to split the foundation "
        "commit, then rerun self-inspection"
    )


def test_worktree_action_areas_reads_area_summary_from_evidence() -> None:
    assert worktree_action_areas(
        {
            "evidence": [
                {
                    "source": "git_status",
                    "summary": (
                        "modified=31; untracked=488; staged=0; "
                        "areas=benchmark:271, docs:160, source:42; "
                        "sample=.github/workflows/ci.yml, README.md"
                    ),
                }
            ]
        }
    ) == ["benchmark", "docs", "source"]


def test_worktree_action_areas_ignores_missing_or_malformed_area_summary() -> None:
    assert worktree_action_areas({"evidence": [{"summary": "modified=1"}]}) == []
    assert worktree_action_areas({"evidence": [{"summary": "areas=, broken"}]}) == []


def test_selected_task_action_hint_uses_dirty_worktree_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "reduce_integration_risk",
            "evidence": [
                {
                    "source": "git_status",
                    "summary": "modified=31; areas=benchmark:271, docs:160, source:42",
                }
            ],
        }
    ) == (
        "triage benchmark and docs changes first, separate generated artifacts, "
        "then rerun self-inspection"
    )


def test_selected_task_action_hint_keeps_fallback_without_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "reduce_integration_risk",
            "evidence": [{"source": "git_status", "summary": "modified=31"}],
        }
    ) == (
        "inspect the dirty worktree and separate generated artifacts, "
        "then rerun self-inspection"
    )


def test_selected_task_action_hint_uses_commit_isolation_area_evidence() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "isolate_foundation_commit",
            "evidence": [
                {
                    "source": "git_status",
                    "summary": (
                        "dirty worktree still spans modified=3; untracked=1; "
                        "areas=docs:2, source:1"
                    ),
                }
            ],
        }
    ) == (
        "follow docs/reports/worktree-commit-plan.md and isolate docs and source "
        "changes into the foundation split, then rerun self-inspection"
    )


def test_selected_task_action_hint_keeps_commit_isolation_fallback_without_area_evidence() -> (
    None
):
    assert selected_task_action_hint(
        {
            "recommendation": "isolate_foundation_commit",
            "evidence": [{"source": "git_status", "summary": "dirty worktree"}],
        }
    ) == (
        "follow docs/reports/worktree-commit-plan.md to split the foundation "
        "commit, then rerun self-inspection"
    )


def test_selected_task_action_hint_names_generated_snapshot_decision() -> None:
    assert selected_task_action_hint(
        {
            "recommendation": "triage_and_isolate_changes",
            "evidence": [
                {
                    "source": "runtime_artifacts",
                    "summary": (
                        "generated runtime artifacts need explicit cleanup handling: "
                        "benchmarks/results-p12-dry-run/report.md"
                    ),
                }
            ],
        }
    ) == (
        "decide whether generated artifacts stay local-only or become intentional "
        "frozen evidence, separate them from source changes, then rerun "
        "self-inspection"
    )


def test_selected_task_validation_command_specializes_known_recommendations() -> None:
    assert (
        selected_task_validation_command(
            {"recommendation": "isolate_foundation_commit"}
        )
        == "python -m qa_z self-inspect"
    )
    assert (
        selected_task_validation_command({"recommendation": "add_benchmark_fixture"})
        == "python -m qa_z benchmark --json"
    )


def test_loop_plan_includes_selected_task_action_hint() -> None:
    plan = render_loop_plan(
        loop_id="loop-action-hint",
        generated_at=NOW,
        selected_items=[
            {
                "id": "commit_isolation_gap-foundation-order",
                "title": "Isolate the foundation commit before later batches",
                "category": "commit_isolation_gap",
                "recommendation": "isolate_foundation_commit",
                "priority_score": 64,
                "evidence": [
                    {
                        "source": "worktree_commit_plan",
                        "path": "docs/reports/worktree-commit-plan.md",
                        "summary": (
                            "alpha closure readiness snapshot pins full gate pass"
                        ),
                    }
                ],
            }
        ],
    )

    assert (
        "   - action: follow docs/reports/worktree-commit-plan.md to split the "
        "foundation commit, then rerun self-inspection" in plan
    )
    assert "   - validation: `python -m qa_z self-inspect`" in plan


def test_compact_evidence_summary_prioritizes_alpha_closure_snapshot() -> None:
    item = {
        "id": "commit_isolation_gap-foundation-order",
        "evidence": [
            {
                "source": "current_state",
                "path": "docs/reports/current-state-analysis.md",
                "summary": (
                    "report calls out commit-order dependency or commit-isolation work"
                ),
            },
            {
                "source": "worktree_commit_plan",
                "path": "docs/reports/worktree-commit-plan.md",
                "summary": (
                    "alpha closure readiness snapshot pins full gate pass and "
                    "commit-split action"
                ),
            },
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "worktree_commit_plan: alpha closure readiness snapshot pins full gate "
        "pass and commit-split action"
    )


def test_compact_evidence_summary_appends_area_action_basis() -> None:
    item = {
        "id": "commit_isolation_gap-foundation-order",
        "evidence": [
            {
                "source": "worktree_commit_plan",
                "path": "docs/reports/worktree-commit-plan.md",
                "summary": (
                    "alpha closure readiness snapshot pins full gate pass and "
                    "commit-split action"
                ),
            },
            {
                "source": "git_status",
                "path": ".",
                "summary": (
                    "dirty worktree still spans modified=3; untracked=1; "
                    "areas=docs:2, source:1"
                ),
            },
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "worktree_commit_plan: alpha closure readiness snapshot pins full gate "
        "pass and commit-split action; action basis: git_status: dirty worktree "
        "still spans modified=3; untracked=1; areas=docs:2, source:1"
    )


def test_compact_evidence_summary_does_not_duplicate_primary_area_summary() -> None:
    item = {
        "evidence": [
            {
                "source": "git_status",
                "summary": "modified=1; areas=docs:1",
            }
        ]
    }

    assert compact_backlog_evidence_summary(item) == (
        "git_status: modified=1; areas=docs:1"
    )


def test_compact_evidence_summary_appends_generated_action_basis() -> None:
    item = {
        "id": "deferred_cleanup_gap-worktree-deferred-items",
        "recommendation": "triage_and_isolate_changes",
        "evidence": [
            {
                "source": "current_state",
                "path": "docs/reports/current-state-analysis.md",
                "summary": (
                    "report calls out deferred cleanup work or generated outputs "
                    "to isolate"
                ),
            },
            {
                "source": "generated_outputs",
                "path": "benchmarks/results/report.md",
                "summary": (
                    "generated benchmark outputs still present: "
                    "benchmarks/results/report.md, benchmarks/results/summary.json"
                ),
            },
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "current_state: report calls out deferred cleanup work or generated "
        "outputs to isolate; action basis: generated_outputs: generated "
        "benchmark outputs still present: benchmarks/results/report.md, "
        "benchmarks/results/summary.json"
    )


def test_compact_evidence_summary_does_not_duplicate_generated_primary() -> None:
    item = {
        "recommendation": "triage_and_isolate_changes",
        "evidence": [
            {
                "source": "generated_outputs",
                "summary": (
                    "generated benchmark outputs still present: "
                    "benchmarks/results/report.md"
                ),
            }
        ],
    }

    assert compact_backlog_evidence_summary(item) == (
        "generated_outputs: generated benchmark outputs still present: "
        "benchmarks/results/report.md"
    )


def test_score_candidate_prioritizes_worktree_risk_over_docs_drift() -> None:
    worktree_candidate = BacklogCandidate(
        id="worktree_risk-dirty-worktree",
        title="Reduce dirty worktree integration risk",
        category="worktree_risk",
        evidence=[
            {
                "source": "git_status",
                "path": ".",
                "summary": "modified=12; untracked=24; staged=0",
            }
        ],
        impact=4,
        likelihood=4,
        confidence=4,
        repair_cost=3,
        recommendation="reduce_integration_risk",
        signals=["dirty_worktree_large", "worktree_integration_risk"],
    )
    docs_candidate = BacklogCandidate(
        id="docs_drift-current_truth_sync",
        title="Run a current-truth docs and schema sync audit",
        category="docs_drift",
        evidence=[
            {
                "source": "docs",
                "path": "README.md",
                "summary": "command surface drift",
            }
        ],
        impact=2,
        likelihood=3,
        confidence=4,
        repair_cost=2,
        recommendation="sync_contract_and_docs",
        signals=["schema_doc_drift"],
    )

    assert score_candidate(worktree_candidate) > score_candidate(docs_candidate)


def test_select_next_penalizes_recent_reselection_from_loop_history(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 61,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 2,
                },
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                            "summary": "commit order dependency remains",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 60,
                    "status": "open",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": "2026-04-14T00:00:00Z",
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "evidence_used": ["."],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": ["commit_isolation_gap-foundation-order"],
                "state": "fallback_selected",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": "2026-04-14T00:05:00Z",
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "evidence_used": ["."],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": ["commit_isolation_gap-foundation-order"],
                "state": "fallback_selected",
            },
        ],
    )

    paths = select_next_tasks(root=tmp_path, count=1, now=NOW, loop_id="penalty-loop")
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "commit_isolation_gap-foundation-order"
    ]
    assert selected["selected_tasks"][0]["selection_penalty"] == 0


def test_select_next_penalizes_repeated_fallback_family_when_alternative_exists(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 62,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 2,
                },
                {
                    "id": "coverage_gap-mixed-surface-benchmark-realism",
                    "title": "Expand executed mixed-surface benchmark realism",
                    "category": "coverage_gap",
                    "evidence": [
                        {
                            "source": "roadmap",
                            "path": "docs/reports/next-improvement-roadmap.md",
                            "summary": "mixed-surface executed benchmark expansion remains open",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 61,
                    "status": "open",
                    "recommendation": "add_benchmark_fixture",
                    "signals": ["mixed_surface_realism_gap"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": "2026-04-14T00:00:00Z",
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "selected_categories": ["worktree_risk"],
                "evidence_used": ["."],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": ["coverage_gap-mixed-surface-benchmark-realism"],
                "state": "fallback_selected",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": "2026-04-14T00:05:00Z",
                "selected_tasks": ["commit_isolation_gap-foundation-order"],
                "selected_categories": ["commit_isolation_gap"],
                "evidence_used": ["docs/reports/worktree-commit-plan.md"],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": ["coverage_gap-mixed-surface-benchmark-realism"],
                "state": "fallback_selected",
            },
        ],
    )

    paths = select_next_tasks(root=tmp_path, count=1, now=NOW, loop_id="family-penalty")
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    history = json.loads(
        paths.history_path.read_text(encoding="utf-8").splitlines()[-1]
    )

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "coverage_gap-mixed-surface-benchmark-realism"
    ]
    assert selected["selected_tasks"][0]["selection_penalty"] == 0
    assert history["selected_fallback_families"] == ["benchmark_expansion"]
    assert "worktree_risk-dirty-worktree" in history["next_candidates"]


def test_select_next_diversifies_fallback_families_within_one_batch(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 62,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                            "summary": "commit order dependency remains",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 61,
                    "status": "open",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
                {
                    "id": "coverage_gap-mixed-surface-benchmark-realism",
                    "title": "Expand executed mixed-surface benchmark realism",
                    "category": "coverage_gap",
                    "evidence": [
                        {
                            "source": "roadmap",
                            "path": "docs/reports/next-improvement-roadmap.md",
                            "summary": "mixed-surface expansion remains open",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 60,
                    "status": "open",
                    "recommendation": "add_benchmark_fixture",
                    "signals": ["mixed_surface_realism_gap"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )

    paths = select_next_tasks(
        root=tmp_path, count=2, now=NOW, loop_id="batch-diversity"
    )
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    history = json.loads(
        paths.history_path.read_text(encoding="utf-8").splitlines()[-1]
    )

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "worktree_risk-dirty-worktree",
        "coverage_gap-mixed-surface-benchmark-realism",
    ]
    assert history["selected_fallback_families"] == ["benchmark_expansion", "cleanup"]
    assert "commit_isolation_gap-foundation-order" in history["next_candidates"]


def test_select_next_keeps_same_fallback_family_when_no_alternative_exists(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "title": "Reduce dirty worktree integration risk",
                    "category": "worktree_risk",
                    "evidence": [
                        {"source": "git_status", "path": ".", "summary": "dirty"}
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 3,
                    "priority_score": 62,
                    "status": "open",
                    "recommendation": "reduce_integration_risk",
                    "signals": ["dirty_worktree_large"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
                {
                    "id": "commit_isolation_gap-foundation-order",
                    "title": "Isolate the foundation commit before later batches",
                    "category": "commit_isolation_gap",
                    "evidence": [
                        {
                            "source": "worktree_commit_plan",
                            "path": "docs/reports/worktree-commit-plan.md",
                            "summary": "commit order dependency remains",
                        }
                    ],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 4,
                    "priority_score": 61,
                    "status": "open",
                    "recommendation": "isolate_foundation_commit",
                    "signals": ["commit_order_dependency_exists"],
                    "first_seen_at": NOW,
                    "last_seen_at": NOW,
                    "recurrence_count": 1,
                },
            ],
        },
    )

    paths = select_next_tasks(
        root=tmp_path, count=2, now=NOW, loop_id="batch-same-family"
    )
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))

    assert [task["id"] for task in selected["selected_tasks"]] == [
        "worktree_risk-dirty-worktree",
        "commit_isolation_gap-foundation-order",
    ]


def test_self_inspection_derives_autonomy_selection_gap_from_repeated_fallback_family(
    tmp_path: Path,
) -> None:
    write_loop_history(
        tmp_path,
        [
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-1",
                "created_at": "2026-04-14T00:00:00Z",
                "selected_tasks": ["worktree_risk-dirty-worktree"],
                "selected_categories": ["worktree_risk"],
                "selected_fallback_families": ["cleanup"],
                "evidence_used": ["."],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "fallback_selected",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-2",
                "created_at": "2026-04-14T00:05:00Z",
                "selected_tasks": ["commit_isolation_gap-foundation-order"],
                "selected_categories": ["commit_isolation_gap"],
                "selected_fallback_families": ["cleanup"],
                "evidence_used": ["docs/reports/worktree-commit-plan.md"],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "fallback_selected",
            },
            {
                "kind": "qa_z.loop_history_entry",
                "schema_version": 1,
                "loop_id": "loop-3",
                "created_at": "2026-04-14T00:10:00Z",
                "selected_tasks": ["evidence_freshness_gap-generated-artifacts"],
                "selected_categories": ["evidence_freshness_gap"],
                "selected_fallback_families": ["cleanup"],
                "evidence_used": ["benchmarks/results/summary.json"],
                "resulting_session_id": None,
                "verify_verdict": None,
                "benchmark_delta": None,
                "next_candidates": [],
                "state": "fallback_selected",
            },
        ],
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="family-history-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))

    candidate = next(
        item
        for item in report["candidates"]
        if item["id"] == "autonomy_selection_gap-repeated-fallback-cleanup"
    )

    assert candidate["category"] == "autonomy_selection_gap"
    assert candidate["recommendation"] == "improve_fallback_diversity"
    assert "recent_fallback_family_repeat" in candidate["signals"]
