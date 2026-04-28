"""Architecture tests for alpha release gate seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

from tests.alpha_release_gate_test_support import (
    CLI_TEST_PATH,
    EVIDENCE_TEST_PATH,
    GATE_TEST_PATH,
    OPTIONS_TEST_PATH,
    RENDER_TEST_PATH,
    SCRIPT_PATH,
    load_gate_evidence_module,
    load_gate_module,
)


def _function_names(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    tree = compile(source, str(path), "exec", flags=ast.PyCF_ONLY_AST)
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_alpha_release_gate_evidence_module_exports_match_surface() -> None:
    gate_module = load_gate_module()
    evidence_module = load_gate_evidence_module()

    assert (
        evidence_module.release_evidence_for_command
        is gate_module.release_evidence_for_command
    )
    assert (
        evidence_module.release_evidence_consistency_errors
        is gate_module.release_evidence_consistency_errors
    )
    assert (
        evidence_module.release_evidence_consistency_next_actions
        is gate_module.release_evidence_consistency_next_actions
    )
    assert (
        evidence_module.render_alpha_release_gate_human
        is gate_module.render_alpha_release_gate_human
    )
    assert (
        evidence_module.render_release_evidence_lines
        is gate_module.render_release_evidence_lines
    )


def test_alpha_release_gate_keeps_evidence_defs_out_of_monolith() -> None:
    function_names = _function_names(SCRIPT_PATH)

    assert "release_evidence_for_command" not in function_names
    assert "release_evidence_consistency_errors" not in function_names
    assert "release_evidence_consistency_next_actions" not in function_names
    assert "render_alpha_release_gate_human" not in function_names
    assert "render_release_evidence_lines" not in function_names
    assert "render_worktree_plan_attention_lines" not in function_names
    assert "render_nested_artifact_lines" not in function_names
    assert "classify_gate_failure" not in function_names
    assert "classify_gate_failures" not in function_names


def test_alpha_release_gate_script_targets_split_evidence_module() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "alpha_release_gate_evidence.py" in source


def test_alpha_release_gate_script_stays_under_line_budget() -> None:
    line_count = sum(1 for _ in SCRIPT_PATH.open(encoding="utf-8"))

    assert line_count <= 1150


def test_alpha_release_gate_evidence_test_pack_stays_split() -> None:
    line_count = sum(1 for _ in GATE_TEST_PATH.open(encoding="utf-8"))

    assert EVIDENCE_TEST_PATH.exists()
    assert RENDER_TEST_PATH.exists()
    assert OPTIONS_TEST_PATH.exists()
    assert CLI_TEST_PATH.exists()
    assert line_count <= 540


def test_alpha_release_gate_split_test_packs_share_support_module() -> None:
    for path in (
        GATE_TEST_PATH,
        EVIDENCE_TEST_PATH,
        RENDER_TEST_PATH,
        OPTIONS_TEST_PATH,
        CLI_TEST_PATH,
    ):
        assert "from tests.alpha_release_gate_test_support import" in path.read_text(
            encoding="utf-8"
        )
