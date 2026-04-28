"""Architecture tests for the alpha release artifact smoke seam."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_artifact_smoke.py"
TEST_PATH = ROOT / "tests" / "test_alpha_release_artifact_smoke.py"


def _function_names(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    tree = compile(source, str(path), "exec", flags=ast.PyCF_ONLY_AST)
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_artifact_smoke_runtime_targets_split_helper() -> None:
    assert "alpha_release_artifact_smoke_support.py" in SCRIPT_PATH.read_text(
        encoding="utf-8"
    )


def test_artifact_smoke_runtime_stays_under_split_budget() -> None:
    assert len(SCRIPT_PATH.read_text(encoding="utf-8").splitlines()) <= 220


def test_artifact_smoke_runtime_keeps_logic_defs_out_of_monolith() -> None:
    function_names = _function_names(SCRIPT_PATH)

    assert "result_payload" not in function_names
    assert "artifact_label" not in function_names
    assert "venv_python_path" not in function_names
    assert "venv_script_path" not in function_names
    assert "validation_code" not in function_names
    assert "command_detail" not in function_names
    assert "smoke_artifact" not in function_names
    assert "run_artifact_smoke" not in function_names


def test_artifact_smoke_tests_share_support_module() -> None:
    assert (
        "from tests.alpha_release_artifact_smoke_test_support import"
        in TEST_PATH.read_text(encoding="utf-8")
    )
