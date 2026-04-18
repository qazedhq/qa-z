"""Regression tests for QA-Z current-truth surfaces."""

from __future__ import annotations

from pathlib import Path

import yaml

from qa_z.config import EXAMPLE_CONFIG
from qa_z.config import COMMAND_GUIDANCE


ROOT = Path(__file__).resolve().parents[1]


def test_command_guidance_matches_landed_review_and_repair_prompt_surface() -> None:
    review = COMMAND_GUIDANCE["review"]
    repair_prompt = COMMAND_GUIDANCE["repair-prompt"]

    assert "scaffolded, not fully implemented yet" not in review
    assert "scaffolded, not fully implemented yet" not in repair_prompt
    assert "review packet" in review
    assert "local artifacts" in review
    assert "repair packet" in repair_prompt
    assert "failed fast checks" in repair_prompt


def test_gitignore_treats_generated_benchmark_summary_and_report_as_local() -> None:
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert "benchmarks/results/work/" in lines
    assert "benchmarks/results/summary.json" in lines
    assert "benchmarks/results/report.md" in lines
    assert "!benchmarks/fixtures/**/repo/.qa-z/**" in lines


def test_legacy_benchmark_readme_points_to_plural_benchmarks_directory() -> None:
    text = (ROOT / "benchmark" / "README.md").read_text(encoding="utf-8")

    assert "../benchmarks/" in text
    assert "historical placeholder" in text


def test_release_target_is_frozen_across_public_surfaces() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release_plan = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-18-github-repository-release.md"
    ).read_text(encoding="utf-8")
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )
    triage = (ROOT / "docs" / "reports" / "worktree-triage.md").read_text(
        encoding="utf-8"
    )
    release_notes = (ROOT / "docs" / "releases" / "v0.9.8-alpha.md").read_text(
        encoding="utf-8"
    )
    assert 'version = "0.9.8a0"' in pyproject
    assert "v0.9.8-alpha" in readme
    assert "v0.9.x-alpha" not in readme
    assert "v0.9.8-alpha" in commit_plan
    assert "v0.9.2-alpha" not in commit_plan
    assert "v0.9.8-alpha" in triage
    assert "v0.9.2-alpha as the natural baseline candidate" not in triage
    assert "`pyproject.toml` still says version `0.1.0`" not in release_plan
    assert "Git tag `v0.9.8-alpha`" in release_plan
    assert "Python package `0.9.8a0`" in release_plan
    assert "# QA-Z v0.9.8-alpha" in release_notes
    assert "`0.9.8a0`" in release_notes


def test_worktree_commit_plan_names_release_closure_boundary() -> None:
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )

    assert "## Alpha Release Closure Batch" in commit_plan
    assert "chore: freeze alpha release target and root qa gate" in commit_plan
    assert "`docs/releases/v0.9.8-alpha.md`" in commit_plan
    assert "`qa-z.yaml`" in commit_plan
    assert "Patch-add only the release-target README hunks" in commit_plan
    assert "Patch-add only the version metadata hunks" in commit_plan
    assert (
        "python -m pytest tests/test_current_truth.py tests/test_github_workflow.py -q"
        in commit_plan
    )
    assert "Do not stage root `.qa-z/**`" in commit_plan
    assert "Do not stage `benchmarks/results/**`" in commit_plan


def test_worktree_triage_reflects_current_benchmark_ignore_policy() -> None:
    text = (ROOT / "docs" / "reports" / "worktree-triage.md").read_text(
        encoding="utf-8"
    )

    assert "benchmarks/results/work/" in text
    assert "already ignores" in text
    assert "Local only by default" in text
    assert "Immediate Worktree Guidance" in text
    assert "does not currently ignore `benchmarks/results/report.md`" not in text
    assert "Defer or ignore" not in text


def test_alpha_closure_readiness_snapshot_is_pinned() -> None:
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )
    release_plan = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-18-github-repository-release.md"
    ).read_text(encoding="utf-8")
    release_notes = (ROOT / "docs" / "releases" / "v0.9.8-alpha.md").read_text(
        encoding="utf-8"
    )
    release_pr = (ROOT / "docs" / "releases" / "v0.9.8-alpha-pr.md").read_text(
        encoding="utf-8"
    )
    github_release = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-github-release.md"
    ).read_text(encoding="utf-8")
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "## Alpha Closure Readiness Snapshot" in commit_plan
    assert "latest full local gate pass" in commit_plan
    assert "python -m pytest" in commit_plan
    assert "341 passed" in commit_plan
    assert "341 passed" in release_plan
    assert "`python -m pytest`: 341 passed" in release_notes
    assert "`python -m pytest`: passed, `341 passed" in release_pr
    assert "`python -m pytest`: passed, `341 passed`" in github_release
    assert "340 passed" not in commit_plan
    assert "340 passed" not in release_plan
    assert "340 passed" not in release_notes
    assert "340 passed" not in release_pr
    assert "340 passed" not in github_release
    assert "python -m qa_z benchmark --json" in commit_plan
    assert "python -m qa_z benchmark --json" in release_pr
    assert "python -m qa_z benchmark --json" in github_release
    assert "python -m build --sdist --wheel" in commit_plan
    assert "python -m build --sdist --wheel" in release_plan
    assert "`python -m build --sdist --wheel`: passed" in release_notes
    assert "`python -m build --sdist --wheel`: passed" in release_pr
    assert "`python -m build --sdist --wheel`: passed" in github_release
    assert "50/50 fixtures" in commit_plan
    assert "50/50 fixtures, overall_rate 1.0" in release_pr
    assert "50/50 fixtures, overall_rate 1.0" in github_release
    assert "benchmark summary `snapshot` field" in commit_plan
    assert "python -m ruff check ." in commit_plan
    assert "`python -m ruff check .`: passed" in release_notes
    assert "`python -m ruff check .`: passed" in release_pr
    assert "`python -m ruff check .`: passed" in github_release
    assert "python -m ruff format --check ." in commit_plan
    assert "`python -m ruff format --check .`: 126 files already formatted" in (
        release_notes
    )
    assert "`python -m ruff format --check .`: passed" in release_pr
    assert "`python -m ruff format --check .`: passed" in github_release
    assert "126 files already formatted" in commit_plan
    assert "python -m mypy src tests" in commit_plan
    assert "`python -m mypy src tests`: 82 source files" in release_notes
    assert "`python -m mypy src tests`: passed" in release_pr
    assert "`python -m mypy src tests`: passed" in github_release
    assert "82 source files" in commit_plan
    assert "CLI smoke checks: 17 help surfaces passed" in release_notes
    assert "CLI smoke checks: passed for 17 help surfaces" in release_pr
    assert "CLI smoke checks: passed for 17 help surfaces" in github_release
    assert "Generated Output Policy" in commit_plan
    assert "split the worktree by this commit plan" in commit_plan
    assert "action basis:" in commit_plan
    assert "alpha closure readiness snapshot" in current_state.lower()
    assert "alpha closure readiness snapshot" in roadmap.lower()
    assert "action basis:" in current_state
    assert "action basis:" in roadmap
    assert "benchmarks/results-*" in commit_plan
    assert "docs/releases/v0.9.8-alpha-pr.md" in release_plan
    assert "docs/releases/v0.9.8-alpha-pr.md" in release_notes
    assert "docs/releases/v0.9.8-alpha-github-release.md" in release_plan
    assert "docs/releases/v0.9.8-alpha-github-release.md" in release_notes
    assert "# Release QA-Z v0.9.8-alpha" in release_pr
    assert "# QA-Z v0.9.8-alpha" in github_release
    assert "No live Codex or Claude execution." in release_pr
    assert "No live Codex or Claude execution." in github_release
    assert "No autonomous code editing." in release_pr
    assert "No autonomous code editing." in github_release
    assert "No remote orchestration" in release_pr
    assert "No remote orchestration" in github_release
    assert "GitHub bot comments" in release_pr
    assert "GitHub bot comments" in github_release
    assert "No LLM-only judgment" in release_pr
    assert "No LLM-only judgment" in github_release
    assert "Generated Artifact Policy" in release_pr
    assert "Generated Artifact Policy" in github_release
    assert "Benchmark Snapshot" in release_pr
    assert "Benchmark corpus" in github_release
    assert "Self-inspection" in github_release
    assert "Executor bridge packaging" in github_release
    assert "live-free executor dry-run" in github_release
    assert "no configured `origin` remote" in release_plan
    assert "no configured `origin` remote" in release_pr
    assert "no configured `origin` remote" in github_release
    assert "does not expose a `JustTyping` or `qa-z` repository target" in (
        github_release
    )
    assert "worktree is not releaseable as-is" not in release_plan
    assert "31 tracked modified files" not in release_plan
    assert "- [x] **Step 1: Run full deterministic validation**" in release_plan
    assert "- [x] **Step 2: Run CLI smoke checks**" in release_plan
    assert "- [x] **Step 3: Confirm worktree cleanliness**" in release_plan


def test_release_plan_marks_completed_commit_split_truthfully() -> None:
    release_plan = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-18-github-repository-release.md"
    ).read_text(encoding="utf-8")

    assert "- [x] **Step 1: Confirm no generated runtime artifacts are staged**" in (
        release_plan
    )
    assert "- [x] **Step 2: Commit foundation first**" in release_plan
    assert "- [x] **Step 3: Commit benchmark coverage**" in release_plan
    assert "- [x] **Step 4: Commit planning and autonomy layers**" in release_plan
    assert (
        "- [x] **Step 5: Commit repair-session, publishing, and executor bridge**"
        in release_plan
    )
    assert (
        "- [x] **Step 6: Commit docs, examples, templates, and release reports last**"
        in release_plan
    )

    for commit in (
        "7d39e3e feat: add runner repair and verification foundations",
        "001e719 feat: expand benchmark coverage for typescript and deep policy cases",
        "a32e7fc feat: add self-inspection backlog and task selection workflow",
        "112b98e feat: add autonomy planning loops and loop artifacts",
        "ee4a4e1 feat: add repair session workflow and verification publishing",
        "a52d01e feat: add executor bridge packaging for external repair workflows",
        "0427add docs: add worktree triage and commit plan reports",
    ):
        assert commit in release_plan


def test_alpha_publish_handoff_pins_remote_blocker_and_next_commands() -> None:
    release_plan = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-18-github-repository-release.md"
    ).read_text(encoding="utf-8")
    release_notes = (ROOT / "docs" / "releases" / "v0.9.8-alpha.md").read_text(
        encoding="utf-8"
    )
    release_handoff = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-publish-handoff.md"
    ).read_text(encoding="utf-8")

    assert "docs/releases/v0.9.8-alpha-publish-handoff.md" in release_plan
    assert "docs/releases/v0.9.8-alpha-publish-handoff.md" in release_notes
    assert "no configured `origin` remote" in release_handoff
    assert "does not expose a `JustTyping` or `qa-z` repository target" in (
        release_handoff
    )
    assert "git remote add origin <repository-url>" in release_handoff
    assert "git push -u origin codex/qa-z-bootstrap" in release_handoff
    assert "Release QA-Z v0.9.8-alpha" in release_handoff
    assert "docs/releases/v0.9.8-alpha-pr.md" in release_handoff
    assert "docs/releases/v0.9.8-alpha-github-release.md" in release_handoff
    assert "Do not tag before remote CI passes and the release PR is merged." in (
        release_handoff
    )
    assert "git tag -a v0.9.8-alpha -m" in release_handoff
    assert "python -m qa_z benchmark --json" in release_handoff
    assert (
        "Package-build validation commit: "
        "`f009d14 chore: add release build validation tooling`"
    ) in release_handoff
    assert (
        "git clone --branch codex/qa-z-bootstrap "
        "dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle"
    ) in release_handoff
    assert (
        "Generated artifact hashes are intentionally not pinned in this tracked handoff"
        in release_handoff
    )
    assert "Get-FileHash -Algorithm SHA256" in release_handoff
    assert "git bundle create" in release_handoff
    assert "git bundle verify" in release_handoff
    assert "git bundle list-heads" in release_handoff
    assert "git rev-parse HEAD" in release_handoff
    assert "SHA256: `" not in release_handoff
    for artifact in (
        "dist/qa_z-0.9.8a0.tar.gz",
        "dist/qa_z-0.9.8a0-py3-none-any.whl",
        "dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle",
    ):
        assert artifact in release_handoff


def test_dev_extra_includes_release_build_tooling() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    release_handoff = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-publish-handoff.md"
    ).read_text(encoding="utf-8")

    assert "build>=" in pyproject
    assert 'license = "Apache-2.0"' in pyproject
    assert "license = { text = " not in pyproject
    assert "License :: OSI Approved :: Apache Software License" not in pyproject
    assert "python -m build --sdist --wheel" in release_handoff


def test_generated_vs_frozen_policy_is_documented_and_linked() -> None:
    policy = (ROOT / "docs" / "generated-vs-frozen-evidence-policy.md").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")
    benchmarking = (ROOT / "docs" / "benchmarking.md").read_text(encoding="utf-8")

    assert (
        "`benchmarks/results/summary.json` and `benchmarks/results/report.md`" in policy
    )
    assert "local by default" in policy
    assert "intentional frozen evidence" in policy
    assert "`benchmarks/fixtures/**/repo/.qa-z/**`" in policy

    for text in (readme, schema, benchmarking):
        assert "docs/generated-vs-frozen-evidence-policy.md" in text
        assert "local by default" in text
        assert "intentional frozen evidence" in text


def test_public_github_readiness_files_are_release_aligned() -> None:
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    pr_template = (ROOT / ".github" / "pull_request_template.md").read_text(
        encoding="utf-8"
    )
    bug_template = (ROOT / ".github" / "ISSUE_TEMPLATE" / "bug_report.yml").read_text(
        encoding="utf-8"
    )
    feature_template = (
        ROOT / ".github" / "ISSUE_TEMPLATE" / "feature_request.yml"
    ).read_text(encoding="utf-8")

    for text in (contributing, pr_template):
        assert "python -m ruff format --check ." in text
        assert "python -m ruff check ." in text
        assert "python -m mypy src tests" in text
        assert "python -m pytest" in text
        assert "python -m qa_z fast --selection smart --json" in text
        assert "python -m qa_z deep --selection smart --json" in text
        assert "python -m qa_z benchmark --json" in text
        assert "benchmarks/results/summary.json" in text
        assert "benchmarks/fixtures/**/repo/.qa-z/**" in text

    for text in (
        contributing,
        security,
        pr_template,
        bug_template,
        feature_template,
    ):
        lowered = text.lower()
        assert "live codex" in lowered
        assert "claude" in lowered
        assert "llm-only" in lowered

    assert "v0.9.8-alpha" in security
    assert "deterministic evidence" in bug_template
    assert "deterministic gates" in feature_template


def test_benchmark_summary_snapshot_is_documented_in_artifact_schema() -> None:
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")

    assert "## Benchmark Summary" in schema
    assert "`snapshot`: compact generated benchmark result text" in schema
    assert (
        "derived from `fixtures_passed`, `fixtures_total`, and `overall_rate`" in schema
    )


def test_current_truth_docs_cover_dry_run_publish_and_session_residue() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")

    assert (
        "session dry-run verdict, reason, source, attempt counts, and history signals"
        in readme
    )
    assert "operator summary and recommended actions" in readme
    assert "synthesizes the same residue from `executor_results/history.json`" in readme
    assert "marks the dry-run source as history fallback" in readme
    assert "summary_source: materialized" in readme
    assert (
        "self-inspection now synthesizes the same dry-run residue from that history"
        in readme
    )
    assert (
        "candidate evidence summaries also preserve dry-run provenance as "
        "`source=materialized` or `source=history_fallback`" in readme
    )
    assert (
        "filters runtime-artifact policy gaps through the live ignore policy" in readme
    )
    assert "closes it instead of leaving stale work permanently selectable" in readme
    assert "within-batch fallback-family penalty" in readme
    assert "recommendation-specific commands plus additive `context_paths`" in readme
    assert "Deferred generated cleanup packets" in readme
    assert "`docs/generated-vs-frozen-evidence-policy.md` through `context_paths`" in (
        readme
    )
    assert (
        "`latest_prepared_actions` and `latest_next_recommendations` fields" in readme
    )
    assert "Human `qa-z backlog` output now focuses on open or active items" in readme
    assert (
        "`latest_selected_task_details`, derived directly from the stored latest `selected_tasks.json`"
        in readme
    )
    assert (
        "Human `qa-z select-next` output now echoes each selected task's title,"
        in readme
    )
    assert "selection score, penalty reasons, and compact evidence summary" in readme
    assert "selection penalty and its reasons" in readme
    assert "loop plans now mirror selection score and penalty residue" in readme
    assert "autonomy loop plans now mirror selected-task evidence summaries" in readme
    assert "selected fallback families" in readme
    assert "`latest_selected_fallback_families`" in readme
    assert "Loop-health packets" in readme
    assert "loop-history evidence" in readme
    assert "Autonomy-created repair-session packets" in readme
    assert "bridge-local action context inputs" in readme
    assert "action-context package health" in readme
    assert "missing action-context diagnostics" in readme
    assert (
        "`selection_gap_reason` plus open backlog counts before and after inspection"
        in readme
    )
    assert "`loop_health` summary" in readme
    assert "`stop_reason`" in readme
    assert "no minimum budget" in readme
    assert "`executor_dry_run_verdict` and `executor_dry_run_reason`" in schema
    assert "`executor_dry_run_source`" in schema
    assert "`summary_source`" in schema
    assert "`executor_dry_run_attempt_count`" in schema
    assert "`executor_dry_run_history_signals`" in schema
    assert "`operator_summary` and `recommended_actions`" in schema
    assert "`operator_decision`" in schema
    assert "`executor_dry_run_operator_decision`" in schema
    assert "`executor_dry_run_operator_summary`" in schema
    assert "`executor_dry_run_recommended_actions`" in schema
    assert "synthesized from readable executor history" in schema
    assert "`source=materialized` or `source=history_fallback`" in schema
    assert "`closed_at`" in schema
    assert "`closure_reason`" in schema
    assert "current-batch fallback-family reselection" in schema
    assert "`context_paths`" in schema
    assert "deferred generated cleanup through `triage_and_isolate_changes`" in schema
    assert "`docs/generated-vs-frozen-evidence-policy.md` through `context_paths`" in (
        schema
    )
    assert "`git status --short`" in schema
    assert "`audit_worktree_integration`" in schema
    assert "`latest_prepared_actions`" in schema
    assert "`latest_next_recommendations`" in schema
    assert "`evidence_summary`" in schema
    assert "open session details" in schema
    assert "plain-text `qa-z backlog` view is intentionally operator-focused" in schema
    assert (
        "plain-text `qa-z select-next` output now mirrors compact selected-task details"
        in schema
    )
    assert "`selection_penalty_reasons`" in schema
    assert "`loop_plan.md` now also mirrors `selection_priority_score`" in schema
    assert "`latest_selected_task_details`" in schema
    assert "`latest_selected_fallback_families`" in schema
    assert "latest selected-task details" in schema
    assert "selected fallback families" in schema
    assert "`improve_fallback_diversity`" in schema
    assert "`.qa-z/loops/history.jsonl`" in schema
    assert "`inputs.action_context`" in schema
    assert "`inputs.action_context_missing`" in schema
    assert "`inputs/context/`" in schema
    assert "`selection_penalty` and `selection_penalty_reasons`" in schema
    assert "autonomy loop plans now also mirror selected-task evidence" in schema
    assert "action basis:" in readme
    assert "action basis:" in schema
    assert "benchmarks/results-*" in readme
    assert "benchmarks/results-*" in schema
    assert "intentional frozen evidence" in readme
    assert "intentional frozen evidence" in schema
    assert "`generated_outputs` or `runtime_artifacts`" in readme
    assert "`generated_outputs` or `runtime_artifacts`" in schema
    assert "benchmark-gap evidence preserves the generated benchmark `snapshot`" in (
        readme
    )
    assert "legacy benchmark summaries" in readme
    assert "summary-level benchmark-gap item" in readme
    assert "benchmark-gap evidence preserves the generated benchmark `snapshot`" in (
        schema
    )
    assert "legacy benchmark summaries" in schema
    assert "summary-level benchmark-gap item" in schema
    assert "`selection_gap_reason`" in schema
    assert (
        "`backlog_open_count_before_inspection` and `backlog_open_count_after_inspection`"
        in schema
    )
    assert "`loop_health`" in schema
    assert "`classification`" in schema
    assert "`stale_open_items_closed`" in schema
    assert "`stop_reason`" in schema
    assert "Executor dry-run source:" in schema
    assert "Executor dry-run diagnostic:" in schema
    assert "history_fallback" in schema
    assert "no minimum budget" in schema


def test_current_state_reports_reflect_post_executor_history_baseline() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )
    assert "loop health" in current_state.lower()
    assert "generated versus frozen evidence policy" in current_state.lower()
    assert "structured executor result contract" not in roadmap.lower()
    assert "add an ingest/resume workflow for external execution results" not in (
        current_state.lower()
    )
    assert "empty-loop" in roadmap.lower()
    assert "generated versus frozen evidence policy" in roadmap.lower()


def test_mixed_fast_deep_benchmark_breadth_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    benchmarking = (ROOT / "docs" / "benchmarking.md").read_text(encoding="utf-8")
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    for text in (readme, benchmarking, current_state, roadmap):
        assert "mixed_fast_deep_handoff_dual_surface" in text
        assert "mixed_fast_deep_handoff_ts_lint_python_deep" in text
        assert "mixed_fast_deep_handoff_py_lint_ts_test_dual_deep" in text
        assert "executor_bridge_action_context_inputs" in text
        assert "executor_bridge_missing_action_context_inputs" in text

    assert "mixed fast plus deep interactions" in current_state
    assert "executor bridge action-context packaging coverage" in current_state
    assert "action-context package health" in current_state
    assert "bridge-local action context copying" in benchmarking
    assert "missing action-context guide and stdout diagnostics" in readme
    assert "guide/stdout missing-context diagnostics" in benchmarking
    assert "first mixed fast plus deep executed fixture" in roadmap
    assert "second mixed fast plus deep executed fixture" in roadmap
    assert "third mixed fast plus deep executed fixture" in roadmap


def test_executor_dry_run_operator_benchmark_density_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    benchmarking = (ROOT / "docs" / "benchmarking.md").read_text(encoding="utf-8")
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    for text in (readme, benchmarking, current_state, roadmap):
        assert "executor_dry_run_validation_noop_operator_actions" in text

    assert "recommended_action_ids" in benchmarking
    assert "operator summary" in readme
    assert "operator-action fixture" in current_state


def test_executor_dry_run_retry_noop_benchmark_density_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    benchmarking = (ROOT / "docs" / "benchmarking.md").read_text(encoding="utf-8")
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )
    repair_sessions = (ROOT / "docs" / "repair-sessions.md").read_text(encoding="utf-8")
    pre_live_safety = (ROOT / "docs" / "pre-live-executor-safety.md").read_text(
        encoding="utf-8"
    )

    fixture_names = [
        "executor_dry_run_repeated_rejected_operator_actions",
        "executor_dry_run_repeated_noop_operator_actions",
        "executor_dry_run_blocked_mixed_history_operator_actions",
        "executor_dry_run_empty_history_operator_actions",
        "executor_dry_run_scope_validation_operator_actions",
        "executor_dry_run_missing_noop_explanation_operator_actions",
    ]
    for text in (readme, benchmarking, current_state, roadmap):
        for fixture_name in fixture_names:
            assert fixture_name in text

    assert "repeated rejected" in benchmarking
    assert "repeated no-op" in benchmarking
    assert "repeated no-op rule attention" in benchmarking
    assert "empty-history rule attention" in benchmarking
    assert "all committed executor dry-run fixtures" in benchmarking
    assert "complete dry-run rule buckets" in benchmarking
    assert "dry-run rule catalog" in benchmarking
    assert "dry-run rule catalog" in schema
    assert "extends the frozen safety package" in benchmarking
    assert "extends the frozen safety package" in schema
    assert "executor safety rule catalog" in benchmarking
    assert "executor safety rule catalog" in schema
    assert "safety rule count" in readme
    assert "safety rule count" in schema
    assert "guide safety rule count" in readme
    assert "guide safety rule count" in schema
    assert "bridge stdout return pointers" in readme
    assert "bridge stdout return pointers" in schema
    assert "template placeholder guidance" in readme
    assert "template placeholder guidance" in schema
    assert "bridge stdout return pointers" in repair_sessions
    assert "template placeholder guidance" in repair_sessions
    assert "executor safety rule catalog" in pre_live_safety
    assert "six-rule frozen pre-live set" in pre_live_safety
    assert "safety rule count" in pre_live_safety
    assert "dry-run rule catalog" in pre_live_safety
    assert "executor_history_recorded" in pre_live_safety
    assert "operator summary and recommended action residue" in readme
    assert "action-aligned next recommendations" in benchmarking
    assert "all committed dry-run fixtures" in current_state
    assert "all committed dry-run fixtures" in roadmap


def test_example_config_only_advertises_landed_deep_execution_surface() -> None:
    public_text = (ROOT / "qa-z.yaml.example").read_text(encoding="utf-8")
    example = yaml.safe_load(public_text)

    assert EXAMPLE_CONFIG == public_text
    assert "deep" not in example.get("checks", {})
    assert [check["id"] for check in example["deep"]["checks"]] == ["sg_scan"]
    assert "property" not in public_text
    assert "mutation" not in public_text
    assert "e2e_smoke" not in public_text


def test_root_release_config_keeps_repository_gate_python_only() -> None:
    public_text = (ROOT / "README.md").read_text(encoding="utf-8")
    root_config_text = (ROOT / "qa-z.yaml").read_text(encoding="utf-8")
    root_config = yaml.safe_load(root_config_text)

    assert root_config["project"]["languages"] == ["python"]
    assert [check["id"] for check in root_config["fast"]["checks"]] == [
        "py_lint",
        "py_format",
        "py_type",
        "py_test",
    ]
    assert [check["id"] for check in root_config["deep"]["checks"]] == ["sg_scan"]
    assert root_config["deep"]["checks"][0]["run"] == [
        "semgrep",
        "--json",
        "src",
        "tests",
    ]
    assert "ts_lint" not in root_config_text
    assert "ts_type" not in root_config_text
    assert "ts_test" not in root_config_text
    assert "root `qa-z.yaml` is Python-only" in public_text
    assert "root deep scan is scoped to `src` and `tests`" in public_text
    assert "TypeScript checks remain covered by `qa-z.yaml.example`" in public_text


def test_agent_templates_reflect_current_alpha_workflow_and_boundaries() -> None:
    template_paths = [
        ROOT / "templates" / "AGENTS.md",
        ROOT / "templates" / "CLAUDE.md",
        ROOT / "templates" / ".claude" / "skills" / "qa-guard" / "SKILL.md",
    ]

    for path in template_paths:
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        assert "qa-z fast" in text
        assert "qa-z deep" in text
        assert "repair-session" in text
        assert "executor-bridge" in text
        assert "executor-result" in text
        assert "does not call live agents" in lowered


def test_reports_record_template_example_sync_first_pass() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "template and example sync first pass" in current_state.lower()
    assert "template/example sync first pass" in roadmap.lower()


def test_reports_record_executor_operator_diagnostics_first_pass() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "operator diagnostics first pass" in current_state.lower()
    assert "operator diagnostics first pass" in roadmap.lower()
    assert "operator summary and recommended actions" in current_state.lower()


def test_reports_record_workflow_template_live_free_gate_sync() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "deterministic CI gate" in readme
    assert "does not run `executor-bridge`" in readme
    assert "post GitHub bot comments" in readme
    assert "workflow template live-free gate" in current_state.lower()
    assert "workflow template live-free gate" in roadmap.lower()


def test_reports_record_typescript_demo_live_free_boundary_sync() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "TypeScript demo live-free boundary" in current_state
    assert "TypeScript demo live-free boundary" in roadmap


def test_reports_record_fastapi_demo_deterministic_boundary_sync() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "FastAPI demo deterministic boundary" in current_state
    assert "FastAPI demo deterministic boundary" in roadmap


def test_reports_record_nextjs_placeholder_live_free_boundary_sync() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )
    mvp_issues = (ROOT / "docs" / "mvp-issues.md").read_text(encoding="utf-8")

    for text in (current_state, roadmap, mvp_issues):
        assert "Next.js placeholder live-free boundary" in text

    assert "placeholder-only" in mvp_issues
    assert "does not call live agents" in mvp_issues
