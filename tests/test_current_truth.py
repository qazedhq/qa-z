"""Regression tests for QA-Z current-truth surfaces."""

from __future__ import annotations

import json
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


def test_readme_github_summary_surface_mentions_session_candidate_resolution() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert (
        "python -m qa_z github-summary --from-session .qa-z/sessions/<session-id>"
        in readme
    )
    assert (
        "If `--from-session` is given without an explicit `--from-run`, QA-Z now follows that session's `candidate_run_dir`"
        in readme
    )
    assert "whichever run currently owns `latest`" in readme


def test_gitignore_treats_generated_benchmark_summary_and_report_as_local() -> None:
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()

    assert ".ruff_cache_safe/" in lines
    assert ".mypy_cache_safe/" in lines
    assert "/tmp_*" in lines
    assert "/benchmarks/minlock-*" in lines
    assert "%TEMP%/" in lines
    assert "benchmarks/results/work/" in lines
    assert "benchmarks/results-*" in lines
    assert "benchmarks/results/summary.json" in lines
    assert "benchmarks/results/report.md" in lines
    assert "!benchmarks/fixtures/**/repo/.qa-z/**" in lines


def test_legacy_benchmark_readme_points_to_plural_benchmarks_directory() -> None:
    text = (ROOT / "benchmark" / "README.md").read_text(encoding="utf-8")

    assert "../benchmarks/" in text
    assert "historical placeholder" in text


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
    assert "`~/AppData/Local/Temp/qa-z-ruff-cache`" in policy
    assert "`%TEMP%/**`" in policy
    assert "`/tmp_*`" in policy
    assert "`/benchmarks/minlock-*`" in policy
    assert "`benchmarks/results-*`" in policy
    assert "local by default" in policy
    assert "local-only runtime artifacts" in policy
    assert "intentional frozen evidence" in policy
    assert "`benchmarks/fixtures/**/repo/.qa-z/**`" in policy
    assert "literal `%TEMP%/**` scratch roots" in policy
    assert "`build/**`" in policy
    assert "`dist/**`" in policy
    assert "`src/qa_z.egg-info/**`" in policy
    assert "`.mypy_cache_safe/`" in policy
    assert "`.ruff_cache_safe/`" in policy
    assert "safe cache roots `.mypy_cache_safe/` and `.ruff_cache_safe/`" in policy
    assert (
        "`benchmarks/results/work/**` is disposable benchmark scratch output" in policy
    )

    for text in (readme, schema, benchmarking):
        assert "docs/generated-vs-frozen-evidence-policy.md" in text
        assert "local by default" in text
        assert "intentional frozen evidence" in text

    assert "python scripts/runtime_artifact_cleanup.py --json" in policy
    assert "python scripts/runtime_artifact_cleanup.py --apply --json" in policy
    assert "review-only local-by-default roots" in policy
    assert "deletes only local-only runtime artifacts automatically" in policy
    assert "same generated-policy roots that the strict worktree helper reports" in (
        policy
    )
    assert "skips candidate roots that still contain tracked files" in policy
    assert "JSON/human output includes a `reason`" in policy
    assert "Cleanup JSON and human output now include a `reason`" in readme
    assert "review-only local-by-default roots" in readme
    assert "helper-derived policy roots" in readme


def test_self_inspection_reseed_contract_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")

    for text in (readme, schema):
        assert "`backlog_reseeded`" in text
        assert "`reseeded_candidate_ids`" in text
        assert "synthetic `backlog_reseeding_gap`" in text
        assert "concrete" in text


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


def test_alpha_release_gate_evidence_is_documented_in_artifact_schema() -> None:
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")

    assert "## Alpha Release Gate Evidence" in schema
    assert "`generated_at`" in schema
    assert "`evidence.pytest.passed`" in schema
    assert "`evidence.pytest.skipped`" in schema
    assert "`evidence.deep.scan_quality_status`" in schema
    assert "`evidence.deep.scan_quality_warning_count`" in schema
    assert "`evidence.deep.scan_quality_warning_paths`" in schema
    assert "`evidence.deep.scan_quality_check_ids`" in schema
    assert "`evidence.benchmark.snapshot`" in schema
    assert "`evidence.worktree_commit_plan.kind`" in schema
    assert "`evidence.worktree_commit_plan.schema_version`" in schema
    assert "`evidence.worktree_commit_plan.output_path`" in schema
    assert "`evidence.worktree_commit_plan.branch`" in schema
    assert "`evidence.worktree_commit_plan.head`" in schema
    assert "`evidence.worktree_commit_plan.unchanged_batch_count`" in schema
    assert "`evidence.worktree_commit_plan.attention_reasons`" in schema
    assert "`evidence.worktree_commit_plan.attention_reason_count`" in schema
    assert "`evidence.worktree_commit_plan.strict_mode`" in schema
    assert "`evidence.local_preflight.repository_target`" in schema
    assert "`evidence.local_preflight.expected_origin_target`" in schema
    assert "`evidence.local_preflight.repository_url`" in schema
    assert "`evidence.local_preflight.expected_origin_url`" in schema
    assert "`evidence.local_preflight.remote_path`" in schema
    assert "`evidence.local_preflight.remote_blocker`" in schema
    assert "`evidence.local_preflight.skip_remote`" in schema
    assert "`worktree_plan_output`" in schema
    assert "`worktree_plan_attention_reasons`" in schema
    assert "`repository_target`" in schema
    assert "`expected_origin_target`" in schema
    assert "`target=`" in schema
    assert "`path=`" in schema
    assert "`blocker=`" in schema
    assert "`target_url=`" in schema
    assert "`origin_url=`" in schema
    assert "`mode=`" in schema
    assert "`remote_path`" in schema
    assert "`remote_blocker`" in schema
    assert "`Target:`" in schema
    assert "`Origin:`" in schema
    assert "`Mode:`" in schema
    assert "`Decision:`" in schema
    assert "`origin_state`" in schema
    assert "`actual_origin_target`" in schema
    assert "`actual_origin_url`" in schema
    assert "`repository_http_status`" in schema
    assert "`repository_probe_state`" in schema
    assert "`repository_probe_generated_at`" in schema
    assert "`repository_visibility`" in schema
    assert "`repository_archived`" in schema
    assert "`repository_default_branch`" in schema
    assert "`remote_ref_count`" in schema
    assert "`remote_ref_head_count`" in schema
    assert "`remote_ref_tag_count`" in schema
    assert "`remote_ref_kinds`" in schema
    assert "`remote_ref_sample`" in schema
    assert "`publish_strategy`" in schema
    assert "`publish_checklist`" in schema
    assert "`publish_checklist_count`" in schema
    assert "`release_path_state`" in schema
    assert "`push_default_branch`" in schema
    assert "`push_release_branch`" in schema
    assert "`remote_preflight`" in schema
    assert "`bootstrap_origin`" in schema
    assert "`origin_current_target=`" in schema
    assert "`origin_current=`" in schema
    assert "`refs=`" in schema
    assert "`head_refs=`" in schema
    assert "`tag_refs=`" in schema
    assert "`ref_kinds=`" in schema
    assert "`ref_sample=`" in schema
    assert "`ready_for_remote_checks`" in schema
    assert "`origin_present`" in schema
    assert "worktree commit-plan `next_actions`" in schema
    assert "top-level `next_commands`" in schema
    assert "older benchmark artifact has only counters" in schema
    assert "`evidence_consistency_errors`" in schema
    assert "`release_evidence_consistency`" in schema


def test_benchmark_results_dir_locking_is_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    benchmarking = (ROOT / "docs" / "benchmarking.md").read_text(encoding="utf-8")

    for text in (readme, benchmarking):
        assert ".benchmark.lock" in text
        assert "--results-dir" in text
        assert "exit code `2`" in text
        assert "parallel" in text or "one benchmark run" in text


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
    assert "`Rule counts: clear=..., attention=..., blocked=...`" in readme
    assert "`Action <id>:` lines" in readme
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
    assert "they no longer reopen `evidence_freshness_gap` by themselves" in readme
    assert (
        "`runtime_artifact_cleanup_gap` now outranks the broader `artifact_hygiene_gap`"
        in readme
    )
    assert "within-batch fallback-family penalty" in readme
    assert "recommendation-specific commands plus additive `context_paths`" in readme
    assert "`python scripts/runtime_artifact_cleanup.py --json`" in readme
    assert "`python scripts/runtime_artifact_cleanup.py --apply --json`" in readme
    assert "Deferred generated cleanup packets" in readme
    assert "`docs/generated-vs-frozen-evidence-policy.md` through `context_paths`" in (
        readme
    )
    assert "`scripts/runtime_artifact_cleanup.py` through `context_paths`" in readme
    assert (
        "`latest_prepared_actions` and `latest_next_recommendations` fields" in readme
    )
    assert "Human `qa-z backlog` output now focuses on open or active items" in readme
    assert "prints the backlog `Updated:` timestamp" in readme
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
    assert (
        "surface a non-cleanup fallback family before selecting more cleanup work"
        in readme
    )
    assert "loop plans now mirror selection score and penalty residue" in readme
    assert "autonomy loop plans now mirror selected-task evidence summaries" in readme
    assert "selected fallback families" in readme
    assert "`latest_selected_fallback_families`" in readme
    assert "Loop-health packets" in readme
    assert "loop-history evidence" in readme
    assert "Autonomy-created repair-session packets" in readme
    assert "loop-local self-inspection plus selected verification evidence" in readme
    assert "bridge-local action context inputs" in readme
    assert "action-context package health" in readme
    assert "missing action-context diagnostics" in readme
    assert "non-JSON stdout mirrors source self-inspection, source loop" in readme
    assert "freshness/provenance checks, warnings, and backlog implications" in readme
    assert (
        "`selection_gap_reason` plus open backlog counts before and after inspection"
        in readme
    )
    assert "`loop_health` summary" in readme
    assert "blocked no-candidate chain" in readme
    assert "blocked no-candidate loop ids" in readme
    assert "`stop_reason`" in readme
    assert "no minimum budget" in readme
    assert "`executor_dry_run_verdict` and `executor_dry_run_reason`" in schema
    assert "`executor_dry_run_source`" in schema
    assert "`summary_source`" in schema
    assert "`executor_dry_run_attempt_count`" in schema
    assert "`executor_dry_run_history_signals`" in schema
    assert "`operator_summary` and `recommended_actions`" in schema
    assert "`operator_decision`" in schema
    assert "`Rule counts: clear=..., attention=..., blocked=...`" in schema
    assert "`Action <id>:` lines" in schema
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
    assert "`python scripts/runtime_artifact_cleanup.py --json`" in schema
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
    assert (
        "surface a non-`<family>` fallback family before selecting more work" in schema
    )
    assert "they do not reopen `evidence_freshness_gap` on their own" in schema
    assert (
        "`runtime_artifact_cleanup_gap` now scores above the broader `artifact_hygiene_gap`"
        in schema
    )
    assert (
        "policy-managed runtime artifacts still present under an explicit policy: `+2`"
        in schema
    )
    assert "`.qa-z/loops/history.jsonl`" in schema
    assert "`.qa-z/loops/<loop-id>/self_inspect.json`" in schema
    assert "loop-local self-inspection plus selected verification evidence" in schema
    assert "`inputs.action_context`" in schema
    assert "`inputs.action_context_missing`" in schema
    assert "`inputs/context/`" in schema
    assert "Non-JSON `qa-z executor-result ingest` stdout" in schema
    assert "prints the ingest report path" in schema
    assert "`Source Context` section" in schema
    assert "backlog implication categories" in schema
    assert "`selection_penalty` and `selection_penalty_reasons`" in schema
    assert "autonomy loop plans now also mirror selected-task evidence" in schema
    assert "`blocked_chain_length`" in schema
    assert "`blocked_chain_remaining_until_stop`" in schema
    assert "`blocked_chain_loop_ids`" in schema
    assert "action basis:" in readme
    assert "action basis:" in schema
    assert "benchmarks/results-*" in readme
    assert "benchmarks/results-*" in schema
    assert "intentional frozen evidence" in readme
    assert "intentional frozen evidence" in schema
    assert "`generated_outputs` or `runtime_artifacts`" in readme
    assert "`generated_outputs` or `runtime_artifacts`" in schema
    assert "clear policy-managed runtime artifacts before source integration" in readme
    assert (
        "clear policy-managed runtime artifacts before rerunning self-inspection"
        in schema
    )
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
    assert "`release_evidence_count`" in schema
    assert "generated alpha release evidence count" in readme
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


def test_current_reports_reflect_latest_local_gate_refresh() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    for text in (current_state, roadmap):
        assert "Date: 2026-04-24" in text
        assert "1184 passed" in text
        assert "54/54 fixtures, overall_rate 1.0" in text
        assert "500 source files" in text
        assert "562 files already formatted" in text
        assert "generated_local_only_count" in text
        assert "generated_local_by_default_count" in text
        assert "cross_cutting_count=12" in text
        assert "cross_cutting_group_count=5" in text
        assert "run_resolution" in text
        assert ".benchmark.lock" in text
        assert "ingest stdout diagnostics" in text
        assert "release_evidence_count" in text
        assert "Generated at:" in text
        assert "release_evidence_consistency" in text
    assert "alpha release gate passed" in current_state
    assert "needs_repository_bootstrap" in current_state
    assert "repository_missing" in current_state
    assert "generated_artifact_count=0" in current_state
    assert "generated_local_only_count=0" in current_state
    assert "generated_local_by_default_count=0" in current_state
    assert "generated_artifact_count=7" in current_state
    assert "generated_local_only_count=0" in current_state
    assert "generated_local_by_default_count=7" in current_state
    assert "unassigned_source_path_count=0" in current_state
    assert "generated_artifact_count=0" in roadmap
    assert "generated_local_only_count=0" in roadmap
    assert "generated_local_by_default_count=0" in roadmap
    assert "generated_artifact_count=7" in roadmap
    assert "generated_local_only_count=0" in roadmap
    assert "generated_local_by_default_count=7" in roadmap
    assert "unassigned_source_path_count=0" in roadmap
    assert "local_only_remote_preflight" in current_state
    assert "ready_for_remote_checks" in current_state
    assert "mypy.ini" in roadmap
    assert "$TEMP/qa-z-mypy-cache" in roadmap
    assert "`30` generated roots total" not in roadmap
    assert "`25` are local-only runtime artifacts" not in roadmap
    assert "475 passed" not in current_state
    assert "474 passed" not in current_state
    assert "469 passed" not in current_state
    assert "407 passed" not in current_state
    assert "386 passed" not in current_state
    assert "50/50 fixtures" not in current_state


def test_continuity_docs_reference_split_publish_test_packs() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )
    triage = (ROOT / "docs" / "reports" / "worktree-triage.md").read_text(
        encoding="utf-8"
    )

    for text in (current_state, commit_plan, triage):
        assert "tests/test_verification_publish.py" not in text
        assert "tests/test_github_summary.py" not in text

    assert "tests/test_verification_publish_summary.py" in current_state
    assert "tests/test_github_summary_render.py" in current_state
    assert "tests/test_verification_publish_summary.py" in commit_plan
    assert "tests/test_github_summary_render.py" in commit_plan
    assert "tests/test_verification_publish_summary.py" in triage
    assert "tests/test_github_summary_render.py" in triage


def test_worktree_reports_document_expanded_untracked_paths_and_shared_command_spine() -> (
    None
):
    triage = (ROOT / "docs" / "reports" / "worktree-triage.md").read_text(
        encoding="utf-8"
    )
    commit_plan = (ROOT / "docs" / "reports" / "worktree-commit-plan.md").read_text(
        encoding="utf-8"
    )

    for text in (triage, commit_plan):
        assert "--untracked-files=all" in text
        assert "src/qa_z/commands/command_registration.py" in text
        assert "src/qa_z/commands/command_registry.py" in text
        assert "src/qa_z/commands/execution.py" in text
        assert "src/qa_z/commands/runtime.py" in text
        assert "tests/test_runtime_commands.py" in text


def test_docs_bind_reduce_integration_risk_to_worktree_commit_plan() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")

    for text in (readme, schema):
        assert "reduce_integration_risk" in text
        assert (
            "python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json"
            in text
        )


def test_reports_record_live_evidence_gating_for_cleanup_self_inspection() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    for text in (current_state, roadmap):
        lowered = " ".join(text.lower().split())
        assert (
            "deferred cleanup, commit-isolation, and integration report-only "
            "evidence is not enough"
        ) in lowered
        assert "live git or runtime artifact evidence" in lowered
    assert "report-only deferred cleanup wording" in readme
    for text in (readme, current_state):
        assert "Integration-gap candidates" in text
        assert "git_status" in text
        assert "audit_worktree_integration" in text
        assert "live_repository" in text
        assert "current_branch" in text
        assert "current_head" in text
        assert "dirty_benchmark_result_count" in text
        assert "branch=detached" in text
        assert "dirty_area_summary" in text
    assert "Live repository:" in readme
    assert (
        "treated as local-by-default benchmark result evidence in live "
        "repository signals and self-inspection" in readme
    )
    assert "stay in the `benchmark` bucket for `dirty_area_summary`" in readme
    assert "not as local-only runtime cleanup pressure" in readme
    assert "kept visible as" in current_state
    assert "local-by-default benchmark result evidence" in current_state
    assert "stay in the `benchmark` bucket for `dirty_area_summary`" in " ".join(
        current_state.split()
    )
    assert "`runtime_artifact_paths`" in current_state
    assert "`benchmark_result_paths`" in roadmap
    assert "`dirty_benchmark_result_count`" in roadmap
    assert "runtime artifacts rather than benchmark fixtures" not in current_state
    assert "treated like generated runtime artifacts" not in readme
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")
    assert "`live_repository`" in schema
    assert "`current_branch`" in schema
    assert "`current_head`" in schema
    assert "`dirty_benchmark_result_count`" in schema
    assert "`generated_artifact_policy_explicit`" in schema
    assert "`dirty_area_summary`" in schema
    assert "excluding local-by-default benchmark result evidence" in schema


def test_release_preflight_docs_follow_generated_evidence_policy_split() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release_handoff = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-publish-handoff.md"
    ).read_text(encoding="utf-8")
    policy = (ROOT / "docs" / "generated-vs-frozen-evidence-policy.md").read_text(
        encoding="utf-8"
    )
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")

    assert "local-only runtime artifacts" in readme
    assert "local-by-default benchmark evidence" in readme
    assert "tracked generated roots" in readme
    assert "local-only runtime artifacts" in release_handoff
    assert "local-by-default benchmark evidence" in release_handoff
    assert "tracked generated roots" in release_handoff
    assert "`tracked_generated_artifact_count`" in schema
    assert "`generated_local_only_tracked_count`" in schema
    assert "`generated_local_by_default_tracked_count`" in schema
    assert (
        "Snapshot directories matching `benchmarks/results-*` are also "
        "generated runtime artifacts."
    ) not in policy
    assert "local-by-default benchmark evidence" in policy


def test_readme_documents_deep_from_run_output_dir_boundary() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")
    benchmarking = (ROOT / "docs" / "benchmarking.md").read_text(encoding="utf-8")

    assert "`--from-run` and `--output-dir` cannot be" in readme
    assert "run_resolution" in readme
    assert "`run_resolution`" in schema
    assert "`source`: `latest`, `from_run`, `output_dir`, or `new_run`" in schema
    assert "run_resolution_source" in benchmarking
    assert "attached_to_fast_run" in benchmarking
    assert "run_resolution_fast_summary_path" in benchmarking
    assert "prefers `--output-dir`, then `--from-run`" not in readme


def test_semgrep_scan_warning_diagnostics_are_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    schema = (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8")
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    benchmarking = (ROOT / "docs" / "benchmarking.md").read_text(encoding="utf-8")

    for text in (readme, schema, current_state, benchmarking):
        assert "scan_warning_count" in text
        assert "scan_warnings" in text
        assert "scan_quality" in text
        assert "deep_scan_warning_diagnostics" in text
        assert "deep_scan_warning_multi_source_diagnostics" in text
    assert "diagnostics.scan_quality" in schema
    assert "warning_types" in schema
    assert "warning_paths" in schema
    assert "check_ids" in schema
    assert "warning checks" in readme.lower()
    assert "warning checks" in benchmarking.lower()
    assert "artifact paths" in readme.lower()
    assert "artifact paths" in benchmarking.lower()


def test_deep_warning_benchmark_fixtures_pin_warning_check_ids() -> None:
    diagnostics = json.loads(
        (
            ROOT
            / "benchmarks"
            / "fixtures"
            / "deep_scan_warning_diagnostics"
            / "expected.json"
        ).read_text(encoding="utf-8")
    )
    multi_source = json.loads(
        (
            ROOT
            / "benchmarks"
            / "fixtures"
            / "deep_scan_warning_multi_source_diagnostics"
            / "expected.json"
        ).read_text(encoding="utf-8")
    )

    assert diagnostics["expect_deep"]["scan_quality_check_ids_present"] == ["sg_scan"]
    assert multi_source["expect_deep"]["scan_quality_check_ids_present"] == ["sg_scan"]


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
        assert "mixed_fast_deep_scan_warning_fast_only" in text
        assert "executor_bridge_action_context_inputs" in text
        assert "executor_bridge_missing_action_context_inputs" in text

    assert "mixed fast plus deep interactions" in current_state
    assert "executor bridge action-context packaging coverage" in current_state
    assert "action-context package health" in current_state
    assert "bridge-local action context copying" in benchmarking
    assert "missing action-context guide and stdout diagnostics" in readme
    assert "guide/stdout missing-context diagnostics" in benchmarking
    assert "ingest stdout diagnostics" in readme
    assert "ingest stdout diagnostics" in benchmarking
    assert "source_context_fields_recorded" in benchmarking
    assert "live_repository_context_recorded" in benchmarking
    assert "check_statuses_recorded" in benchmarking
    assert "backlog_implications_recorded" in benchmarking
    assert "stdout_mentions_source_context" not in benchmarking
    assert "four executed mixed fast plus deep handoff fixtures" in readme
    assert "two executed mixed fast plus deep handoff fixtures" not in readme
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
        "executor_dry_run_validation_conflict_repeated_rejected_operator_actions",
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
    for text in (readme, benchmarking, current_state, roadmap):
        assert "rejected-result inspection ahead of partial retry review" in text
        assert "validation conflicts and retry pressure still need review" in text
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
    assert "ordered `Action <id>:` lines for recommended actions" in readme
    assert "action-aligned next recommendations" in benchmarking
    assert "all committed dry-run fixtures" in current_state
    assert "all committed dry-run fixtures" in roadmap
    assert "ordered `Action <id>:` lines for those recommended actions" in current_state
    assert "ordered `Action <id>:` lines for those recommended actions" in roadmap


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


def test_readme_repository_map_marks_placeholder_examples_honestly() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert (
        "examples/                 runnable Python and TypeScript demos plus placeholder examples"
        in readme
    )


def test_readme_example_policy_marks_public_example_as_authoritative_excerpt_source() -> (
    None
):
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert (
        "`qa-z.yaml.example` is the authoritative full public example config." in readme
    )
    assert "The excerpt below shows the intended policy shape:" in readme


def test_reports_record_template_example_sync_first_pass() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert "template and example sync first pass" in current_state.lower()
    assert "template/example sync first pass" in roadmap.lower()


def test_reports_identify_generated_evidence_policy_as_post_l29_immediate_focus() -> (
    None
):
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    assert (
        "preserve generated versus frozen evidence policy as artifact surfaces evolve"
        in current_state
    )
    assert (
        "Immediate next focus: create or expose `qazedhq/qa-z`, or install/authorize access to that owner for this session, rerun remote preflight against the configured `origin`, and only then choose direct publish versus release-PR cutover."
        in roadmap
    )
    assert (
        "Priority 5 executor operator diagnostics now includes the committed non-blocked `validation_conflict + repeated_rejected_attempts` mixed-history slice"
        in roadmap
    )


def test_reports_document_workflow_template_non_goals_beyond_live_executor_calls() -> (
    None
):
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    for text in (current_state, roadmap):
        normalized = " ".join(text.split())
        assert "do not call live executors" in normalized
        assert "ingest executor results" in normalized
        assert "perform autonomous repair" in normalized


def test_readme_near_term_roadmap_matches_post_sync_priorities() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")

    assert (
        "1. Preserve generated versus frozen evidence policy as artifact surfaces evolve."
        in readme
    )
    assert (
        "2. Maintain loop-health summary clarity as autonomy surfaces grow." in readme
    )
    assert (
        "3. Broaden operator diagnostics and mixed-history depth only where a new deterministic dry-run slice adds unique evidence."
        in readme
    )
    assert (
        "4. Broaden mixed-surface benchmark realism only where a new deterministic slice adds unique evidence."
        in readme
    )
    assert (
        "5. Keep report, template, and example current-truth sync as maintenance so the alpha docs stay exact."
        in readme
    )
    assert (
        "Add standalone GitHub annotation helpers if code scanning is not available."
        not in readme
    )


def test_reports_do_not_overclaim_reusable_workflow_template_surface() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )

    for text in (current_state, roadmap):
        assert "workflow template" in text
        assert "reusable workflow template" not in text


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

    assert "TypeScript demo live-free boundary" in " ".join(current_state.split())
    assert "TypeScript demo live-free boundary" in " ".join(roadmap.split())


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
        assert "Next.js placeholder live-free boundary" in " ".join(text.split())

    assert "placeholder-only" in mvp_issues
    assert "does not call live agents" in mvp_issues
