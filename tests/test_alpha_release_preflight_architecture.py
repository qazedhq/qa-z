from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body
from tests.alpha_release_preflight_test_support import (
    CLI_RENDER_TEST_PATH,
    REMOTE_REFS_TEST_PATH,
    REMOTE_TEST_PATH,
)


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_preflight.py"
MAIN_TEST_PATH = ROOT / "tests" / "test_alpha_release_preflight.py"


def _function_names(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8")
    tree = compile(source, str(path), "exec", flags=ast.PyCF_ONLY_AST)
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def test_alpha_release_preflight_remote_contracts_live_in_split_pack() -> None:
    main_text = (ROOT / "tests" / "test_alpha_release_preflight.py").read_text(
        encoding="utf-8"
    )
    split_text = (ROOT / "tests" / "test_alpha_release_preflight_remote.py").read_text(
        encoding="utf-8"
    )

    moved_tests = [
        "test_preflight_passes_when_local_clean_and_empty_remote_reachable",
        "test_preflight_preserves_github_repository_metadata_in_payload",
        "test_preflight_direct_publish_guidance_uses_repository_default_branch",
        "test_preflight_fails_when_remote_is_missing",
        "test_preflight_dirty_worktree_failure_has_next_action",
        "test_preflight_skip_remote_marks_repository_probe_state_skipped",
        "test_preflight_allows_configured_origin_when_expected_url_matches",
        "test_preflight_blocks_unexpected_origin_when_expectation_is_omitted",
        "test_preflight_allows_equivalent_origin_url_forms",
        "test_preflight_allows_ssh_url_origin_form",
        "test_preflight_allows_ssh_url_origin_form_with_explicit_port",
        "test_preflight_allows_schemeless_github_origin_url_form",
        "test_preflight_fails_when_expected_origin_targets_different_repository",
        "test_preflight_origin_target_mismatch_without_origin_uses_add_origin_command",
        "test_preflight_payload_records_expected_origin_target_when_github_url",
        "test_preflight_payload_records_missing_origin_state_when_origin_unconfigured",
        "test_preflight_payload_guides_origin_bootstrap_when_remote_checks_are_skipped",
        "test_preflight_payload_guides_remote_checks_when_origin_is_ready",
        "test_preflight_payload_records_actual_origin_url_when_origin_is_configured",
        "test_preflight_payload_records_actual_origin_target_when_origin_is_github",
        "test_parse_github_repository_target_accepts_schemeless_github_url",
    ]

    for name in moved_tests:
        assert f"def {name}" not in main_text
        assert f"def {name}" in split_text


def test_alpha_release_preflight_main_file_stays_under_split_budget() -> None:
    line_count = len(MAIN_TEST_PATH.read_text(encoding="utf-8").splitlines())

    assert line_count <= 260


def test_alpha_release_preflight_cli_and_render_surfaces_live_in_split_pack() -> None:
    main_text = (ROOT / "tests" / "test_alpha_release_preflight.py").read_text(
        encoding="utf-8"
    )
    split_text = (
        ROOT / "tests" / "test_alpha_release_preflight_cli_render.py"
    ).read_text(encoding="utf-8")

    moved_tests = [
        "test_preflight_cli_accepts_existing_ref_pr_path_flag",
        "test_preflight_cli_accepts_expected_repository_override",
        "test_preflight_cli_accepts_expected_origin_url_override",
        "test_preflight_cli_can_emit_json_summary",
        "test_preflight_cli_can_write_json_output",
        "test_preflight_cli_can_write_output_without_printing_json",
        "test_preflight_cli_reuses_last_known_probe_from_existing_output",
        "test_preflight_cli_ignores_last_known_probe_for_mismatched_repository",
        "test_result_payload_marks_last_known_probe_as_stale_after_24h",
        "test_result_payload_marks_current_probe_as_current",
        "test_render_preflight_human_prints_remote_blocker_decision",
        "test_render_preflight_human_prints_missing_origin_state",
        "test_render_preflight_human_prints_last_known_probe_basis",
        "test_render_preflight_human_prints_ready_for_remote_checks_decision",
        "test_render_preflight_human_prints_publish_checklist",
        "test_preflight_cli_json_preserves_failed_exit_code",
        "test_preflight_cli_writes_failed_output_with_counters",
    ]

    for name in moved_tests:
        assert f"def {name}" not in main_text
        assert f"def {name}" in split_text


def test_alpha_release_preflight_runtime_targets_split_evidence_module() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "alpha_release_preflight_evidence.py" in source


def test_alpha_release_preflight_runtime_stays_under_split_budget() -> None:
    line_count = len(SCRIPT_PATH.read_text(encoding="utf-8").splitlines())

    assert line_count <= 950


def test_alpha_release_preflight_runtime_keeps_decision_defs_out_of_monolith() -> None:
    function_names = _function_names(SCRIPT_PATH)

    assert "last_known_probe_snapshot" not in function_names
    assert "probe_freshness_fields" not in function_names
    assert "publish_strategy_for_result" not in function_names
    assert "publish_checklist_for_result" not in function_names
    assert "release_path_state_for_result" not in function_names
    assert "release_path_state_from_payload" not in function_names
    assert "remote_readiness_for_result" not in function_names
    assert "next_actions_for_result" not in function_names
    assert "next_commands_for_result" not in function_names
    assert "result_payload" not in function_names
    assert "render_preflight_human" not in function_names
    assert "classify_remote_decision" not in function_names


def test_alpha_release_preflight_split_tests_share_support_module() -> None:
    expected_import = "from tests.alpha_release_preflight_test_support import"

    for path in (
        MAIN_TEST_PATH,
        REMOTE_TEST_PATH,
        REMOTE_REFS_TEST_PATH,
        CLI_RENDER_TEST_PATH,
    ):
        assert expected_import in path.read_text(encoding="utf-8")


def test_alpha_release_preflight_remote_ref_contracts_live_in_split_pack() -> None:
    remote_text = REMOTE_TEST_PATH.read_text(encoding="utf-8")
    split_text = REMOTE_REFS_TEST_PATH.read_text(encoding="utf-8")

    moved_tests = [
        "test_preflight_fails_when_configured_origin_does_not_match_expected_url",
        "test_preflight_fails_when_remote_has_any_refs",
        "test_preflight_allows_existing_refs_when_explicitly_requested",
        "test_preflight_fails_when_existing_refs_include_release_tag_even_if_allowed",
        "test_preflight_fails_for_wrong_github_repository_target",
        "test_preflight_fails_for_non_github_repository_url",
        "test_preflight_missing_repository_payload_handles_github_error_body",
    ]

    for name in moved_tests:
        assert f"def {name}" not in remote_text
        assert f"def {name}" in split_text


def test_alpha_release_preflight_remote_file_stays_under_split_budget() -> None:
    line_count = len(REMOTE_TEST_PATH.read_text(encoding="utf-8").splitlines())

    assert REMOTE_REFS_TEST_PATH.exists()
    assert line_count <= 620
