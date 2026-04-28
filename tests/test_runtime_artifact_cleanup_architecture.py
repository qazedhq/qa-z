"""Architecture tests for runtime artifact cleanup seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "runtime_artifact_cleanup.py"
TEST_PATH = ROOT / "tests" / "test_runtime_artifact_cleanup.py"


def _function_names(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    tree = compile(source, str(path), "exec", flags=ast.PyCF_ONLY_AST)
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_runtime_artifact_cleanup_runtime_targets_split_helper() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "runtime_artifact_cleanup_support.py" in source
    assert "sys.dont_write_bytecode = True" in source


def test_runtime_artifact_cleanup_runtime_stays_under_split_budget() -> None:
    line_count = len(SCRIPT_PATH.read_text(encoding="utf-8").splitlines())

    assert line_count <= 320


def test_runtime_artifact_cleanup_runtime_keeps_cleanup_defs_out_of_monolith() -> None:
    function_names = _function_names(SCRIPT_PATH)

    assert "candidate_cleanup_roots" not in function_names
    assert "collect_cleanup_plan" not in function_names
    assert "tracked_paths_under" not in function_names
    assert "delete_candidate_root" not in function_names
    assert "render_human" not in function_names


def test_runtime_artifact_cleanup_tests_share_support_module() -> None:
    assert "from tests.runtime_artifact_cleanup_test_support import" in (
        TEST_PATH.read_text(encoding="utf-8")
    )
