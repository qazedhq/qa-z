"""Release-script routing tests for the worktree commit plan helper."""

from __future__ import annotations

from tests.worktree_commit_plan_test_support import load_plan_module


def test_commit_plan_assigns_alpha_release_support_surfaces_to_closure_batch() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            " M scripts/alpha_release_artifact_smoke.py",
            " M scripts/alpha_release_bundle_manifest.py",
            "?? scripts/alpha_release_truth_validator.py",
            "?? scripts/package_smoke_rehearsal.py",
            "?? scripts/package_smoke_rehearsal_support.py",
            " M tests/test_alpha_release_artifact_smoke_architecture.py",
            " M tests/test_alpha_release_bundle_manifest.py",
            "?? tests/test_alpha_release_truth_validator.py",
            "?? tests/test_beta_no_release_decision_docs.py",
            "?? tests/test_package_smoke_rehearsal.py",
            "?? tests/test_package_smoke_rehearsal_architecture.py",
            " M tests/alpha_release_artifact_smoke_test_support.py",
            " M tests/alpha_release_bundle_manifest_test_support.py",
            "?? tests/package_smoke_rehearsal_test_support.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["alpha_release_closure"]["changed_paths"] == [
        "scripts/alpha_release_artifact_smoke.py",
        "scripts/alpha_release_bundle_manifest.py",
        "scripts/alpha_release_truth_validator.py",
        "scripts/package_smoke_rehearsal.py",
        "scripts/package_smoke_rehearsal_support.py",
        "tests/test_alpha_release_artifact_smoke_architecture.py",
        "tests/test_alpha_release_bundle_manifest.py",
        "tests/test_alpha_release_truth_validator.py",
        "tests/test_beta_no_release_decision_docs.py",
        "tests/test_package_smoke_rehearsal.py",
        "tests/test_package_smoke_rehearsal_architecture.py",
        "tests/alpha_release_artifact_smoke_test_support.py",
        "tests/alpha_release_bundle_manifest_test_support.py",
        "tests/package_smoke_rehearsal_test_support.py",
    ]
    assert result["unassigned_source_paths"] == []


def test_commit_plan_routes_auth_demo_semgrep_rule_contract() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(["?? tests/test_auth_demo_semgrep_rules.py"])
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert batches["current_truth_release_surface"]["changed_paths"] == [
        "tests/test_auth_demo_semgrep_rules.py"
    ]
    assert result["unassigned_source_paths"] == []
