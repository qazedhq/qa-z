"""Tests for deterministic autonomy planning loops."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.autonomy import (
    action_for_task,
    load_autonomy_status,
    render_autonomy_status,
    run_autonomy,
)
from qa_z.cli import main

NOW = "2026-04-15T00:00:00Z"


class FakeClock:
    """Deterministic monotonic clock for runtime-budget tests."""

    def __init__(self) -> None:
        self.current = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.current

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.current += seconds


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_benchmark_summary(tmp_path: Path) -> None:
    write_json(
        tmp_path / "benchmarks" / "results" / "summary.json",
        {
            "kind": "qa_z.benchmark_summary",
            "schema_version": 1,
            "fixtures_total": 1,
            "fixtures_passed": 0,
            "fixtures_failed": 1,
            "overall_rate": 0.0,
            "snapshot": "0/1 fixtures, overall_rate 0.0",
            "failed_fixtures": ["py_type_error"],
            "fixtures": [
                {
                    "name": "py_type_error",
                    "passed": False,
                    "failures": ["fast.failed_checks missing expected values"],
                    "categories": ["detection"],
                    "actual": {},
                    "artifacts": [],
                }
            ],
        },
    )


def write_verify_summary(tmp_path: Path) -> None:
    write_json(
        tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "summary.json",
        {
            "kind": "qa_z.verify_summary",
            "schema_version": 1,
            "repair_improved": False,
            "verdict": "regressed",
            "blocking_before": 0,
            "blocking_after": 1,
            "resolved_count": 0,
            "remaining_issue_count": 0,
            "new_issue_count": 1,
            "regression_count": 1,
            "not_comparable_count": 0,
        },
    )


def test_autonomy_one_loop_writes_outcome_latest_summary_and_history(
    tmp_path: Path,
) -> None:
    write_benchmark_summary(tmp_path)

    summary = run_autonomy(root=tmp_path, loops=1, count=2, now=NOW)

    loop_id = "loop-20260415-000000-01"
    loop_dir = tmp_path / ".qa-z" / "loops" / loop_id
    latest_dir = tmp_path / ".qa-z" / "loops" / "latest"
    outcome = read_json(loop_dir / "outcome.json")
    latest_outcome = read_json(latest_dir / "outcome.json")
    latest_summary = read_json(latest_dir / "autonomy_summary.json")
    history = json.loads(
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()[0]
    )

    assert summary["kind"] == "qa_z.autonomy_summary"
    assert summary["loops_requested"] == 1
    assert summary["loops_completed"] == 1
    assert summary["latest_loop_id"] == loop_id
    assert latest_summary == summary
    assert (loop_dir / "self_inspect.json").exists()
    assert (loop_dir / "selected_tasks.json").exists()
    assert (loop_dir / "loop_plan.md").exists()
    assert outcome["kind"] == "qa_z.autonomy_outcome"
    assert outcome["state"] == "completed"
    assert outcome["selected_task_ids"] == ["benchmark-fixture-py-type-error"]
    assert outcome["actions_prepared"][0]["type"] == "benchmark_fixture_plan"
    assert latest_outcome == outcome
    assert history["loop_id"] == loop_id
    assert history["state"] == "completed"
    assert history["outcome_path"] == f".qa-z/loops/{loop_id}/outcome.json"


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

    history_lines = (
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    first_history = json.loads(history_lines[0])
    second_history = json.loads(history_lines[1])
    first_outcome = summary["outcomes"][0]
    second_outcome = summary["outcomes"][1]
    latest_outcome = read_json(tmp_path / ".qa-z" / "loops" / "latest" / "outcome.json")

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
    assert second_history["cumulative_elapsed_seconds"] == 240
    assert clock.sleeps == [120, 120]


def test_autonomy_empty_evidence_is_graceful(tmp_path: Path) -> None:
    summary = run_autonomy(root=tmp_path, loops=1, count=3, now=NOW)
    loop_dir = tmp_path / ".qa-z" / "loops" / "loop-20260415-000000-01"
    selected = read_json(loop_dir / "selected_tasks.json")
    outcome = read_json(loop_dir / "outcome.json")
    plan = (loop_dir / "loop_plan.md").read_text(encoding="utf-8")

    assert summary["loops_completed"] == 1
    assert selected["selected_tasks"] == []
    assert outcome["state"] == "blocked_no_candidates"
    assert outcome["selected_task_ids"] == []
    assert outcome["actions_prepared"] == []
    assert outcome["next_recommendations"] == ["no open backlog tasks selected"]
    assert "blocked_no_candidates" in outcome["state_transitions"]
    assert "No open backlog tasks were selected." in plan


def test_action_mapping_is_local_and_deterministic(tmp_path: Path) -> None:
    benchmark_action = action_for_task(
        root=tmp_path,
        loop_id="loop-one",
        task={
            "id": "benchmark-fixture-py-type-error",
            "category": "benchmark_failure",
            "recommendation": "add_benchmark_fixture",
        },
    )
    verify_action = action_for_task(
        root=tmp_path,
        loop_id="loop-one",
        task={
            "id": "verification-candidate-regressed",
            "category": "verification_regression",
            "recommendation": "repair_verification_regression",
        },
    )

    assert benchmark_action["type"] == "benchmark_fixture_plan"
    assert benchmark_action["commands"] == ["python -m qa_z benchmark --json"]
    assert verify_action["type"] == "verification_stabilization_plan"
    assert verify_action["commands"] == [
        "python -m pytest tests/test_self_improvement.py tests/test_cli.py -q"
    ]


def test_autonomy_status_reflects_latest_loop_and_backlog(tmp_path: Path) -> None:
    write_benchmark_summary(tmp_path)
    run_autonomy(root=tmp_path, loops=1, count=1, now=NOW)

    status = load_autonomy_status(tmp_path)

    assert status["kind"] == "qa_z.autonomy_status"
    assert status["latest_loop_id"] == "loop-20260415-000000-01"
    assert status["latest_state"] == "completed"
    assert status["latest_selected_tasks"] == ["benchmark-fixture-py-type-error"]
    assert status["latest_selected_task_details"][0]["recommendation"] == (
        "add_benchmark_fixture"
    )
    assert status["latest_prepared_actions"][0]["type"] == "benchmark_fixture_plan"
    assert status["backlog_top_items"][0]["id"] == "benchmark-fixture-py-type-error"


def test_autonomy_cli_run_and_status_json(tmp_path: Path, capsys, monkeypatch) -> None:
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
    assert status_exit == 0
    assert status["latest_loop_id"] == output["latest_loop_id"]
    assert status["runtime_target_seconds"] == 4
    assert status["runtime_budget_met"] is True


def test_render_autonomy_status_uses_explicit_no_budget_runtime_text() -> None:
    output = render_autonomy_status(
        {
            "latest_state": "completed",
            "latest_loop_id": "loop-one",
            "latest_selected_tasks": ["benchmark-fixture-py-type-error"],
            "runtime_elapsed_seconds": 2,
            "runtime_target_seconds": 0,
            "runtime_budget_met": True,
            "min_loop_seconds": 0,
            "latest_prepared_actions": [],
            "latest_next_recommendations": [],
            "backlog_top_items": [],
        }
    )

    assert "Runtime: 2 seconds elapsed (no minimum budget)" in output
