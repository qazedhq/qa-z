"""Tests for QA-Z self-inspection and improvement backlog planning."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.cli import main
from qa_z.self_improvement import (
    run_self_inspection,
    select_next_tasks,
    selected_task_action_hint,
)
from tests.self_improvement_test_support import (
    stub_live_repository_signals,
    write_benchmark_summary,
    write_json,
    write_report,
)


NOW = "2026-04-15T00:00:00Z"


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
    write_json(
        tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json",
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "inspect-loop",
            "generated_at": NOW,
            "live_repository": {
                "modified_count": 4,
                "untracked_count": 2,
                "staged_count": 0,
                "runtime_artifact_count": 1,
                "benchmark_result_count": 1,
                "dirty_benchmark_result_count": 0,
                "generated_artifact_policy_explicit": True,
                "dirty_area_summary": "docs:3, source:2, tests:1",
            },
            "candidates": [],
        },
    )

    paths = select_next_tasks(root=tmp_path, count=2, now=NOW, loop_id="select-loop")

    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    plan = paths.loop_plan_path.read_text(encoding="utf-8")
    history_lines = (
        (tmp_path / ".qa-z" / "loops" / "history.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    history = json.loads(history_lines[0])

    assert [task["id"] for task in selected["selected_tasks"]] == ["high", "low"]
    assert selected["loop_id"] == "select-loop"
    assert selected["source_self_inspection"] == ".qa-z/loops/latest/self_inspect.json"
    assert selected["source_self_inspection_loop_id"] == "inspect-loop"
    assert selected["source_self_inspection_generated_at"] == NOW
    assert selected["live_repository"]["modified_count"] == 4
    assert "High priority" in plan
    assert "Live Repository Context" in plan
    assert (
        "modified=4; untracked=2; staged=0; runtime_artifacts=1; "
        "benchmark_results=1; dirty_benchmark_results=0; release_evidence=0; "
        "generated_policy=true; "
        "areas=docs:3, source:2, tests:1" in plan
    )
    assert history["loop_id"] == "select-loop"
    assert history["selected_tasks"] == ["high", "low"]
    assert history["source_self_inspection"] == ".qa-z/loops/latest/self_inspect.json"
    assert history["source_self_inspection_loop_id"] == "inspect-loop"
    assert history["source_self_inspection_generated_at"] == NOW
    assert (
        history["live_repository"]["dirty_area_summary"] == "docs:3, source:2, tests:1"
    )
    assert history["resulting_session_id"] is None


def test_self_inspection_promotes_deferred_cleanup_and_commit_isolation_gaps(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=4,
        untracked_count=2,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=[
            "docs/reports/worktree-triage.md",
            "benchmarks/results/report.md",
        ],
        runtime_artifact_paths=["benchmarks/results/report.md"],
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

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

        Deferred cleanup items remain open. Generated benchmark summaries should
        stay deferred until intentionally frozen evidence is declared.
        """,
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

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
    assert {evidence["summary"] for evidence in deferred["evidence"]} >= {
        "report freshness verified: date=2026-04-15; branch=codex/qa-z-bootstrap; head=1234567890abcdef1234567890abcdef12345678"
    }
    assert {evidence["summary"] for evidence in isolation["evidence"]} >= {
        "report freshness verified: date=2026-04-15; branch=codex/qa-z-bootstrap; head=1234567890abcdef1234567890abcdef12345678"
    }


def test_self_inspection_skips_deferred_cleanup_for_clean_benchmark_outputs(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        modified_count=0,
        untracked_count=0,
        staged_count=0,
        modified_paths=[],
        untracked_paths=[],
        runtime_artifact_paths=[],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-15
        Branch context: `codex/qa-z-bootstrap`

        Deferred cleanup once mentioned generated benchmark outputs and
        intentionally frozen evidence decisions.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="clean-benchmark-only")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" not in categories


def test_self_inspection_skips_deferred_cleanup_without_live_cleanup_pressure(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=2,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["tests/test_cli.py"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
        generated_artifact_policy_explicit=True,
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

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="stale-cleanup")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" not in categories


def test_integration_gap_includes_live_worktree_area_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=2,
        untracked_count=2,
        staged_count=1,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=[
            "benchmarks/fixtures/new_case/expected.json",
            "tests/test_cli.py",
        ],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

        Dirty worktree integration caveats need a commit split before release.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="integration-gap")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    integration = next(
        item for item in report["candidates"] if item["category"] == "integration_gap"
    )

    assert integration["evidence"][-1] == {
        "source": "git_status",
        "path": ".",
        "summary": (
            "integration worktree spans modified=2; untracked=2; staged=1; "
            "areas=benchmark:1, docs:1, source:1, tests:1"
        ),
    }
    assert {evidence["summary"] for evidence in integration["evidence"]} >= {
        "report freshness verified: date=2026-04-15; branch=codex/qa-z-bootstrap; head=1234567890abcdef1234567890abcdef12345678"
    }
    assert selected_task_action_hint(integration) == (
        "audit benchmark, docs, source, and tests integration first, then rerun "
        "self-inspection"
    )


def test_self_inspection_ignores_cleanup_report_terms_when_worktree_is_clean(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=0,
        untracked_count=0,
        staged_count=0,
        modified_paths=[],
        untracked_paths=[],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Recommended commit order remains important for the old dirty worktree.
        Deferred cleanup and generated benchmark outputs were called out during
        the historical split.
        """,
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        This historical worktree triage mentioned dirty worktree cleanup and
        commit split risk.
        """,
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        The corrected commit sequence required git add -p and a commit split.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="clean-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "commit_isolation_gap" not in categories
    assert "deferred_cleanup_gap" not in categories
    assert "integration_gap" not in categories


def test_self_inspection_ignores_generated_cleanup_when_policy_is_explicit(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=0,
        untracked_count=0,
        staged_count=0,
        modified_paths=[],
        untracked_paths=[],
        runtime_artifact_paths=[],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
        generated_artifact_policy_explicit=True,
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Deferred cleanup once mentioned generated benchmark outputs.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="explicit-policy-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" not in categories


def test_self_inspection_skips_report_only_deferred_cleanup_when_policy_is_explicit(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=11,
        untracked_count=1,
        staged_count=0,
        modified_paths=[
            "README.md",
            "src/qa_z/self_improvement.py",
            "src/qa_z/cli.py",
            "tests/test_a.py",
            "tests/test_b.py",
            "docs/a.md",
            "docs/b.md",
            "docs/c.md",
            "benchmarks/fixtures/a/expected.json",
            "benchmarks/fixtures/b/expected.json",
            "qa-z.yaml",
        ],
        untracked_paths=["tests/test_self_improvement.py"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
        generated_artifact_policy_explicit=True,
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Deferred cleanup, commit-isolation, and integration report-only evidence
        is not enough to reopen those candidates. Generated benchmark outputs are
        local by default under the generated-versus-frozen evidence policy.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="report-only-cleanup")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" not in categories
    assert "worktree_risk" in categories


def test_self_inspection_promotes_runtime_artifact_cleanup_from_live_paths(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=0,
        untracked_count=0,
        staged_count=0,
        modified_paths=[],
        untracked_paths=[],
        runtime_artifact_paths=[".qa-z/loops/latest/outcome.json"],
        benchmark_result_paths=[],
        generated_artifact_policy_explicit=True,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="runtime-path-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    cleanup = next(
        item
        for item in report["candidates"]
        if item["id"] == "runtime_artifact_cleanup_gap-generated-results"
    )

    assert cleanup["recommendation"] == "triage_and_isolate_changes"
    assert cleanup["evidence"] == [
        {
            "source": "runtime_artifacts",
            "path": ".qa-z/loops/latest/outcome.json",
            "summary": (
                "generated runtime artifacts need explicit cleanup handling: "
                ".qa-z/loops/latest/outcome.json"
            ),
        }
    ]


def test_self_inspection_uses_alpha_closure_snapshot_for_commit_isolation_evidence(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
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

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

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
        "report freshness verified: date=2026-04-15; branch=codex/qa-z-bootstrap; head=1234567890abcdef1234567890abcdef12345678",
        "dirty worktree still spans modified=3; untracked=1; areas=docs:2, source:1",
    }


def test_self_inspection_skips_commit_isolation_for_runtime_artifact_only_pressure(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=0,
        untracked_count=2,
        staged_count=0,
        modified_paths=[],
        untracked_paths=[
            ".qa-z/loops/latest/outcome.json",
            "benchmarks/results/report.md",
        ],
        runtime_artifact_paths=[
            ".qa-z/loops/latest/outcome.json",
            "benchmarks/results/report.md",
        ],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-15
        Branch context: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation and `git add -p`.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="runtime-artifact-only")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "commit_isolation_gap" not in categories


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
    inspect_human_exit = main(["self-inspect", "--path", str(tmp_path)])
    inspect_human_output = capsys.readouterr().out

    assert inspect_exit == 0
    assert inspect_output["kind"] == "qa_z.self_inspection"
    assert select_exit == 0
    assert select_output["kind"] == "qa_z.selected_tasks"
    assert (
        select_output["source_self_inspection"]
        == ".qa-z/loops/latest/self_inspect.json"
    )
    assert select_output["live_repository"]["benchmark_result_count"] == 1
    assert select_output["live_repository"]["dirty_benchmark_result_count"] == 0
    assert backlog_exit == 0
    assert backlog_output["kind"] == "qa_z.improvement_backlog"
    assert inspect_human_exit == 0
    assert (
        "Live repository: modified=0; untracked=0; staged=0; "
        "runtime_artifacts=0; benchmark_results=1; dirty_benchmark_results=0; "
        "release_evidence=0; "
        "generated_policy=false"
    ) in inspect_human_output
    assert (tmp_path / ".qa-z" / "loops" / "latest" / "selected_tasks.json").exists()
    assert (tmp_path / ".qa-z" / "loops" / "latest" / "loop_plan.md").exists()
