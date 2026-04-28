"""Architecture tests for deep-runner seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.runners.deep as deep_module
import qa_z.runners.deep_policy as deep_policy_module
import qa_z.runners.deep_runtime as deep_runtime_module


def _deep_function_names() -> set[str]:
    source = Path(deep_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(deep_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_deep_runtime_module_exports_match_surface() -> None:
    assert deep_runtime_module.run_deep is deep_module.run_deep
    assert deep_runtime_module.resolve_deep_run_dir is deep_module.resolve_deep_run_dir
    assert (
        deep_runtime_module.resolve_deep_change_set
        is deep_module.resolve_deep_change_set
    )


def test_deep_policy_module_exports_match_surface() -> None:
    assert deep_policy_module.resolve_deep_checks is deep_module.resolve_deep_checks
    assert (
        deep_policy_module.configured_deep_checks is deep_module.configured_deep_checks
    )
    assert deep_policy_module.fail_on_missing_tool is deep_module.fail_on_missing_tool
    assert deep_policy_module.full_run_threshold is deep_module.full_run_threshold
    assert deep_policy_module.high_risk_paths is deep_module.high_risk_paths
    assert deep_policy_module.deep_exclude_paths is deep_module.deep_exclude_paths


def test_deep_module_keeps_public_defs_out_of_monolith() -> None:
    function_names = _deep_function_names()

    assert "run_deep" not in function_names
    assert "resolve_deep_run_dir" not in function_names
    assert "resolve_deep_change_set" not in function_names
    assert "resolve_deep_checks" not in function_names
    assert "configured_deep_checks" not in function_names
    assert "fail_on_missing_tool" not in function_names
    assert "full_run_threshold" not in function_names
    assert "high_risk_paths" not in function_names
    assert "deep_exclude_paths" not in function_names


def test_deep_surface_avoids_importlib_facades() -> None:
    source = Path("src/qa_z/runners/deep.py").read_text(encoding="utf-8")

    assert "importlib.import_module" not in source
