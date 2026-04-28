"""Architecture tests for review-packet seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.reporters.review_packet as review_packet_module
import qa_z.reporters.review_packet_contract as review_packet_contract_module
import qa_z.reporters.review_packet_contract_markdown as contract_markdown_module
import qa_z.reporters.review_packet_render as review_packet_render_module
import qa_z.reporters.review_packet_sections as review_packet_sections_module


def _review_packet_function_names() -> set[str]:
    source = Path(review_packet_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(review_packet_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_review_packet_module_keeps_contract_markdown_defs_out_of_monolith() -> None:
    function_names = _review_packet_function_names()

    assert "extract_section" not in function_names
    assert "extract_subsection" not in function_names
    assert "bulletize" not in function_names
    assert "extract_bullet_or_lines" not in function_names


def test_review_packet_module_keeps_section_defs_out_of_monolith() -> None:
    function_names = _review_packet_function_names()

    assert "ordered_failed_checks" not in function_names
    assert "render_failed_check" not in function_names
    assert "check_summary" not in function_names
    assert "failed_check_summary" not in function_names
    assert "evidence_tail" not in function_names
    assert "render_selection_markdown" not in function_names
    assert "format_check_list" not in function_names
    assert "render_deep_findings_markdown" not in function_names
    assert "format_deep_check_run_sentence" not in function_names
    assert "format_affected_files" not in function_names
    assert "format_grouped_finding" not in function_names


def test_review_packet_contract_markdown_module_exposes_helpers() -> None:
    assert callable(contract_markdown_module.extract_section)
    assert callable(contract_markdown_module.extract_subsection)
    assert callable(contract_markdown_module.bulletize)
    assert callable(contract_markdown_module.extract_bullet_or_lines)


def test_review_packet_sections_module_exposes_helpers() -> None:
    assert callable(review_packet_sections_module.ordered_failed_checks)
    assert callable(review_packet_sections_module.render_failed_check)
    assert callable(review_packet_sections_module.check_summary)
    assert callable(review_packet_sections_module.render_deep_findings_markdown)


def test_review_packet_contract_module_exports_match_surface() -> None:
    assert (
        review_packet_contract_module.contract_output_dir
        is review_packet_module.contract_output_dir
    )
    assert (
        review_packet_contract_module.find_latest_contract
        is review_packet_module.find_latest_contract
    )
    assert (
        review_packet_contract_module.load_contract_review_context
        is review_packet_module.load_contract_review_context
    )


def test_review_packet_render_module_exports_match_surface() -> None:
    assert (
        review_packet_render_module.render_review_packet
        is review_packet_module.render_review_packet
    )
    assert (
        review_packet_render_module.review_packet_json
        is review_packet_module.review_packet_json
    )
    assert (
        review_packet_render_module.render_run_review_packet
        is review_packet_module.render_run_review_packet
    )
    assert (
        review_packet_render_module.run_review_packet_json
        is review_packet_module.run_review_packet_json
    )
    assert (
        review_packet_render_module.write_review_artifacts
        is review_packet_module.write_review_artifacts
    )


def test_review_packet_surface_avoids_importlib_facades() -> None:
    source = Path("src/qa_z/reporters/review_packet.py").read_text(encoding="utf-8")

    assert "importlib.import_module" not in source
