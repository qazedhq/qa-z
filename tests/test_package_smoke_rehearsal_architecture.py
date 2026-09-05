"""Architecture tests for the package smoke rehearsal seam."""

from __future__ import annotations

import ast
from pathlib import Path

from tests.ast_test_support import module_body


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "package_smoke_rehearsal.py"
TEST_PATH = ROOT / "tests" / "test_package_smoke_rehearsal.py"


def _function_names(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    tree = compile(source, str(path), "exec", flags=ast.PyCF_ONLY_AST)
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_package_rehearsal_runtime_targets_split_helper() -> None:
    assert "package_smoke_rehearsal_support.py" in SCRIPT_PATH.read_text(
        encoding="utf-8"
    )


def test_package_rehearsal_runtime_stays_under_split_budget() -> None:
    assert len(SCRIPT_PATH.read_text(encoding="utf-8").splitlines()) <= 220


def test_package_rehearsal_runtime_keeps_logic_defs_out_of_monolith() -> None:
    function_names = _function_names(SCRIPT_PATH)

    assert "result_payload" not in function_names
    assert "run_package_smoke_rehearsal" not in function_names
    assert "subprocess_runner" not in function_names
    assert "run_tool_check" not in function_names


def test_package_rehearsal_tests_share_support_module() -> None:
    assert (
        "from tests.package_smoke_rehearsal_test_support import"
        in TEST_PATH.read_text(encoding="utf-8")
    )
