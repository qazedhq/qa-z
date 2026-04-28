"""Architecture tests for internal repair-prompt helper seams."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.reporters.repair_prompt as repair_prompt_module
import qa_z.reporters.repair_prompt_failures as repair_prompt_failures_module
import qa_z.reporters.repair_prompt_sections as repair_prompt_sections_module


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


def test_repair_prompt_module_keeps_failure_defs_out_of_monolith() -> None:
    function_names = _repair_prompt_function_names()

    assert "sorted_failures" not in function_names
    assert "failure_context" not in function_names
    assert "ordered_candidate_files" not in function_names
    assert "default_failure_summary" not in function_names
    assert "fix_priority" not in function_names


def test_repair_prompt_module_keeps_section_defs_out_of_monolith() -> None:
    function_names = _repair_prompt_function_names()

    assert "render_optional_list" not in function_names
    assert "render_failure_markdown" not in function_names
    assert "render_security_findings" not in function_names
    assert "evidence_tail" not in function_names
    assert "format_command" not in function_names
    assert "format_list" not in function_names
    assert "format_inline_code_list" not in function_names
    assert "format_severity_summary_dict" not in function_names
    assert "suggested_fix_order" not in function_names
    assert "done_when_items" not in function_names
    assert "has_blocking_deep_findings" not in function_names
    assert "blocking_grouped_findings" not in function_names
    assert "blocking_severities" not in function_names
    assert "format_grouped_finding" not in function_names
    assert "unique_preserve_order" not in function_names
    assert "utc_now" not in function_names


def test_repair_prompt_failures_module_exposes_helpers() -> None:
    assert callable(repair_prompt_failures_module.sorted_failures)
    assert callable(repair_prompt_failures_module.failure_context)
    assert callable(repair_prompt_failures_module.fix_priority)


def test_repair_prompt_sections_module_exposes_helpers() -> None:
    assert callable(repair_prompt_sections_module.render_failure_markdown)
    assert callable(repair_prompt_sections_module.render_security_findings)
    assert callable(repair_prompt_sections_module.done_when_items)
