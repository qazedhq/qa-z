"""Tests for self-improvement selection workflow seams."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.self_improvement as self_improvement_module
import qa_z.self_improvement_selection as self_improvement_selection_module
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
    assert selected["source_self_inspection"] == ".qa-z/loops/latest/self_inspect.json"
    assert selected["source_self_inspection_loop_id"] == "inspect-loop"
    assert selected["source_self_inspection_generated_at"] == "2026-04-22T00:00:00Z"
    assert selected["live_repository"]["modified_count"] == 2
    assert "Reduce dirty worktree integration risk" in paths.loop_plan_path.read_text(
        encoding="utf-8"
    )
    assert "worktree_risk-dirty-worktree" in history


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
