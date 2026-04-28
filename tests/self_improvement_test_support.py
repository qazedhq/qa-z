"""Shared fixture writers for self-improvement test modules."""

from __future__ import annotations

import json
from pathlib import Path


def assert_mapping_contains(
    actual: dict[str, object], expected: dict[str, object]
) -> None:
    """Assert that a mapping contains the expected key/value pairs."""
    for key, value in expected.items():
        assert actual[key] == value


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

        Root `.qa-z/**` artifacts are local-only runtime artifacts.
        `.mypy_cache_safe/**`, `.ruff_cache_safe/**`, literal `%TEMP%/**`,
        root `/tmp_*` scratch roots, and `/benchmarks/minlock-*` benchmark
        lock probes are local-only runtime artifacts.
        `benchmarks/results/work/**` is disposable benchmark scratch output.
        `benchmarks/results-*` is local-by-default benchmark evidence unless
        intentionally frozen as evidence with surrounding documentation.
        `benchmarks/results/summary.json` and `benchmarks/results/report.md`
        are local-by-default benchmark evidence and may be committed only as
        intentional frozen evidence with surrounding documentation.
        `benchmarks/fixtures/**/repo/.qa-z/**` is allowed as fixture-local
        deterministic benchmark input.
        """.strip()
        + "\n",
        encoding="utf-8",
    )


def write_generated_artifact_gitignore(root: Path) -> None:
    """Write the standard generated-artifact ignore rules used by self-improvement tests."""
    write_gitignore(
        root,
        [
            ".qa-z/",
            ".mypy_cache_safe/",
            ".ruff_cache_safe/",
            "%TEMP%/",
            "/tmp_*",
            "/benchmarks/minlock-*",
            "!benchmarks/fixtures/**/repo/.qa-z/",
            "!benchmarks/fixtures/**/repo/.qa-z/**",
            "benchmarks/results/work/",
            "benchmarks/results-*",
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )


def write_loop_history(root: Path, entries: list[dict[str, object]]) -> None:
    """Write deterministic loop history entries."""
    path = root / ".qa-z" / "loops" / "history.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(entry, sort_keys=True) for entry in entries) + "\n",
        encoding="utf-8",
    )


def write_executor_result_session(
    root: Path,
    *,
    session_id: str,
    state: str,
    result_status: str,
    validation_status: str,
    verification_hint: str,
    now: str = "2026-04-15T00:00:00Z",
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
            "created_at": now,
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
            "created_at": now,
            "updated_at": now,
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
    now: str = "2026-04-15T00:00:00Z",
) -> None:
    """Seed a session-scoped executor-result history artifact."""
    write_json(
        root / ".qa-z" / "sessions" / session_id / "executor_results" / "history.json",
        {
            "kind": "qa_z.executor_result_history",
            "schema_version": 1,
            "session_id": session_id,
            "updated_at": now,
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


def write_fixture_index(root: Path, names: list[str]) -> None:
    """Seed benchmark fixture expected.json files with the given names."""
    for name in names:
        write_fixture_expectation(
            root,
            name,
            {"name": name, "run": {"fast": True}, "expect_fast": {"status": "failed"}},
        )


def write_fixture_expectation(
    root: Path, name: str, payload: dict[str, object]
) -> None:
    """Seed one benchmark fixture expected.json payload."""
    write_json(root / "benchmarks" / "fixtures" / name / "expected.json", payload)


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


def stub_live_repository_signals(monkeypatch, **signals: object) -> None:
    """Patch live repository signal collection for deterministic tests."""

    def fake_signals(_root: Path) -> dict[str, object]:
        return dict(signals)

    monkeypatch.setattr(
        "qa_z.self_improvement.collect_live_repository_signals",
        fake_signals,
    )


__all__ = [
    "assert_mapping_contains",
    "stub_live_repository_signals",
    "write_aggregate_only_failed_benchmark_summary",
    "write_generated_artifact_gitignore",
    "write_benchmark_summary",
    "write_executor_dry_run_summary",
    "write_executor_ingest_record",
    "write_executor_result_history",
    "write_executor_result_session",
    "write_fixture_expectation",
    "write_fixture_index",
    "write_generated_evidence_policy",
    "write_gitignore",
    "write_incomplete_session",
    "write_json",
    "write_legacy_benchmark_summary_without_snapshot",
    "write_loop_history",
    "write_regressed_verify_summary",
    "write_report",
]
