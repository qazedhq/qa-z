"""Tests for self-improvement selection workflow seams."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from tests.ast_test_support import module_body

import pytest

import qa_z.self_improvement as self_improvement_module
import qa_z.self_improvement_selection as self_improvement_selection_module
from qa_z.selection_context import latest_self_inspection_selection_context
from tests.self_improvement_test_support import write_json


def test_self_improvement_selection_module_exports_match_self_improvement_surface() -> (
    None
):
    assert (
        self_improvement_selection_module.SelectionArtifactPaths
        is self_improvement_module.SelectionArtifactPaths
    )
    assert (
        self_improvement_selection_module.select_next_tasks
        is self_improvement_module.select_next_tasks
    )


def test_self_improvement_selection_module_writes_selected_task_artifacts(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-22T00:00:00Z",
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
                    "signals": ["dirty_worktree_large", "worktree_integration_risk"],
                    "first_seen_at": "2026-04-21T00:00:00Z",
                    "last_seen_at": "2026-04-22T00:00:00Z",
                    "recurrence_count": 1,
                }
            ],
        },
    )
    write_json(
        tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json",
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "inspect-loop",
            "generated_at": "2026-04-22T00:00:00Z",
            "live_repository": {
                "modified_count": 2,
                "untracked_count": 1,
                "staged_count": 0,
                "runtime_artifact_count": 0,
                "benchmark_result_count": 1,
                "dirty_benchmark_result_count": 0,
                "release_evidence_count": 0,
                "generated_artifact_policy_explicit": True,
                "dirty_area_summary": "docs:1, source:1",
            },
        },
    )

    paths = self_improvement_selection_module.select_next_tasks(
        root=tmp_path,
        count=1,
        now="2026-04-22T03:04:05Z",
        loop_id="loop-20260422-030405",
    )

    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    history = (tmp_path / ".qa-z" / "loops" / "history.jsonl").read_text(
        encoding="utf-8"
    )

    assert selected["selected_tasks"][0]["id"] == "worktree_risk-dirty-worktree"
    assert selected["selected_tasks"][0]["action_hint"] == (
        "inspect the dirty worktree, run "
        "`python scripts/runtime_artifact_cleanup.py --json` plus "
        "`python scripts/worktree_commit_plan.py --summary-only --json "
        "--fail-on-generated --fail-on-cross-cutting --output "
        ".qa-z/tmp/worktree-commit-plan.json`, then rerun self-inspection"
    )
    assert selected["selected_tasks"][0]["validation_command"] == (
        "python scripts/worktree_commit_plan.py --summary-only --json "
        "--fail-on-generated --fail-on-cross-cutting --output "
        ".qa-z/tmp/worktree-commit-plan.json"
    )
    assert selected["selected_tasks"][0]["evidence_summary"] == "git_status: dirty"
    assert selected["source_self_inspection"] == ".qa-z/loops/latest/self_inspect.json"
    assert selected["source_self_inspection_loop_id"] == "inspect-loop"
    assert selected["source_self_inspection_generated_at"] == "2026-04-22T00:00:00Z"
    assert selected["live_repository"]["modified_count"] == 2
    assert "Reduce dirty worktree integration risk" in paths.loop_plan_path.read_text(
        encoding="utf-8"
    )
    assert "worktree_risk-dirty-worktree" in history


def test_select_next_records_reason_when_no_backlog_tasks_are_open(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-22T00:00:00Z",
            "items": [],
        },
    )
    write_json(
        tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json",
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "inspect-empty",
            "generated_at": "2026-04-22T00:00:00Z",
            "live_repository": {"modified_count": 0, "untracked_count": 0},
        },
    )

    paths = self_improvement_selection_module.select_next_tasks(
        root=tmp_path,
        count=1,
        now="2026-04-22T03:04:05Z",
        loop_id="loop-empty",
    )

    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    plan = paths.loop_plan_path.read_text(encoding="utf-8")
    history = json.loads(
        (tmp_path / ".qa-z" / "loops" / "history.jsonl").read_text(encoding="utf-8")
    )

    assert selected["selected_tasks"] == []
    assert selected["state"] == "blocked_no_candidates"
    assert selected["selection_gap_reason"] == "no_open_backlog_after_inspection"
    assert selected["open_backlog_count"] == 0
    assert selected["next_actions"] == [
        "Review docs/agent/next-real-slices.md for the next safe manually selected Flow, Contract, Evidence, or Cleanup slice.",
        "Rerun backlog and strict worktree evidence before treating an empty backlog as safe exhaustion.",
    ]
    assert selected["next_commands"] == [
        "python -m qa_z backlog --refresh --json",
        "python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting",
    ]
    assert "- State: `blocked_no_candidates`" in plan
    assert "- Selection gap reason: `no_open_backlog_after_inspection`" in plan
    assert "- Open backlog items: 0" in plan
    assert "- Next actions:" in plan
    assert "docs/agent/next-real-slices.md" in plan
    assert "- Next commands:" in plan
    assert "`python -m qa_z backlog --refresh --json`" in plan
    assert "## Verification After External Repair" in plan
    assert history["state"] == "blocked_no_candidates"
    assert history["selection_gap_reason"] == "no_open_backlog_after_inspection"
    assert history["open_backlog_count"] == 0


def test_select_next_wraps_history_append_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-22T00:00:00Z",
            "items": [],
        },
    )
    history_path = tmp_path / ".qa-z" / "loops" / "history.jsonl"
    original_open = Path.open

    def fail_history(path: Path, *args, **kwargs):
        mode = str(args[0] if args else kwargs.get("mode", "r"))
        if path == history_path and "a" in mode:
            raise OSError("disk full")
        return original_open(path, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_history)

    with pytest.raises(OSError) as excinfo:
        self_improvement_selection_module.select_next_tasks(
            root=tmp_path,
            count=1,
            now="2026-04-22T03:04:05Z",
            loop_id="loop-history-fail",
        )

    message = str(excinfo.value)
    assert "could not append self-improvement history" in message
    assert str(history_path) in message
    assert "disk full" in message


def test_select_next_marks_stale_self_inspection_context_after_backlog_update(
    tmp_path: Path,
) -> None:
    write_json(
        tmp_path / ".qa-z" / "improvement" / "backlog.json",
        {
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "updated_at": "2026-04-22T00:00:00Z",
            "items": [
                {
                    "id": "fresh-work",
                    "title": "Fresh backlog work",
                    "category": "workflow_gap",
                    "evidence": [{"source": "test", "path": "fresh.json"}],
                    "impact": 4,
                    "likelihood": 4,
                    "confidence": 4,
                    "repair_cost": 2,
                    "priority_score": 50,
                    "status": "open",
                    "recommendation": "create_repair_session",
                    "signals": [],
                    "first_seen_at": "2026-04-22T00:00:00Z",
                    "last_seen_at": "2026-04-22T00:00:00Z",
                    "recurrence_count": 1,
                }
            ],
        },
    )
    write_json(
        tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json",
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "inspect-old",
            "generated_at": "2026-04-21T00:00:00Z",
            "live_repository": {"modified_count": 99},
        },
    )

    paths = self_improvement_selection_module.select_next_tasks(
        root=tmp_path,
        count=1,
        now="2026-04-22T03:04:05Z",
        loop_id="loop-fresh",
    )

    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    plan = paths.loop_plan_path.read_text(encoding="utf-8")
    history = json.loads(
        (tmp_path / ".qa-z" / "loops" / "history.jsonl").read_text(encoding="utf-8")
    )

    assert selected["selected_tasks"][0]["id"] == "fresh-work"
    assert selected["source_self_inspection_stale_for_backlog"] is True
    assert selected["source_self_inspection_refresh_commands"] == [
        "python -m qa_z select-next --refresh --count 3 --json"
    ]
    assert "live_repository" not in selected
    assert "- Source self-inspection stale for backlog: true" in plan
    assert "- Source self-inspection refresh commands:" in plan
    assert "  - `python -m qa_z select-next --refresh --count 3 --json`" in plan
    assert history["source_self_inspection_stale_for_backlog"] is True
    assert history["source_self_inspection_refresh_commands"] == [
        "python -m qa_z select-next --refresh --count 3 --json"
    ]
    assert "live_repository" not in history


def test_selection_context_treats_missing_and_malformed_timestamps_as_stale(
    tmp_path: Path,
) -> None:
    path = tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json"
    write_json(
        path,
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "inspect-missing",
            "live_repository": {"modified_count": 99},
        },
    )

    missing_context = latest_self_inspection_selection_context(
        tmp_path, min_generated_at="2026-04-22T00:00:00Z"
    )

    assert missing_context["source_self_inspection_stale_for_backlog"] is True
    assert "live_repository" not in missing_context

    write_json(
        path,
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "inspect-malformed",
            "generated_at": "not-a-timestamp",
            "live_repository": {"modified_count": 99},
        },
    )

    malformed_context = latest_self_inspection_selection_context(
        tmp_path, min_generated_at="2026-04-22T00:00:00Z"
    )

    assert malformed_context["source_self_inspection_stale_for_backlog"] is True
    assert malformed_context["source_self_inspection_generated_at"] == (
        "not-a-timestamp"
    )
    assert "live_repository" not in malformed_context


def test_selection_context_treats_missing_or_wrong_kind_self_inspection_as_stale(
    tmp_path: Path,
) -> None:
    path = tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json"

    missing_context = latest_self_inspection_selection_context(
        tmp_path, min_generated_at="2026-04-22T00:00:00Z"
    )

    assert missing_context["source_self_inspection"] == (
        ".qa-z/loops/latest/self_inspect.json"
    )
    assert missing_context["source_self_inspection_stale_for_backlog"] is True
    assert missing_context["source_self_inspection_refresh_commands"] == [
        "python -m qa_z select-next --refresh --count 3 --json"
    ]
    assert "live_repository" not in missing_context

    write_json(
        path,
        {
            "kind": "qa_z.selected_tasks",
            "schema_version": 1,
            "generated_at": "2026-04-22T01:00:00Z",
            "live_repository": {"modified_count": 99},
        },
    )

    wrong_kind_context = latest_self_inspection_selection_context(
        tmp_path, min_generated_at="2026-04-22T00:00:00Z"
    )

    assert wrong_kind_context["source_self_inspection_stale_for_backlog"] is True
    assert wrong_kind_context["source_self_inspection_generated_at"] == (
        "2026-04-22T01:00:00Z"
    )
    assert "live_repository" not in wrong_kind_context


def test_selection_context_compares_timezone_offsets_by_instant(
    tmp_path: Path,
) -> None:
    path = tmp_path / ".qa-z" / "loops" / "latest" / "self_inspect.json"
    write_json(
        path,
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "inspect-equal-offset",
            "generated_at": "2026-04-21T23:30:00-01:00",
            "live_repository": {"modified_count": 2},
        },
    )

    fresh_context = latest_self_inspection_selection_context(
        tmp_path, min_generated_at="2026-04-22T00:00:00Z"
    )

    assert fresh_context["source_self_inspection_loop_id"] == "inspect-equal-offset"
    assert fresh_context["live_repository"]["modified_count"] == 2
    assert "source_self_inspection_stale_for_backlog" not in fresh_context

    write_json(
        path,
        {
            "kind": "qa_z.self_inspection",
            "schema_version": 1,
            "loop_id": "inspect-older-offset",
            "generated_at": "2026-04-21T22:30:00-01:00",
            "live_repository": {"modified_count": 99},
        },
    )

    stale_context = latest_self_inspection_selection_context(
        tmp_path, min_generated_at="2026-04-22T00:00:00Z"
    )

    assert stale_context["source_self_inspection_stale_for_backlog"] is True
    assert stale_context["source_self_inspection_loop_id"] == "inspect-older-offset"
    assert "live_repository" not in stale_context


def test_self_improvement_module_keeps_selection_defs_out_of_monolith() -> None:
    source = Path(self_improvement_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(self_improvement_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    function_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }
    class_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.ClassDef)
    }

    assert "select_next_tasks" not in function_names
    assert "SelectionArtifactPaths" not in class_names
