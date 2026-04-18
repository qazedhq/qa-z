"""Tests for artifact-driven self-improvement planning."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.cli import main
from qa_z.self_improvement import (
    BACKLOG_KIND,
    SELECTED_TASKS_KIND,
    BacklogCandidate,
    benchmark_summary_snapshot,
    compact_backlog_evidence_summary,
    load_backlog,
    run_self_inspection,
    score_candidate,
    select_next_tasks,
    selected_task_action_hint,
    selected_task_validation_command,
)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_benchmark_summary(tmp_path: Path, *, failed: bool = True) -> Path:
    summary_path = tmp_path / "benchmarks" / "results" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "kind": "qa_z.benchmark_summary",
        "schema_version": 1,
        "fixtures_total": 2,
        "fixtures_passed": 1 if failed else 2,
        "fixtures_failed": 1 if failed else 0,
        "overall_rate": 0.5 if failed else 1.0,
        "snapshot": "1/2 fixtures, overall_rate 0.5"
        if failed
        else "2/2 fixtures, overall_rate 1.0",
        "failed_fixtures": ["py_lint_failure"] if failed else [],
        "fixtures": [
            {
                "name": "py_lint_failure",
                "passed": not failed,
                "failures": ["expected failed check py_lint was missing"],
                "categories": ["detection"],
                "actual": {},
                "artifacts": [],
            }
        ],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary_path


def write_legacy_benchmark_summary(tmp_path: Path) -> Path:
    summary_path = tmp_path / "benchmarks" / "results" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "fixtures_total": 3,
        "fixtures_passed": 2,
        "fixtures_failed": 1,
        "overall_rate": 0.6667,
        "failed_fixtures": ["legacy_fixture"],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary_path


def write_aggregate_failure_summary(tmp_path: Path) -> Path:
    summary_path = tmp_path / "benchmarks" / "results" / "summary.json"
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "kind": "qa_z.benchmark_summary",
        "schema_version": 1,
        "fixtures_total": 4,
        "fixtures_passed": 2,
        "fixtures_failed": 2,
        "overall_rate": 0.5,
        "fixtures": [],
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary_path


def write_backlog(tmp_path: Path, items: list[dict]) -> Path:
    backlog_path = tmp_path / ".qa-z" / "improvement" / "backlog.json"
    backlog_path.parent.mkdir(parents=True, exist_ok=True)
    backlog_path.write_text(
        json.dumps(
            {
                "kind": BACKLOG_KIND,
                "schema_version": 1,
                "generated_at": "2026-04-15T00:00:00Z",
                "items": items,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return backlog_path


def test_score_candidate_uses_formula_grounded_bonuses_and_recurrence() -> None:
    candidate = BacklogCandidate(
        id="benchmark-fixture-example",
        title="Repair benchmark fixture example",
        category="benchmark_failure",
        recommendation="add_benchmark_fixture",
        evidence=[],
        signals={"failed_benchmark_fixture": True},
        impact=4,
        likelihood=3,
        confidence=2,
        repair_cost=5,
    )

    assert score_candidate(candidate, recurrence_count=3) == 45


def test_self_inspection_writes_report_and_updates_backlog(tmp_path: Path) -> None:
    write_benchmark_summary(tmp_path)

    paths = run_self_inspection(
        root=tmp_path,
        loop_id="loop-1",
        generated_at="2026-04-15T00:00:00Z",
    )
    report = read_json(paths.self_inspection_path)
    backlog = read_json(paths.backlog_path)

    assert report["kind"] == "qa_z.self_inspection"
    assert report["artifact_only"] is True
    assert report["candidates_total"] == 1
    assert report["candidates"][0]["id"] == "benchmark-fixture-py-lint-failure"
    assert report["evidence_sources"] == [
        {"source": "benchmark_summary", "path": "benchmarks/results/summary.json"}
    ]
    assert backlog["kind"] == BACKLOG_KIND
    assert backlog["items"][0]["status"] == "open"
    assert backlog["items"][0]["priority_score"] > 0
    assert (
        backlog["items"][0]["evidence"][0]["snapshot"]
        == "1/2 fixtures, overall_rate 0.5"
    )


def test_self_inspection_synthesizes_snapshot_for_legacy_benchmark_summary(
    tmp_path: Path,
) -> None:
    summary_path = write_legacy_benchmark_summary(tmp_path)
    summary = read_json(summary_path)

    paths = run_self_inspection(root=tmp_path)
    backlog = read_json(paths.backlog_path)

    assert benchmark_summary_snapshot(summary) == "2/3 fixtures, overall_rate 0.6667"
    assert (
        backlog["items"][0]["signals"]["snapshot"]
        == "2/3 fixtures, overall_rate 0.6667"
    )


def test_self_inspection_creates_candidate_for_aggregate_benchmark_failure(
    tmp_path: Path,
) -> None:
    write_aggregate_failure_summary(tmp_path)

    paths = run_self_inspection(root=tmp_path)
    backlog = read_json(paths.backlog_path)

    assert [item["id"] for item in backlog["items"]] == ["benchmark-summary-failures"]
    assert backlog["items"][0]["signals"]["benchmark_summary_failure"] is True


def test_self_inspection_preserves_recurrence_from_existing_backlog(
    tmp_path: Path,
) -> None:
    write_benchmark_summary(tmp_path)
    write_backlog(
        tmp_path,
        [
            {
                "id": "benchmark-fixture-py-lint-failure",
                "title": "Old title",
                "category": "benchmark_failure",
                "recommendation": "add_benchmark_fixture",
                "status": "open",
                "first_seen_at": "2026-04-14T00:00:00Z",
                "last_seen_at": "2026-04-14T00:00:00Z",
                "recurrence_count": 2,
                "priority_score": 10,
                "evidence": [],
                "signals": {},
            }
        ],
    )

    paths = run_self_inspection(
        root=tmp_path,
        generated_at="2026-04-15T00:00:00Z",
    )
    item = read_json(paths.backlog_path)["items"][0]

    assert item["first_seen_at"] == "2026-04-14T00:00:00Z"
    assert item["last_seen_at"] == "2026-04-15T00:00:00Z"
    assert item["recurrence_count"] == 3
    assert item["priority_score"] > 10


def test_self_inspection_with_no_evidence_writes_empty_artifacts(
    tmp_path: Path,
) -> None:
    paths = run_self_inspection(root=tmp_path, loop_id="empty")

    report = read_json(paths.self_inspection_path)
    backlog = read_json(paths.backlog_path)

    assert report["candidates_total"] == 0
    assert report["evidence_sources"] == []
    assert backlog["items"] == []
    assert load_backlog(tmp_path)["items"] == []


def test_self_inspection_closes_stale_open_backlog_items_not_reobserved(
    tmp_path: Path,
) -> None:
    write_backlog(
        tmp_path,
        [
            {
                "id": "old-item",
                "title": "Old item",
                "category": "docs_drift",
                "recommendation": "sync_contract_and_docs",
                "status": "open",
                "first_seen_at": "2026-04-14T00:00:00Z",
                "last_seen_at": "2026-04-14T00:00:00Z",
                "recurrence_count": 1,
                "priority_score": 1,
                "evidence": [],
                "signals": {},
            }
        ],
    )

    paths = run_self_inspection(
        root=tmp_path,
        generated_at="2026-04-15T00:00:00Z",
    )
    item = read_json(paths.backlog_path)["items"][0]

    assert item["status"] == "closed"
    assert item["closure_reason"] == "not_reobserved"


def test_self_inspection_keeps_in_progress_backlog_items_when_not_reobserved(
    tmp_path: Path,
) -> None:
    write_backlog(
        tmp_path,
        [
            {
                "id": "active-item",
                "title": "Active item",
                "category": "docs_drift",
                "recommendation": "sync_contract_and_docs",
                "status": "in_progress",
                "first_seen_at": "2026-04-14T00:00:00Z",
                "last_seen_at": "2026-04-14T00:00:00Z",
                "recurrence_count": 1,
                "priority_score": 1,
                "evidence": [],
                "signals": {},
            }
        ],
    )

    paths = run_self_inspection(root=tmp_path)
    item = read_json(paths.backlog_path)["items"][0]

    assert item["status"] == "in_progress"
    assert "closure_reason" not in item


def test_select_next_writes_selected_tasks_loop_plan_and_history(
    tmp_path: Path,
) -> None:
    write_backlog(
        tmp_path,
        [
            {
                "id": "low",
                "title": "Low priority",
                "category": "docs_drift",
                "recommendation": "sync_contract_and_docs",
                "status": "open",
                "priority_score": 5,
                "recurrence_count": 1,
                "evidence": [],
                "signals": {},
            },
            {
                "id": "high",
                "title": "High priority",
                "category": "benchmark_failure",
                "recommendation": "add_benchmark_fixture",
                "status": "open",
                "priority_score": 50,
                "recurrence_count": 2,
                "evidence": [
                    {
                        "source": "benchmark_summary",
                        "path": "benchmarks/results/summary.json",
                        "summary": "failed fixture",
                    }
                ],
                "signals": {"failed_benchmark_fixture": True},
            },
        ],
    )

    paths = select_next_tasks(root=tmp_path, count=1, loop_id="loop-2")
    selected = read_json(paths.selected_tasks_path)
    loop_plan = paths.loop_plan_path.read_text(encoding="utf-8")
    history_lines = paths.history_path.read_text(encoding="utf-8").splitlines()

    assert selected["kind"] == SELECTED_TASKS_KIND
    assert selected["selected_tasks"][0]["id"] == "high"
    assert selected["selected_tasks"][0]["action_hint"]
    assert "Backlog id: `high`" in loop_plan
    assert "python -m qa_z benchmark --json" in loop_plan
    assert json.loads(history_lines[-1])["selected_task_ids"] == ["high"]


def test_select_next_clamps_count_to_three(tmp_path: Path) -> None:
    write_backlog(
        tmp_path,
        [
            {
                "id": f"item-{index}",
                "title": f"Item {index}",
                "category": "benchmark_failure",
                "recommendation": "add_benchmark_fixture",
                "status": "open",
                "priority_score": 100 - index,
                "recurrence_count": 1,
                "evidence": [],
                "signals": {},
            }
            for index in range(5)
        ],
    )

    paths = select_next_tasks(root=tmp_path, count=99)
    selected = read_json(paths.selected_tasks_path)

    assert selected["selection_limit"] == 3
    assert selected["selected_count"] == 3


def test_self_improvement_cli_commands_write_expected_paths(
    tmp_path: Path, capsys
) -> None:
    write_benchmark_summary(tmp_path)

    inspect_exit = main(["self-inspect", "--path", str(tmp_path), "--json"])
    inspect_output = json.loads(capsys.readouterr().out)
    backlog_exit = main(["backlog", "--path", str(tmp_path), "--json"])
    backlog_output = json.loads(capsys.readouterr().out)
    select_exit = main(
        ["select-next", "--path", str(tmp_path), "--count", "1", "--json"]
    )
    select_output = json.loads(capsys.readouterr().out)

    assert inspect_exit == 0
    assert inspect_output["kind"] == "qa_z.self_inspection"
    assert backlog_exit == 0
    assert backlog_output["items"][0]["id"] == "benchmark-fixture-py-lint-failure"
    assert select_exit == 0
    assert (
        select_output["selected_tasks"][0]["id"] == "benchmark-fixture-py-lint-failure"
    )
    assert (tmp_path / ".qa-z" / "loops" / "latest" / "loop_plan.md").exists()


def test_human_cli_output_is_path_focused(tmp_path: Path, capsys) -> None:
    write_benchmark_summary(tmp_path)

    inspect_exit = main(["self-inspect", "--path", str(tmp_path)])
    inspect_output = capsys.readouterr().out
    backlog_exit = main(["backlog", "--path", str(tmp_path)])
    backlog_output = capsys.readouterr().out
    select_exit = main(["select-next", "--path", str(tmp_path)])
    select_output = capsys.readouterr().out

    assert inspect_exit == 0
    assert "Self inspection:" in inspect_output
    assert ".qa-z/loops/latest/self_inspect.json" in inspect_output
    assert backlog_exit == 0
    assert "Open backlog items: 1" in backlog_output
    assert select_exit == 0
    assert "Selected tasks:" in select_output
    assert ".qa-z/loops/latest/selected_tasks.json" in select_output


def test_selected_task_action_hint_and_validation_specialize_known_recommendations() -> (
    None
):
    benchmark_task = {
        "category": "benchmark_failure",
        "recommendation": "add_benchmark_fixture",
    }
    verification_task = {
        "category": "verification_regression",
        "recommendation": "repair_verification_regression",
    }
    docs_task = {"category": "docs_drift", "recommendation": "sync_contract_and_docs"}

    assert "benchmark" in selected_task_action_hint(benchmark_task)
    assert (
        selected_task_validation_command(benchmark_task)
        == "python -m qa_z benchmark --json"
    )
    assert "verification" in selected_task_action_hint(verification_task)
    assert "tests/test_self_improvement.py" in selected_task_validation_command(
        verification_task
    )
    assert "docs" in selected_task_action_hint(docs_task)
    assert "tests/test_artifact_schema.py" in selected_task_validation_command(
        docs_task
    )


def test_compact_evidence_summary_prefers_benchmark_snapshot() -> None:
    item = {
        "evidence": [
            {"source": "readme", "path": "README.md", "summary": "docs drift"},
            {
                "source": "benchmark_summary",
                "path": "benchmarks/results/summary.json",
                "summary": "fixture failed",
                "snapshot": "1/2 fixtures, overall_rate 0.5",
            },
        ]
    }

    assert compact_backlog_evidence_summary(item) == (
        "benchmark_summary at benchmarks/results/summary.json: "
        "fixture failed; 1/2 fixtures, overall_rate 0.5"
    )
