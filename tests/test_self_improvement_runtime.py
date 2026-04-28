"""Tests for self-improvement runtime and artifact helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.self_improvement as self_improvement_module
import qa_z.self_improvement_runtime as self_improvement_runtime_module


def test_self_improvement_runtime_module_reads_optional_artifacts(
    tmp_path: Path,
) -> None:
    json_path = tmp_path / "artifact.json"
    json_path.write_text('{"value": 3}\n', encoding="utf-8")
    text_path = tmp_path / "notes.txt"
    text_path.write_text("hello\n", encoding="utf-8")

    assert self_improvement_runtime_module.read_json_object(json_path) == {"value": 3}
    assert (
        self_improvement_runtime_module.read_json_object(tmp_path / "missing.json")
        == {}
    )
    assert self_improvement_runtime_module.read_text(text_path) == "hello\n"
    assert self_improvement_runtime_module.read_text(tmp_path / "missing.txt") == ""


def test_self_improvement_runtime_module_resolves_paths_and_loop_ids(
    tmp_path: Path,
) -> None:
    assert (
        self_improvement_runtime_module.resolve_optional_artifact_path(tmp_path, "")
        is None
    )
    assert (
        self_improvement_runtime_module.resolve_optional_artifact_path(
            tmp_path, "reports/out.json"
        )
        == (tmp_path / "reports" / "out.json").resolve()
    )
    assert (
        self_improvement_runtime_module.default_loop_id(
            "inspect", "2026-04-22T11:22:33Z"
        )
        == "inspect-20260422-112233"
    )


def test_self_improvement_module_keeps_runtime_helper_defs_out_of_monolith() -> None:
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

    assert "resolve_optional_artifact_path" not in function_names
    assert "write_json" not in function_names
    assert "read_json_object" not in function_names
    assert "read_text" not in function_names
    assert "utc_now" not in function_names
    assert "default_loop_id" not in function_names
