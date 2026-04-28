"""Architecture tests for executor-history support seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.executor_history as executor_history_module
import qa_z.executor_history_support as executor_history_support_module


def _executor_history_function_names() -> set[str]:
    source = Path(executor_history_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(executor_history_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_executor_history_support_module_exports_match_surface() -> None:
    assert (
        executor_history_support_module.write_json is executor_history_module.write_json
    )
    assert (
        executor_history_support_module.allocate_attempt_id
        is executor_history_module.allocate_attempt_id
    )
    assert (
        executor_history_support_module.legacy_attempt_base
        is executor_history_module.legacy_attempt_base
    )
    assert executor_history_support_module.slugify is executor_history_module.slugify
    assert (
        executor_history_support_module.resolve_path
        is executor_history_module.resolve_path
    )


def test_executor_history_module_keeps_support_defs_out_of_monolith() -> None:
    function_names = _executor_history_function_names()

    assert "write_json" not in function_names
    assert "allocate_attempt_id" not in function_names
    assert "legacy_attempt_base" not in function_names
    assert "slugify" not in function_names
    assert "resolve_path" not in function_names


def test_history_store_and_dry_run_target_split_support_modules() -> None:
    store_source = Path("src/qa_z/executor_history_store.py").read_text(
        encoding="utf-8"
    )
    dry_run_source = Path("src/qa_z/executor_dry_run.py").read_text(encoding="utf-8")

    assert "executor_history_support" in store_source
    assert "executor_history_support" in dry_run_source
    assert ".allocate_attempt_id(" not in store_source
    assert ".legacy_attempt_base(" not in store_source
