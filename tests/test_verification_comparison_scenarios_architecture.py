from __future__ import annotations

from pathlib import Path


def test_verification_comparison_scenarios_live_in_split_file() -> None:
    split_source = Path("tests/test_verification_comparison_scenarios.py").read_text(
        encoding="utf-8"
    )
    verification_source = Path("tests/test_verification.py").read_text(encoding="utf-8")

    for test_name in (
        "test_fast_check_comparison_classifies_resolved_still_and_regressed",
        "test_deep_finding_comparison_uses_relaxed_identity_for_message_changes",
        "test_verdict_improved_when_existing_blockers_resolve_without_new_issues",
        "test_verdict_regressed_when_candidate_introduces_only_new_blockers",
        "test_one_sided_deep_artifacts_make_verification_not_comparable",
        "test_count_only_deep_artifacts_force_not_comparable_verification",
    ):
        assert test_name in split_source
        assert test_name not in verification_source


def test_verification_main_test_file_stays_under_split_budget() -> None:
    line_count = len(
        Path("tests/test_verification.py").read_text(encoding="utf-8").splitlines()
    )

    assert line_count <= 100
