"""Architecture tests for shared runner model seams."""

from __future__ import annotations

import ast
from pathlib import Path

from tests.ast_test_support import module_body


ROOT = Path(__file__).resolve().parents[1]
MODELS_PATH = ROOT / "src" / "qa_z" / "runners" / "models.py"


def _imported_modules(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    tree = compile(source, str(path), "exec", flags=ast.PyCF_ONLY_AST)
    modules: set[str] = set()
    for node in module_body(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def test_runner_models_define_explicit_public_surface() -> None:
    source = MODELS_PATH.read_text(encoding="utf-8")

    assert "__all__ = [" in source
    for name in (
        "CheckPlan",
        "CheckResult",
        "CheckSpec",
        "ExecutionMode",
        "GroupedFinding",
        "RunSummary",
        "SelectionSummary",
        "SemgrepCheckPolicy",
        "SemgrepFinding",
    ):
        assert f'"{name}"' in source


def test_runner_models_only_depend_on_diffing_from_repo() -> None:
    imported_modules = _imported_modules(MODELS_PATH)
    qa_z_imports = {name for name in imported_modules if name.startswith("qa_z.")}

    assert qa_z_imports == {"qa_z.diffing.models"}
