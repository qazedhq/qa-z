from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RELEASE_HANDOFF_TEST_PATH = ROOT / "tests" / "test_current_truth_release_handoff.py"
RELEASE_CONTINUITY_TEST_PATH = (
    ROOT / "tests" / "test_current_truth_release_continuity.py"
)
WORKTREE_COMMIT_PLAN_TEST_PATH = (
    ROOT / "tests" / "test_current_truth_worktree_commit_plan.py"
)


def test_current_truth_release_surfaces_live_in_split_pack() -> None:
    main_text = (ROOT / "tests" / "test_current_truth.py").read_text(encoding="utf-8")
    split_text = (ROOT / "tests" / "test_current_truth_release_surfaces.py").read_text(
        encoding="utf-8"
    )

    moved_tests = [
        "test_release_target_is_frozen_across_public_surfaces",
        "test_runtime_package_version_matches_release_metadata",
        "test_worktree_commit_plan_names_release_closure_boundary",
        "test_worktree_triage_reflects_current_benchmark_ignore_policy",
        "test_alpha_closure_readiness_snapshot_is_pinned",
    ]

    for name in moved_tests:
        assert f"def {name}" not in main_text
        assert f"def {name}" in split_text


def test_current_truth_main_file_stays_under_split_budget() -> None:
    line_count = len(
        (ROOT / "tests" / "test_current_truth.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 1150


def test_current_truth_release_handoff_surfaces_live_in_split_pack() -> None:
    split_text = (ROOT / "tests" / "test_current_truth_release_surfaces.py").read_text(
        encoding="utf-8"
    )
    handoff_text = RELEASE_HANDOFF_TEST_PATH.read_text(encoding="utf-8")

    moved_tests = [
        "test_release_plan_marks_completed_commit_split_truthfully",
        "test_alpha_publish_handoff_pins_remote_blocker_and_next_commands",
    ]

    for name in moved_tests:
        assert f"def {name}" not in split_text
        assert f"def {name}" in handoff_text


def test_current_truth_release_continuity_surfaces_live_in_split_pack() -> None:
    main_text = (ROOT / "tests" / "test_current_truth.py").read_text(encoding="utf-8")
    continuity_text = RELEASE_CONTINUITY_TEST_PATH.read_text(encoding="utf-8")

    moved_tests = [
        "test_release_continuity_docs_cover_loop_local_prepared_action_context",
    ]

    for name in moved_tests:
        assert f"def {name}" not in main_text
        assert f"def {name}" in continuity_text


def test_current_truth_worktree_commit_plan_surfaces_live_in_split_pack() -> None:
    main_text = (ROOT / "tests" / "test_current_truth.py").read_text(encoding="utf-8")
    worktree_text = WORKTREE_COMMIT_PLAN_TEST_PATH.read_text(encoding="utf-8")

    moved_tests = [
        "test_docs_document_worktree_commit_plan_helper",
        "test_artifact_schema_documents_runtime_artifact_cleanup_contract",
    ]

    for name in moved_tests:
        assert f"def {name}" not in main_text
        assert f"def {name}" in worktree_text


def test_current_truth_release_surfaces_file_stays_under_split_budget() -> None:
    line_count = len(
        (ROOT / "tests" / "test_current_truth_release_surfaces.py")
        .read_text(encoding="utf-8")
        .splitlines()
    )

    assert line_count <= 700
