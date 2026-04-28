"""Architecture tests for executor-result model seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body


def test_executor_result_models_module_exists() -> None:
    assert Path("src/qa_z/executor_result_models.py").exists()


def test_executor_result_monolith_no_longer_defines_model_classes() -> None:
    source = Path("src/qa_z/executor_result.py").read_text(encoding="utf-8")
    tree = compile(
        source,
        "src/qa_z/executor_result.py",
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    class_names = {
        node.name for node in module_body(tree) if isinstance(node, ast.ClassDef)
    }

    assert "ExecutorChangedFile" not in class_names
    assert "ExecutorValidationResult" not in class_names
    assert "ExecutorValidation" not in class_names
    assert "ExecutorResult" not in class_names


def test_executor_result_module_routes_models_through_split_module() -> None:
    source = Path("src/qa_z/executor_result.py").read_text(encoding="utf-8")

    assert "executor_result_models" in source
