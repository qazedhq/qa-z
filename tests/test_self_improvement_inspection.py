"""Tests for self-improvement inspection workflow seams."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.self_improvement as self_improvement_module
import qa_z.self_improvement_inspection as self_improvement_inspection_module
import qa_z.self_improvement_registry as self_improvement_registry_module


def test_self_improvement_inspection_modules_match_self_improvement_surface() -> None:
    assert (
        self_improvement_inspection_module.SelfInspectionArtifactPaths
        is self_improvement_module.SelfInspectionArtifactPaths
    )
    assert (
        self_improvement_inspection_module.run_self_inspection
        is self_improvement_module.run_self_inspection
    )
    assert (
        self_improvement_registry_module.DISCOVERY_STAGE_NAMES
        == self_improvement_module.DISCOVERY_STAGE_NAMES
    )


def test_self_improvement_inspection_module_writes_report_and_backlog(
    tmp_path: Path,
) -> None:
    paths = self_improvement_inspection_module.run_self_inspection(
        root=tmp_path,
        now="2026-04-22T08:09:10Z",
        loop_id="inspect-20260422-080910",
    )

    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))

    assert report["kind"] == "qa_z.self_inspection"
    assert report["loop_id"] == "inspect-20260422-080910"
    assert backlog["kind"] == "qa_z.improvement_backlog"


def test_discover_candidates_respects_explicit_empty_live_signals(
    tmp_path: Path, monkeypatch
) -> None:
    def fail_live_signal_collection(_root: Path) -> dict[str, object]:
        raise AssertionError("live signals should not be collected")

    monkeypatch.setattr(
        self_improvement_module,
        "collect_live_repository_signals",
        fail_live_signal_collection,
    )

    candidates = self_improvement_inspection_module.discover_candidates(
        tmp_path,
        existing={
            "kind": "qa_z.improvement_backlog",
            "schema_version": 1,
            "items": [],
        },
        live_signals={},
        generated_at="2026-04-22T08:09:10Z",
    )

    assert isinstance(candidates, list)


def test_self_improvement_module_keeps_inspection_defs_out_of_monolith() -> None:
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
    assignment_names = {
        target.id
        for node in module_body(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }

    assert "run_self_inspection" not in function_names
    assert "discover_candidates" not in function_names
    assert "SelfInspectionArtifactPaths" not in class_names
    assert "DISCOVERY_PIPELINE_STAGES" not in assignment_names
