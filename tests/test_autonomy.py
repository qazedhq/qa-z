"""Tests for deterministic autonomy workflow loops."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import yaml

from qa_z.autonomy import (
    action_for_task,
    load_autonomy_status,
    render_autonomy_loop_plan,
    render_autonomy_summary,
    render_autonomy_status,
    run_autonomy,
)
from qa_z.cli import main
from qa_z.config import load_config


NOW = "2026-04-15T00:00:00Z"


class FakeClock:
    """Deterministic monotonic clock for runtime-budget tests."""

    def __init__(self) -> None:
        self.current = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        """Return the current monotonic time."""
        return self.current

    def sleep(self, seconds: float) -> None:
        """Advance time instead of sleeping."""
        self.sleeps.append(seconds)
        self.current += seconds


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write a deterministic JSON object fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_report(tmp_path: Path, name: str, body: str) -> None:
    """Write a deterministic report fixture."""
    path = tmp_path / "docs" / "reports" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body.strip() + "\n", encoding="utf-8")


def stub_live_repository_signals(monkeypatch, **signals: object) -> None:
    """Patch live repository signal collection for deterministic autonomy tests."""

    def fake_signals(_root: Path) -> dict[str, object]:
        return dict(signals)

    monkeypatch.setattr(
        "qa_z.self_improvement.collect_live_repository_signals",
        fake_signals,
    )


def write_config(tmp_path: Path) -> None:
    """Write a minimal QA-Z config for autonomy tests."""
    config = {
        "project": {"name": "qa-z-autonomy-test", "languages": ["python"]},
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "fail_on_missing_tool": True,
            "checks": [
                {
                    "id": "py_test",
                    "run": [sys.executable, "-c", ""],
                    "kind": "test",
                }
            ],
        },
        "deep": {"checks": []},
    }
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(config, sort_keys=False), encoding="utf-8"
    )


def write_contract(tmp_path: Path) -> None:
    """Write a contract that repair-session creation can resolve."""
    path = tmp_path / "qa" / "contracts" / "contract.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        dedent(
            """
            ---
            title: Autonomy repair contract
            summary: Restore deterministic QA evidence.
            constraints:
              - Keep autonomy planning local.
            ---
            # QA Contract: Autonomy repair contract

            ## Acceptance Checks

            - The candidate run no longer regresses deterministic evidence.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_fast_summary(
    tmp_path: Path,
    run_id: str,
    *,
    status: str,
    exit_code: int | None,
) -> None:
    """Write a compact fast run summary."""
    fast_dir = tmp_path / ".qa-z" / "runs" / run_id / "fast"
    fast_dir.mkdir(parents=True, exist_ok=True)
    write_json(
        fast_dir / "summary.json",
        {
            "schema_version": 2,
            "mode": "fast",
            "contract_path": "qa/contracts/contract.md",
            "project_root": str(tmp_path),
            "status": "failed" if status in {"failed", "error"} else "passed",
            "started_at": "2026-04-14T00:00:00Z",
            "finished_at": "2026-04-14T00:00:01Z",
            "artifact_dir": f".qa-z/runs/{run_id}/fast",
            "checks": [
                {
                    "id": "py_test",
                    "tool": "pytest",
                    "command": ["pytest"],
                    "kind": "test",
                    "status": status,
                    "exit_code": exit_code,
                    "duration_ms": 1,
                    "stdout_tail": "",
                    "stderr_tail": "",
                }
            ],
        },
    )


def write_benchmark_summary(tmp_path: Path) -> None:
    """Seed a benchmark summary with one failed fixture."""
    write_json(
        tmp_path / "benchmarks" / "results" / "summary.json",
        {
            "kind": "qa_z.benchmark_summary",
            "schema_version": 1,
            "fixtures_total": 1,
            "fixtures_passed": 0,
            "fixtures_failed": 1,
            "overall_rate": 0.0,
            "failed_fixtures": ["py_type_error"],
            "category_rates": {},
            "fixtures": [
                {
                    "name": "py_type_error",
                    "passed": False,
                    "failures": ["fast.failed_checks missing expected values"],
                    "categories": {"detection": False},
                    "actual": {},
                    "artifacts": {"fast_summary": "work/py_type_error/summary.json"},
                }
            ],
        },
    )


def write_regressed_verify_artifacts(tmp_path: Path) -> None:
    """Seed verification artifacts that identify a baseline run for repair."""
    verify_dir = tmp_path / ".qa-z" / "runs" / "candidate" / "verify"
    write_json(
        verify_dir / "summary.json",
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
    write_json(
        verify_dir / "compare.json",
        {
            "kind": "qa_z.verify_compare",
            "schema_version": 1,
            "baseline_run_id": "baseline",
            "candidate_run_id": "candidate",
            "baseline": {
                "run_dir": ".qa-z/runs/baseline",
                "fast_status": "passed",
                "deep_status": None,
            },
            "candidate": {
                "run_dir": ".qa-z/runs/candidate",
                "fast_status": "failed",
                "deep_status": None,
            },
            "verdict": "regressed",
            "fast_checks": {},
            "deep_findings": {},
            "summary": {"regression_count": 1},
        },
    )


def test_autonomy_one_loop_writes_per_loop_latest_outcome_and_history(
    tmp_path: Path,
) -> None:
    write_benchmark_summary(tmp_path)

    summary = run_autonomy(root=tmp_path, loops=1, count=2, now=NOW)

    loop_id = "loop-20260415-000000-01"
    loop_dir = tmp_path / ".qa-z" / "loops" / loop_id
    latest_dir = tmp_path / ".qa-z" / "loops" / "latest"
    history_lines = (
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    outcome = json.loads((loop_dir / "outcome.json").read_text(encoding="utf-8"))
    latest_outcome = json.loads(
        (latest_dir / "outcome.json").read_text(encoding="utf-8")
    )
    history = json.loads(history_lines[0])

    assert summary["kind"] == "qa_z.autonomy_summary"
    assert summary["loops_requested"] == 1
    assert summary["loops_completed"] == 1
    assert summary["outcomes"][0]["loop_id"] == loop_id
    assert (loop_dir / "self_inspect.json").exists()
    assert (loop_dir / "selected_tasks.json").exists()
    assert (loop_dir / "loop_plan.md").exists()
    assert outcome["kind"] == "qa_z.autonomy_outcome"
    assert outcome["state"] == "completed"
    assert outcome["state_transitions"] == [
        "inspected",
        "selected",
        "awaiting_repair",
        "recorded",
        "completed",
    ]
    assert outcome["selected_task_ids"] == ["benchmark_gap-py_type_error"]
    assert outcome["actions_prepared"][0]["type"] == "benchmark_fixture_plan"
    assert latest_outcome == outcome
    assert history["loop_id"] == loop_id
    assert history["resulting_session_id"] is None
    assert history["outcome_path"] == f".qa-z/loops/{loop_id}/outcome.json"


def test_autonomy_multiple_loops_appends_history_and_keeps_distinct_directories(
    tmp_path: Path,
) -> None:
    write_benchmark_summary(tmp_path)

    summary = run_autonomy(root=tmp_path, loops=2, count=1, now=NOW)

    history_lines = (
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert summary["loops_completed"] == 2
    assert [outcome["loop_id"] for outcome in summary["outcomes"]] == [
        "loop-20260415-000000-01",
        "loop-20260415-000000-02",
    ]
    assert len(history_lines) == 2
    assert (tmp_path / ".qa-z" / "loops" / "loop-20260415-000000-01").is_dir()
    assert (tmp_path / ".qa-z" / "loops" / "loop-20260415-000000-02").is_dir()


def test_autonomy_runtime_budget_extends_loops_and_records_progress(
    tmp_path: Path,
) -> None:
    write_benchmark_summary(tmp_path)
    clock = FakeClock()

    summary = run_autonomy(
        root=tmp_path,
        loops=1,
        count=1,
        now=NOW,
        min_runtime_seconds=240,
        min_loop_seconds=120,
        monotonic=clock.monotonic,
        sleeper=clock.sleep,
    )

    latest_outcome = json.loads(
        (tmp_path / ".qa-z" / "loops" / "latest" / "outcome.json").read_text(
            encoding="utf-8"
        )
    )
    history_lines = (
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    first_history = json.loads(history_lines[0])
    second_history = json.loads(history_lines[1])
    first_outcome = summary["outcomes"][0]
    second_outcome = summary["outcomes"][1]

    assert summary["loops_requested"] == 1
    assert summary["loops_completed"] == 2
    assert summary["runtime_target_seconds"] == 240
    assert summary["runtime_elapsed_seconds"] == 240
    assert summary["runtime_remaining_seconds"] == 0
    assert summary["runtime_budget_met"] is True
    assert summary["min_loop_seconds"] == 120
    assert first_outcome["loop_elapsed_seconds"] == 120
    assert first_outcome["cumulative_elapsed_seconds"] == 120
    assert first_outcome["runtime_remaining_seconds"] == 120
    assert first_outcome["runtime_budget_met"] is False
    assert second_outcome["loop_elapsed_seconds"] == 120
    assert second_outcome["cumulative_elapsed_seconds"] == 240
    assert second_outcome["runtime_remaining_seconds"] == 0
    assert second_outcome["runtime_budget_met"] is True
    assert latest_outcome == second_outcome
    assert first_history["loop_elapsed_seconds"] == 120
    assert first_history["cumulative_elapsed_seconds"] == 120
    assert second_history["loop_elapsed_seconds"] == 120
    assert second_history["cumulative_elapsed_seconds"] == 240
    assert clock.sleeps == [120, 120]


def test_autonomy_empty_evidence_is_graceful(tmp_path: Path) -> None:
    summary = run_autonomy(root=tmp_path, loops=1, count=3, now=NOW)
    loop_dir = tmp_path / ".qa-z" / "loops" / "loop-20260415-000000-01"
    selected = json.loads(
        (loop_dir / "selected_tasks.json").read_text(encoding="utf-8")
    )
    outcome = json.loads((loop_dir / "outcome.json").read_text(encoding="utf-8"))
    plan = (loop_dir / "loop_plan.md").read_text(encoding="utf-8")

    assert summary["loops_completed"] == 1
    assert selected["selected_tasks"] == []
    assert outcome["state"] == "blocked_no_candidates"
    assert outcome["selection_gap_reason"] == "no_open_backlog_after_inspection"
    assert outcome["backlog_open_count_before_inspection"] == 0
    assert outcome["backlog_open_count_after_inspection"] == 0
    assert outcome["loop_health"]["classification"] == "taskless"
    assert outcome["loop_health"]["selected_count"] == 0
    assert outcome["loop_health"]["taskless"] is True
    assert outcome["loop_health"]["fallback_selected"] is False
    assert (
        outcome["loop_health"]["selection_gap_reason"]
        == "no_open_backlog_after_inspection"
    )
    assert outcome["loop_health"]["backlog_open_count_before_inspection"] == 0
    assert outcome["loop_health"]["backlog_open_count_after_inspection"] == 0
    assert outcome["loop_health"]["stale_open_items_closed"] == 0
    assert (
        "no open backlog items before inspection" in outcome["loop_health"]["summary"]
    )
    assert outcome["selected_task_ids"] == []
    assert outcome["actions_prepared"] == []
    assert outcome["next_recommendations"] == [
        "no evidence-backed fallback candidates available"
    ]
    assert "empty_backlog_detected" in outcome["state_transitions"]
    assert "blocked_no_candidates" in outcome["state_transitions"]
    assert "No open backlog tasks were selected." in plan
    assert "Selection gap reason: `no_open_backlog_after_inspection`" in plan
    assert "Loop health: `taskless`" in plan
    assert "no open backlog items before inspection" in plan


def test_autonomy_marks_stale_backlog_taskless_loop_as_blocked(tmp_path: Path) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": NOW,
            "items": [
                {
                    "id": "docs_drift-current_truth_sync",
                    "title": "Run a current-truth docs and schema sync audit",
                    "category": "docs_drift",
                    "evidence": [
                        {
                            "source": "current_state",
                            "path": "docs/reports/current-state-analysis.md",
                            "summary": (
                                "report calls out current-truth drift or an explicit sync audit"
                            ),
                        }
                    ],
                    "impact": 2,
                    "likelihood": 3,
                    "confidence": 4,
                    "repair_cost": 2,
                    "priority_score": 26,
                    "recommendation": "sync_contract_and_docs",
                    "signals": ["schema_doc_drift"],
                    "status": "open",
                }
            ],
        },
    )

    summary = run_autonomy(root=tmp_path, loops=1, count=1, now=NOW)
    loop_dir = tmp_path / ".qa-z" / "loops" / "loop-20260415-000000-01"
    outcome = json.loads((loop_dir / "outcome.json").read_text(encoding="utf-8"))
    plan = (loop_dir / "loop_plan.md").read_text(encoding="utf-8")
    history = json.loads(
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    status = load_autonomy_status(tmp_path)

    assert summary["loops_completed"] == 1
    assert outcome["state"] == "blocked_no_candidates"
    assert outcome["selection_gap_reason"] == "no_open_backlog_after_inspection"
    assert outcome["backlog_open_count_before_inspection"] == 1
    assert outcome["backlog_open_count_after_inspection"] == 0
    assert outcome["loop_health"]["classification"] == "taskless"
    assert outcome["loop_health"]["stale_open_items_closed"] == 1
    assert "closed 1 stale open backlog item" in outcome["loop_health"]["summary"]
    assert "empty_backlog_detected" not in outcome["state_transitions"]
    assert "blocked_no_candidates" in outcome["state_transitions"]
    assert history["state"] == "blocked_no_candidates"
    assert history["selection_gap_reason"] == "no_open_backlog_after_inspection"
    assert history["backlog_open_count_before_inspection"] == 1
    assert history["backlog_open_count_after_inspection"] == 0
    assert history["loop_health"] == outcome["loop_health"]
    assert "Selection gap reason: `no_open_backlog_after_inspection`" in plan
    assert "Loop health: `taskless`" in plan
    assert status["latest_selection_gap_reason"] == "no_open_backlog_after_inspection"
    assert status["latest_backlog_open_count_before_inspection"] == 1
    assert status["latest_backlog_open_count_after_inspection"] == 0
    assert status["latest_loop_health"] == outcome["loop_health"]


def test_autonomy_reseeds_and_selects_fallback_task_when_backlog_is_empty(
    tmp_path: Path,
) -> None:
    write_report(
        tmp_path,
        "next-improvement-roadmap.md",
        """
        # QA-Z Next Improvement Roadmap

        ## Priority 3: Mixed-Surface Executed Benchmark Expansion

        Add realistic mixed-surface fixtures that exercise fast, deep, and
        repair-handoff behavior in one deterministic benchmark flow.
        """,
    )

    summary = run_autonomy(root=tmp_path, loops=1, count=1, now=NOW)
    loop_dir = tmp_path / ".qa-z" / "loops" / "loop-20260415-000000-01"
    selected = json.loads(
        (loop_dir / "selected_tasks.json").read_text(encoding="utf-8")
    )
    outcome = json.loads((loop_dir / "outcome.json").read_text(encoding="utf-8"))
    plan = (loop_dir / "loop_plan.md").read_text(encoding="utf-8")
    status = load_autonomy_status(tmp_path)
    history = json.loads(
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )

    assert summary["loops_completed"] == 1
    assert outcome["state"] == "fallback_selected"
    assert [task["id"] for task in selected["selected_tasks"]] == [
        "coverage_gap-mixed-surface-benchmark-realism"
    ]
    assert outcome["selected_task_ids"] == [
        "coverage_gap-mixed-surface-benchmark-realism"
    ]
    assert outcome["selected_fallback_families"] == ["benchmark_expansion"]
    assert outcome["actions_prepared"][0]["type"] == "benchmark_fixture_plan"
    assert status["latest_selected_fallback_families"] == ["benchmark_expansion"]
    assert "- Selected fallback families: `benchmark_expansion`" in plan
    assert "empty_backlog_detected" in outcome["state_transitions"]
    assert "reseeded" in outcome["state_transitions"]
    assert "fallback_selected" in outcome["state_transitions"]
    assert history["state"] == "fallback_selected"
    assert history["selected_fallback_families"] == ["benchmark_expansion"]


def test_autonomy_selects_worktree_cleanup_fallback_from_live_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=14,
        untracked_count=21,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=[
            "docs/reports/worktree-triage.md",
            "docs/reports/worktree-commit-plan.md",
        ],
        runtime_artifact_paths=[".qa-z/loops/latest/outcome.json"],
        benchmark_result_paths=["benchmarks/results/summary.json"],
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Deferred cleanup items remain open. Generated benchmark outputs should
        stay deferred until intentionally frozen evidence is defined.
        """,
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation.
        """,
    )

    summary = run_autonomy(root=tmp_path, loops=1, count=1, now=NOW)
    loop_dir = tmp_path / ".qa-z" / "loops" / "loop-20260415-000000-01"
    outcome = json.loads((loop_dir / "outcome.json").read_text(encoding="utf-8"))
    selected = json.loads(
        (loop_dir / "selected_tasks.json").read_text(encoding="utf-8")
    )
    history = json.loads(
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )

    assert summary["loops_completed"] == 1
    assert outcome["state"] == "fallback_selected"
    assert selected["selected_tasks"][0]["category"] in {
        "worktree_risk",
        "commit_isolation_gap",
        "deferred_cleanup_gap",
    }
    assert outcome["selected_fallback_families"] == ["cleanup"]
    assert outcome["actions_prepared"][0]["type"] == "integration_cleanup_plan"
    assert history["selected_tasks"] == [selected["selected_tasks"][0]["id"]]
    assert history["state"] == "fallback_selected"
    assert history["selected_fallback_families"] == ["cleanup"]


def test_autonomy_stops_after_repeated_blocked_no_candidate_loops(
    tmp_path: Path,
) -> None:
    clock = FakeClock()

    summary = run_autonomy(
        root=tmp_path,
        loops=1,
        count=1,
        now=NOW,
        min_runtime_seconds=600,
        min_loop_seconds=120,
        monotonic=clock.monotonic,
        sleeper=clock.sleep,
    )

    history_lines = (
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert summary["loops_completed"] == 2
    assert summary["runtime_budget_met"] is False
    assert summary["stop_reason"] == "repeated_blocked_no_candidates"
    assert summary["consecutive_blocked_loops"] == 2
    assert [outcome["state"] for outcome in summary["outcomes"]] == [
        "blocked_no_candidates",
        "blocked_no_candidates",
    ]
    assert [json.loads(line)["state"] for line in history_lines] == [
        "blocked_no_candidates",
        "blocked_no_candidates",
    ]
    assert clock.sleeps == [120, 120]


def test_load_autonomy_status_reports_runtime_progress(tmp_path: Path) -> None:
    write_benchmark_summary(tmp_path)
    clock = FakeClock()
    run_autonomy(
        root=tmp_path,
        loops=1,
        count=1,
        now=NOW,
        min_runtime_seconds=120,
        min_loop_seconds=120,
        monotonic=clock.monotonic,
        sleeper=clock.sleep,
    )

    status = load_autonomy_status(tmp_path)

    assert status["runtime_target_seconds"] == 120
    assert status["runtime_elapsed_seconds"] == 120
    assert status["runtime_remaining_seconds"] == 0
    assert status["runtime_budget_met"] is True
    assert status["latest_loop_elapsed_seconds"] == 120
    assert status["min_loop_seconds"] == 120


def test_action_mapping_is_grounded_by_task_category(tmp_path: Path) -> None:
    assert (
        action_for_task(
            root=tmp_path,
            config=None,
            loop_id="loop-one",
            task={
                "id": "benchmark_gap-py_type_error",
                "category": "benchmark_gap",
                "recommendation": "add_benchmark_fixture",
                "evidence": [],
            },
        )["type"]
        == "benchmark_fixture_plan"
    )
    assert (
        action_for_task(
            root=tmp_path,
            config=None,
            loop_id="loop-one",
            task={
                "id": "policy_gap-semgrep",
                "category": "policy_gap",
                "recommendation": "add_policy_fixture",
                "evidence": [],
            },
        )["type"]
        == "policy_fixture_plan"
    )
    assert (
        action_for_task(
            root=tmp_path,
            config=None,
            loop_id="loop-one",
            task={
                "id": "docs_drift-self_improvement_commands",
                "category": "docs_drift",
                "recommendation": "sync_contract_and_docs",
                "evidence": [],
            },
        )["type"]
        == "docs_sync_plan"
    )
    assert (
        action_for_task(
            root=tmp_path,
            config=None,
            loop_id="loop-one",
            task={
                "id": "session_gap-existing",
                "category": "session_gap",
                "recommendation": "create_repair_session",
                "evidence": [
                    {
                        "source": "repair_session",
                        "path": ".qa-z/sessions/session-one/session.json",
                    }
                ],
            },
        )["type"]
        == "repair_session_followup"
    )
    blocked_action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "workflow_gap-session-blocked-history",
            "category": "workflow_gap",
            "recommendation": "audit_executor_contract",
            "signals": ["executor_dry_run_blocked", "service_readiness_gap"],
            "evidence": [
                {
                    "source": "executor_result_dry_run",
                    "path": ".qa-z/sessions/session-blocked/executor_results/dry_run_summary.json",
                }
            ],
        },
    )
    assert blocked_action["type"] == "executor_safety_review_plan"
    assert (
        "python -m qa_z executor-result dry-run --session session-blocked"
        in blocked_action["commands"]
    )
    attention_action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "no_op_safeguard_gap-session-noop-history",
            "category": "no_op_safeguard_gap",
            "recommendation": "harden_executor_no_op_safeguards",
            "signals": ["executor_dry_run_attention", "executor_result_no_op"],
            "evidence": [
                {
                    "source": "executor_result_dry_run",
                    "path": ".qa-z/sessions/session-noop/executor_results/dry_run_summary.json",
                }
            ],
        },
    )
    assert attention_action["type"] == "executor_safety_followup_plan"
    assert (
        "python -m qa_z executor-result dry-run --session session-noop"
        in attention_action["commands"]
    )


def test_action_mapping_loop_health_plan_includes_task_context_paths(
    tmp_path: Path,
) -> None:
    action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "autonomy_selection_gap-repeated-fallback-cleanup",
            "category": "autonomy_selection_gap",
            "recommendation": "improve_fallback_diversity",
            "signals": ["recent_fallback_family_repeat"],
            "evidence": [
                {
                    "source": "loop_history",
                    "path": ".qa-z/loops/history.jsonl",
                    "summary": (
                        "recent_fallback_family=cleanup; loops=3; "
                        "states=unknown, completed, unknown"
                    ),
                }
            ],
        },
    )

    assert action["type"] == "loop_health_plan"
    assert action["commands"] == [
        "python -m qa_z self-inspect",
        "python -m qa_z autonomy --loops 1",
    ]
    assert action["context_paths"] == [".qa-z/loops/history.jsonl"]
    assert action["next_recommendation"] == (
        "rerun autonomy after tightening loop health rules"
    )


def test_action_mapping_specializes_cleanup_packets_by_recommendation(
    tmp_path: Path,
) -> None:
    cleanup_action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "worktree_risk-dirty-worktree",
            "category": "worktree_risk",
            "recommendation": "reduce_integration_risk",
            "signals": ["dirty_worktree_large", "worktree_integration_risk"],
            "evidence": [
                {
                    "source": "git_status",
                    "path": ".",
                    "summary": "modified=25; untracked=344; staged=0",
                }
            ],
        },
    )
    isolation_action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "commit_isolation_gap-foundation-order",
            "category": "commit_isolation_gap",
            "recommendation": "isolate_foundation_commit",
            "signals": ["commit_order_dependency_exists"],
            "evidence": [
                {
                    "source": "worktree_commit_plan",
                    "path": "docs/reports/worktree-commit-plan.md",
                    "summary": "corrected commit order still requires isolation",
                }
            ],
        },
    )

    assert cleanup_action["type"] == "integration_cleanup_plan"
    assert cleanup_action["commands"] == [
        "git status --short",
        "python -m qa_z backlog --json",
        "python -m qa_z self-inspect --json",
    ]
    assert cleanup_action["context_paths"] == ["docs/reports/worktree-triage.md"]
    assert cleanup_action["next_recommendation"] == (
        "reduce dirty worktree integration risk and rerun self-inspection"
    )
    assert isolation_action["type"] == "integration_cleanup_plan"
    assert isolation_action["context_paths"] == ["docs/reports/worktree-commit-plan.md"]
    assert isolation_action["next_recommendation"] == (
        "isolate the foundation commit before rerunning self-inspection"
    )


def test_deferred_cleanup_action_includes_generated_policy_context_path(
    tmp_path: Path,
) -> None:
    action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "deferred_cleanup_gap-worktree-deferred-items",
            "category": "deferred_cleanup_gap",
            "recommendation": "triage_and_isolate_changes",
            "signals": ["deferred_cleanup_items_open"],
            "evidence": [
                {
                    "source": "current_state",
                    "path": "docs/reports/current-state-analysis.md",
                    "summary": (
                        "report calls out deferred cleanup work or generated "
                        "outputs to isolate"
                    ),
                },
                {
                    "source": "generated_outputs",
                    "path": "benchmarks/results/report.md",
                    "summary": "generated benchmark outputs still present",
                },
            ],
        },
    )

    assert action["type"] == "integration_cleanup_plan"
    assert action["context_paths"] == [
        "benchmarks/results/report.md",
        "docs/generated-vs-frozen-evidence-policy.md",
        "docs/reports/current-state-analysis.md",
        "docs/reports/worktree-commit-plan.md",
        "docs/reports/worktree-triage.md",
    ]
    assert action["next_recommendation"] == (
        "triage and isolate worktree changes before rerunning self-inspection"
    )


def test_action_mapping_specializes_integration_gap_packets_from_reports(
    tmp_path: Path,
) -> None:
    action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "integration_gap-worktree-integration-risk",
            "category": "integration_gap",
            "recommendation": "audit_worktree_integration",
            "signals": ["worktree_integration_risk"],
            "evidence": [
                {
                    "source": "current_state",
                    "path": "docs/reports/current-state-analysis.md",
                    "summary": "report calls out worktree integration risk",
                },
                {
                    "source": "worktree_triage",
                    "path": "docs/reports/worktree-triage.md",
                    "summary": "report calls out commit split risk",
                },
                {
                    "source": "worktree_commit_plan",
                    "path": "docs/reports/worktree-commit-plan.md",
                    "summary": "report calls out commit order dependency",
                },
            ],
        },
    )

    assert action["type"] == "workflow_gap_plan"
    assert action["commands"] == [
        "git status --short",
        "python -m qa_z backlog --json",
        "python -m qa_z self-inspect --json",
    ]
    assert action["context_paths"] == [
        "docs/reports/current-state-analysis.md",
        "docs/reports/worktree-commit-plan.md",
        "docs/reports/worktree-triage.md",
    ]
    assert action["next_recommendation"] == (
        "audit worktree integration evidence and rerun self-inspection"
    )


def test_render_autonomy_loop_plan_includes_action_context_paths() -> None:
    plan = render_autonomy_loop_plan(
        loop_id="loop-one",
        generated_at=NOW,
        selected_tasks=[
            {
                "id": "worktree_risk-dirty-worktree",
                "title": "Reduce dirty worktree integration risk",
                "category": "worktree_risk",
                "recommendation": "reduce_integration_risk",
                "priority_score": 65,
            }
        ],
        actions=[
            {
                "type": "integration_cleanup_plan",
                "task_id": "worktree_risk-dirty-worktree",
                "title": "Prepare a deterministic cleanup and integration-risk reduction plan.",
                "next_recommendation": "reduce dirty worktree integration risk and rerun self-inspection",
                "commands": [
                    "git status --short",
                    "python -m qa_z backlog --json",
                ],
                "context_paths": ["docs/reports/worktree-triage.md"],
            }
        ],
    )

    assert "context:" in plan
    assert "`docs/reports/worktree-triage.md`" in plan


def test_render_autonomy_loop_plan_preserves_selection_penalty_residue() -> None:
    plan = render_autonomy_loop_plan(
        loop_id="loop-penalty",
        generated_at=NOW,
        selected_tasks=[
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
            }
        ],
        actions=[],
    )

    assert "selection score: 60" in plan
    assert (
        "selection penalty: 5 (`recent_task_reselected`, "
        "`recent_category_reselected`)" in plan
    )


def test_render_autonomy_loop_plan_includes_selected_task_evidence() -> None:
    plan = render_autonomy_loop_plan(
        loop_id="loop-evidence",
        generated_at=NOW,
        selected_tasks=[
            {
                "id": "integration_gap-worktree-integration-risk",
                "title": "Audit worktree integration and commit-split risk",
                "category": "integration_gap",
                "recommendation": "audit_worktree_integration",
                "priority_score": 24,
                "evidence": [
                    {
                        "source": "current_state",
                        "path": "docs/reports/current-state-analysis.md",
                        "summary": (
                            "report calls out worktree integration or commit-split risk"
                        ),
                    }
                ],
            }
        ],
        actions=[],
    )

    assert "evidence:" in plan
    assert (
        "current_state: `docs/reports/current-state-analysis.md` "
        "report calls out worktree integration or commit-split risk" in plan
    )


def test_autonomy_prepares_repair_session_for_verify_regression(
    tmp_path: Path,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_fast_summary(tmp_path, "candidate", status="passed", exit_code=0)
    write_regressed_verify_artifacts(tmp_path)
    config = load_config(tmp_path)

    summary = run_autonomy(root=tmp_path, config=config, loops=1, count=1, now=NOW)

    loop_id = "loop-20260415-000000-01"
    outcome = json.loads(
        (tmp_path / ".qa-z" / "loops" / loop_id / "outcome.json").read_text(
            encoding="utf-8"
        )
    )
    action = outcome["actions_prepared"][0]
    session_id = f"{loop_id}-verify_regression-candidate"
    session_dir = tmp_path / ".qa-z" / "sessions" / session_id

    assert summary["created_session_ids"] == [session_id]
    assert action["type"] == "repair_session"
    assert action["session_id"] == session_id
    assert action["baseline_run"] == ".qa-z/runs/baseline"
    assert outcome["state_transitions"] == [
        "inspected",
        "selected",
        "verification_observed",
        "session_prepared",
        "awaiting_repair",
        "recorded",
        "completed",
    ]
    assert outcome["verification_evidence"][0]["verdict"] == "regressed"
    assert (session_dir / "session.json").exists()
    assert (session_dir / "executor_guide.md").exists()
    assert (
        json.loads((session_dir / "session.json").read_text(encoding="utf-8"))["state"]
        == "waiting_for_external_repair"
    )
    history = json.loads(
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )
    assert history["verify_verdict"] == "regressed"


def test_autonomy_prepares_repair_session_with_context_paths(
    tmp_path: Path,
) -> None:
    write_config(tmp_path)
    write_contract(tmp_path)
    write_fast_summary(tmp_path, "baseline", status="failed", exit_code=1)
    write_fast_summary(tmp_path, "candidate", status="passed", exit_code=0)
    write_regressed_verify_artifacts(tmp_path)
    config = load_config(tmp_path)

    run_autonomy(root=tmp_path, config=config, loops=1, count=1, now=NOW)

    loop_id = "loop-20260415-000000-01"
    outcome = json.loads(
        (tmp_path / ".qa-z" / "loops" / loop_id / "outcome.json").read_text(
            encoding="utf-8"
        )
    )
    action = outcome["actions_prepared"][0]

    assert action["type"] == "repair_session"
    assert action["context_paths"] == [".qa-z/runs/candidate/verify/summary.json"]


def test_autonomy_cli_run_and_status(tmp_path: Path, capsys, monkeypatch) -> None:
    write_benchmark_summary(tmp_path)
    clock = FakeClock()
    monkeypatch.setattr("qa_z.autonomy.time.monotonic", clock.monotonic)
    monkeypatch.setattr("qa_z.autonomy.time.sleep", clock.sleep)

    exit_code = main(
        [
            "autonomy",
            "--path",
            str(tmp_path),
            "--loops",
            "1",
            "--count",
            "1",
            "--min-runtime-hours",
            "0.001",
            "--min-loop-seconds",
            "2",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)
    status_exit = main(["autonomy", "status", "--path", str(tmp_path), "--json"])
    status = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output["kind"] == "qa_z.autonomy_summary"
    assert output["runtime_target_seconds"] == 4
    assert output["runtime_elapsed_seconds"] == 4
    assert output["min_loop_seconds"] == 2
    assert output["loops_completed"] == 2
    assert output["latest_loop_id"] == "loop-20260415-000000-01" or output[
        "latest_loop_id"
    ].startswith("loop-")
    assert status_exit == 0
    assert status["kind"] == "qa_z.autonomy_status"
    assert status["latest_loop_id"] == output["latest_loop_id"]
    assert status["latest_selected_tasks"] == ["benchmark_gap-py_type_error"]
    assert status["latest_selected_task_details"][0]["title"] == (
        "Fix benchmark fixture failure: py_type_error"
    )
    assert status["latest_selected_task_details"][0]["recommendation"] == (
        "add_benchmark_fixture"
    )
    assert "selection_penalty" in status["latest_selected_task_details"][0]
    assert status["latest_prepared_actions"][0]["type"] == "benchmark_fixture_plan"
    assert status["latest_next_recommendations"] == [
        "run qa-z benchmark after fixture updates"
    ]
    assert (
        status["backlog_top_items"][0]["title"]
        == "Fix benchmark fixture failure: py_type_error"
    )
    assert status["backlog_top_items"][0]["recommendation"] == "add_benchmark_fixture"
    assert "benchmark" in status["backlog_top_items"][0]["evidence_summary"]
    assert status["runtime_target_seconds"] == 4
    assert status["runtime_elapsed_seconds"] == 4
    assert status["runtime_budget_met"] is True


def test_load_autonomy_status_without_previous_loop(tmp_path: Path) -> None:
    status = load_autonomy_status(tmp_path)

    assert status["kind"] == "qa_z.autonomy_status"
    assert status["latest_loop_id"] is None
    assert status["latest_selected_tasks"] == []
    assert status["latest_selected_task_details"] == []
    assert status["latest_prepared_actions"] == []
    assert status["latest_next_recommendations"] == []
    assert status["open_session_count"] == 0


def test_render_autonomy_status_surfaces_prepared_actions_and_context_paths() -> None:
    output = render_autonomy_status(
        {
            "latest_state": "completed",
            "latest_loop_id": "loop-one",
            "latest_selected_tasks": [
                "worktree_risk-dirty-worktree",
                "integration_gap-worktree-integration-risk",
            ],
            "latest_selected_fallback_families": ["cleanup"],
            "runtime_elapsed_seconds": 1,
            "runtime_target_seconds": 0,
            "runtime_budget_met": True,
            "min_loop_seconds": 0,
            "open_session_count": 0,
            "recent_verify_verdict": None,
            "latest_prepared_actions": [
                {
                    "type": "integration_cleanup_plan",
                    "task_id": "worktree_risk-dirty-worktree",
                    "next_recommendation": (
                        "reduce dirty worktree integration risk and rerun "
                        "self-inspection"
                    ),
                    "commands": [
                        "git status --short",
                        "python -m qa_z backlog --json",
                    ],
                    "context_paths": ["docs/reports/worktree-triage.md"],
                }
            ],
            "latest_next_recommendations": [
                "reduce dirty worktree integration risk and rerun self-inspection"
            ],
            "backlog_top_items": [],
        }
    )

    assert "Prepared actions:" in output
    assert "Runtime: 1 seconds elapsed (no minimum budget)" in output
    assert "Selected fallback families: cleanup" in output
    assert "integration_cleanup_plan for worktree_risk-dirty-worktree" in output
    assert "commands: git status --short; python -m qa_z backlog --json" in output
    assert "context: docs/reports/worktree-triage.md" in output


def test_render_autonomy_loop_plan_includes_selected_fallback_families() -> None:
    plan = render_autonomy_loop_plan(
        loop_id="loop-fallback-family",
        generated_at=NOW,
        selected_tasks=[
            {
                "id": "worktree_risk-dirty-worktree",
                "title": "Reduce dirty worktree integration risk",
                "category": "worktree_risk",
                "recommendation": "reduce_integration_risk",
                "priority_score": 65,
            }
        ],
        actions=[],
        selected_fallback_families=["cleanup"],
    )

    assert "- Selected fallback families: `cleanup`" in plan


def test_render_autonomy_status_shows_next_recommendations_without_actions() -> None:
    output = render_autonomy_status(
        {
            "latest_state": "blocked_no_candidates",
            "latest_loop_id": "loop-empty",
            "latest_selected_tasks": [],
            "runtime_elapsed_seconds": 0,
            "runtime_target_seconds": 0,
            "runtime_budget_met": True,
            "min_loop_seconds": 0,
            "open_session_count": 0,
            "recent_verify_verdict": None,
            "latest_selection_gap_reason": "no_open_backlog_after_inspection",
            "latest_backlog_open_count_before_inspection": 1,
            "latest_backlog_open_count_after_inspection": 0,
            "latest_loop_health": {
                "classification": "taskless",
                "selected_count": 0,
                "taskless": True,
                "fallback_selected": False,
                "selection_gap_reason": "no_open_backlog_after_inspection",
                "backlog_open_count_before_inspection": 1,
                "backlog_open_count_after_inspection": 0,
                "stale_open_items_closed": 1,
                "summary": (
                    "self-inspection closed 1 stale open backlog item; no "
                    "replacement fallback candidates were selected"
                ),
            },
            "latest_prepared_actions": [],
            "latest_next_recommendations": [
                "no evidence-backed fallback candidates available"
            ],
            "backlog_top_items": [],
        }
    )

    assert "Prepared actions:\n- none" in output
    assert "Next recommendations:" in output
    assert "Loop health: taskless" in output
    assert (
        "Loop health summary: self-inspection closed 1 stale open backlog item"
        in output
    )
    assert "Selection gap reason: no_open_backlog_after_inspection" in output
    assert "Open backlog count: 1 before inspection, 0 after inspection" in output
    assert "- no evidence-backed fallback candidates available" in output


def test_render_autonomy_status_shows_open_sessions_and_backlog_details() -> None:
    output = render_autonomy_status(
        {
            "latest_state": "completed",
            "latest_loop_id": "loop-two",
            "latest_selected_tasks": ["session_gap-existing"],
            "latest_selected_task_details": [
                {
                    "id": "session_gap-existing",
                    "title": "Resume existing repair session",
                    "category": "session_gap",
                    "recommendation": "create_repair_session",
                    "selection_priority_score": 40,
                    "selection_penalty": 2,
                    "selection_penalty_reasons": [
                        "recent_category_reselected",
                        "recent_fallback_family_reselected",
                    ],
                    "evidence_summary": (
                        "repair_session: state=waiting_for_external_repair"
                    ),
                }
            ],
            "runtime_elapsed_seconds": 3,
            "runtime_target_seconds": 10,
            "runtime_budget_met": False,
            "min_loop_seconds": 2,
            "open_session_count": 1,
            "open_sessions": [
                {
                    "session_id": "session-one",
                    "state": "waiting_for_external_repair",
                    "session_dir": ".qa-z/sessions/session-one",
                }
            ],
            "recent_verify_verdict": "mixed",
            "latest_prepared_actions": [],
            "latest_next_recommendations": [],
            "backlog_top_items": [
                {
                    "id": "worktree_risk-dirty-worktree",
                    "category": "worktree_risk",
                    "priority_score": 65,
                    "status": "open",
                    "title": "Reduce dirty worktree integration risk",
                    "recommendation": "reduce_integration_risk",
                    "evidence_summary": (
                        "git_status: modified=25; untracked=346; staged=0"
                    ),
                }
            ],
        }
    )

    assert "Open session details:" in output
    assert (
        "- session-one: waiting_for_external_repair (.qa-z/sessions/session-one)"
        in output
    )
    assert "Selected task details:" in output
    assert "- session_gap-existing: Resume existing repair session" in output
    assert "recommendation: create_repair_session" in output
    assert "selection score: 40" in output
    assert (
        "selection penalty: 2 (recent_category_reselected, "
        "recent_fallback_family_reselected)" in output
    )
    assert "title: Reduce dirty worktree integration risk" in output
    assert "next: reduce_integration_risk" in output
    assert "evidence: git_status: modified=25; untracked=346; staged=0" in output


def test_render_autonomy_summary_uses_explicit_no_budget_runtime_text(
    tmp_path: Path,
) -> None:
    output = render_autonomy_summary(
        {
            "loops_requested": 1,
            "loops_completed": 1,
            "latest_loop_id": "loop-runtime",
            "runtime_elapsed_seconds": 2,
            "runtime_target_seconds": 0,
            "min_loop_seconds": 0,
            "created_session_ids": [],
        },
        tmp_path,
    )

    assert "Runtime: 2 seconds elapsed (no minimum budget)" in output
