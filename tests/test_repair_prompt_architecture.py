"""Architecture tests for repair-prompt seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.reporters.repair_prompt as repair_prompt_module
import qa_z.reporters.repair_prompt_artifacts as repair_prompt_artifacts_module
import qa_z.reporters.repair_prompt_packet as repair_prompt_packet_module
import qa_z.reporters.repair_prompt_render as repair_prompt_render_module


def _repair_prompt_function_names() -> set[str]:
    source = Path(repair_prompt_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(repair_prompt_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_repair_prompt_packet_module_exports_match_surface() -> None:
    assert (
        repair_prompt_packet_module.build_repair_packet
        is repair_prompt_module.build_repair_packet
    )


def test_repair_prompt_render_module_exports_match_surface() -> None:
    assert (
        repair_prompt_render_module.render_repair_prompt
        is repair_prompt_module.render_repair_prompt
    )


def test_repair_prompt_artifacts_module_exports_match_surface() -> None:
    assert (
        repair_prompt_artifacts_module.write_repair_artifacts
        is repair_prompt_module.write_repair_artifacts
    )
    assert (
        repair_prompt_artifacts_module.repair_packet_json
        is repair_prompt_module.repair_packet_json
    )


def test_repair_prompt_module_keeps_public_packet_defs_out_of_monolith() -> None:
    function_names = _repair_prompt_function_names()

    assert "build_repair_packet" not in function_names
    assert "render_repair_prompt" not in function_names
    assert "write_repair_artifacts" not in function_names
    assert "repair_packet_json" not in function_names


def test_repair_prompt_surface_avoids_importlib_facades() -> None:
    source = Path("src/qa_z/reporters/repair_prompt.py").read_text(encoding="utf-8")

    assert "importlib.import_module" not in source


def test_repair_prompt_regression_pack_stays_split() -> None:
    prompt_lines = len(
        Path("tests/test_repair_prompt.py").read_text(encoding="utf-8").splitlines()
    )
    contract_lines = len(
        Path("tests/test_repair_prompt_contracts.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )
    review_lines = len(
        Path("tests/test_review_packet_runtime.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert prompt_lines <= 280, f"test_repair_prompt.py exceeded budget: {prompt_lines}"
    assert contract_lines <= 140, (
        f"test_repair_prompt_contracts.py exceeded budget: {contract_lines}"
    )
    assert review_lines <= 220, (
        f"test_review_packet_runtime.py exceeded budget: {review_lines}"
    )
