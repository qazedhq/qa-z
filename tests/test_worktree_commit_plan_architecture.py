"""Architecture tests for worktree commit plan seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "worktree_commit_plan.py"
TEST_PATH = ROOT / "tests" / "test_worktree_commit_plan.py"
OUTPUT_TEST_PATH = ROOT / "tests" / "test_worktree_commit_plan_output.py"
FILTER_TEST_PATH = ROOT / "tests" / "test_worktree_commit_plan_filtering.py"
CLI_TEST_PATH = ROOT / "tests" / "test_worktree_commit_plan_cli.py"


def _function_names(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    tree = compile(source, str(path), "exec", flags=ast.PyCF_ONLY_AST)
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_worktree_commit_plan_runtime_targets_split_helper() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "worktree_commit_plan_support.py" in source
    assert "sys.dont_write_bytecode = True" in source


def test_worktree_commit_plan_runtime_stays_under_split_budget() -> None:
    line_count = len(SCRIPT_PATH.read_text(encoding="utf-8").splitlines())

    assert line_count <= 420


def test_worktree_commit_plan_runtime_keeps_analysis_defs_out_of_monolith() -> None:
    function_names = _function_names(SCRIPT_PATH)

    assert "normalize_path" not in function_names
    assert "parse_status_line" not in function_names
    assert "status_paths" not in function_names
    assert "is_generated_artifact" not in function_names
    assert "is_source_like" not in function_names
    assert "owner_override_for_path" not in function_names
    assert "build_staging_plan" not in function_names
    assert "next_actions" not in function_names
    assert "analyze_paths" not in function_names
    assert "analyze_status_lines" not in function_names
    assert "filter_payload_for_batch" not in function_names
    assert "render_human" not in function_names


def test_worktree_commit_plan_tests_share_support_module() -> None:
    assert "from tests.worktree_commit_plan_test_support import" in TEST_PATH.read_text(
        encoding="utf-8"
    )
    assert (
        "from tests.worktree_commit_plan_test_support import"
        in OUTPUT_TEST_PATH.read_text(encoding="utf-8")
    )
    assert (
        "from tests.worktree_commit_plan_test_support import"
        in FILTER_TEST_PATH.read_text(encoding="utf-8")
    )
    assert (
        "from tests.worktree_commit_plan_test_support import"
        in CLI_TEST_PATH.read_text(encoding="utf-8")
    )


def test_worktree_commit_plan_main_test_file_stays_under_split_budget() -> None:
    line_count = len(TEST_PATH.read_text(encoding="utf-8").splitlines())

    assert line_count <= 720


def test_worktree_commit_plan_runtime_has_cli_entrypoint_guard() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    assert 'if __name__ == "__main__":' in source
    assert "raise SystemExit(main())" in source
