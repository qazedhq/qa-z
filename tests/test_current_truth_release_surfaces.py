from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_text(*parts: str) -> str:
    return ROOT.joinpath(*parts).read_text(encoding="utf-8")


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


def test_runtime_package_version_matches_release_metadata() -> None:
    package_init = (ROOT / "src" / "qa_z" / "__init__.py").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'version = "0.9.8a0"' in pyproject
    assert '__version__ = "0.9.8a0"' in package_init
    assert '__version__ = "0.1.0"' not in package_init


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
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release_notes = (ROOT / "docs" / "releases" / "v0.9.8-alpha.md").read_text(
        encoding="utf-8"
    )
    release_handoff = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-publish-handoff.md"
    ).read_text(encoding="utf-8")
    launch_plan = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-19-github-repository-launch.md"
    ).read_text(encoding="utf-8")
    release_pr = (ROOT / "docs" / "releases" / "v0.9.8-alpha-pr.md").read_text(
        encoding="utf-8"
    )
    github_release = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-github-release.md"
    ).read_text(encoding="utf-8")
    assert "## Alpha Closure Readiness Snapshot" in commit_plan
    assert "latest full local gate pass" in commit_plan
    assert "python -m pytest" in commit_plan
    assert "Verified on 2026-04-23" in release_plan
    assert "Verified on 2026-04-22" not in release_plan
    assert "Audit date: 2026-04-23 KST." in launch_plan
    assert "Audit date: 2026-04-22 KST." not in launch_plan
    assert "1158 passed" in commit_plan
    assert "1158 passed" in release_plan
    assert "1158 passed" in release_handoff
    assert "pytest: 1158 passed" in launch_plan
    assert "expected current pytest count is 1158 passed" in launch_plan
    assert "`python -m pytest`: 1158 passed" in release_notes
    assert "`python -m pytest`: passed, `1158 passed" in release_pr
    assert "`python -m pytest`: passed, `1158 passed`" in github_release
    assert "repo_probe=..." in readme
    assert "repo_probe_basis=last_known" in readme
    assert "repo_probe_at=..." in readme
    assert "repo_probe_freshness=..." in readme
    assert "repo_probe_age_hours=..." in readme
    assert "repo_http=..." in readme
    assert "repo_visibility=..." in readme
    assert "repo_archived=yes|no" in readme
    assert "repo_default_branch=..." in readme
    assert "repo_probe=..." in release_handoff
    assert "repo_probe_basis=last_known" in release_handoff
    assert "repo_probe_at=..." in release_handoff
    assert "repo_probe_freshness=..." in release_handoff
    assert "repo_probe_age_hours=..." in release_handoff
    assert "repo_http=..." in release_handoff
    assert "repo_visibility=..." in release_handoff
    assert "repo_archived=yes|no" in release_handoff
    assert "repo_default_branch=..." in release_handoff
    assert "474 passed" not in commit_plan
    assert "474 passed" not in release_plan
    assert "474 passed" not in release_handoff
    assert "474 passed" not in launch_plan
    assert "474 passed" not in release_notes
    assert "474 passed" not in release_pr
    assert "474 passed" not in github_release
    assert "469 passed" not in commit_plan
    assert "469 passed" not in release_plan
    assert "469 passed" not in release_handoff
    assert "469 passed" not in launch_plan
    assert "469 passed" not in release_notes
    assert "469 passed" not in release_pr
    assert "469 passed" not in github_release
    assert "459 passed" not in commit_plan
    assert "459 passed" not in release_plan
    assert "459 passed" not in release_handoff
    assert "459 passed" not in launch_plan
    assert "459 passed" not in release_notes
    assert "459 passed" not in release_pr
    assert "459 passed" not in github_release
    assert "385 passed" not in commit_plan
    assert "385 passed" not in release_plan
    assert "385 passed" not in release_handoff
    assert "385 passed" not in launch_plan
    assert "385 passed" not in release_notes
    assert "385 passed" not in release_pr
    assert "385 passed" not in github_release
    assert "384 passed" not in commit_plan
    assert "384 passed" not in release_plan
    assert "384 passed" not in release_handoff
    assert "384 passed" not in launch_plan
    assert "384 passed" not in release_notes
    assert "384 passed" not in release_pr
    assert "384 passed" not in github_release
    assert "381 passed" not in commit_plan
    assert "381 passed" not in release_plan
    assert "381 passed" not in release_handoff
    assert "381 passed" not in launch_plan
    assert "381 passed" not in release_notes
    assert "381 passed" not in release_pr
    assert "381 passed" not in github_release
    assert "380 passed" not in commit_plan
    assert "380 passed" not in release_plan
    assert "380 passed" not in release_handoff
    assert "380 passed" not in launch_plan
    assert "380 passed" not in release_notes
    assert "380 passed" not in release_pr
    assert "380 passed" not in github_release
    assert "377 passed" not in commit_plan
    assert "377 passed" not in release_plan
    assert "377 passed" not in release_handoff
    assert "377 passed" not in launch_plan
    assert "377 passed" not in release_notes
    assert "377 passed" not in release_pr
    assert "377 passed" not in github_release
    assert "367 passed" not in commit_plan
    assert "367 passed" not in release_plan
    assert "367 passed" not in release_handoff
    assert "367 passed" not in launch_plan
    assert "367 passed" not in release_notes
    assert "367 passed" not in release_pr
    assert "367 passed" not in github_release
    assert "366 passed" not in commit_plan
    assert "366 passed" not in release_plan
    assert "366 passed" not in release_handoff
    assert "366 passed" not in launch_plan
    assert "366 passed" not in release_notes
    assert "366 passed" not in release_pr
    assert "366 passed" not in github_release
    assert "362 passed" not in commit_plan
    assert "362 passed" not in release_plan
    assert "362 passed" not in release_handoff
    assert "362 passed" not in launch_plan
    assert "362 passed" not in release_notes
    assert "362 passed" not in release_pr
    assert "362 passed" not in github_release
    assert "359 passed" not in commit_plan
    assert "359 passed" not in release_plan
    assert "359 passed" not in release_handoff
    assert "359 passed" not in launch_plan
    assert "359 passed" not in release_notes
    assert "359 passed" not in release_pr
    assert "359 passed" not in github_release
    assert "356 passed" not in commit_plan
    assert "356 passed" not in release_plan
    assert "356 passed" not in release_handoff
    assert "356 passed" not in launch_plan
    assert "356 passed" not in release_notes
    assert "356 passed" not in release_pr
    assert "356 passed" not in github_release
    assert "354 passed" not in commit_plan
    assert "354 passed" not in release_plan
    assert "354 passed" not in release_handoff
    assert "354 passed" not in launch_plan
    assert "354 passed" not in release_notes
    assert "354 passed" not in release_pr
    assert "354 passed" not in github_release
    assert "348 passed" not in commit_plan
    assert "348 passed" not in release_plan
    assert "348 passed" not in release_handoff
    assert "348 passed" not in launch_plan
    assert "348 passed" not in release_notes
    assert "348 passed" not in release_pr
    assert "348 passed" not in github_release
    assert "347 passed" not in commit_plan
    assert "347 passed" not in release_plan
    assert "347 passed" not in release_notes
    assert "347 passed" not in release_pr
    assert "347 passed" not in github_release


def test_release_surfaces_describe_preflight_generated_policy_split() -> None:
    readme = read_text("README.md")
    commit_plan = read_text("docs", "reports", "worktree-commit-plan.md")
    release_plan = read_text(
        "docs", "superpowers", "plans", "2026-04-18-github-repository-release.md"
    )
    release_handoff = read_text("docs", "releases", "v0.9.8-alpha-publish-handoff.md")
    current_state = read_text("docs", "reports", "current-state-analysis.md")
    roadmap = read_text("docs", "reports", "next-improvement-roadmap.md")
    launch_plan = read_text(
        "docs", "superpowers", "plans", "2026-04-19-github-repository-launch.md"
    )
    release_notes = read_text("docs", "releases", "v0.9.8-alpha.md")
    release_pr = read_text("docs", "releases", "v0.9.8-alpha-pr.md")
    github_release = read_text("docs", "releases", "v0.9.8-alpha-github-release.md")
    schema = read_text("docs", "artifact-schema-v1.md")

    assert "generated-artifact preflight" in readme
    for text in (readme, release_handoff):
        assert "local-only runtime artifacts" in text
        assert "local-by-default benchmark evidence" in text
        assert "tracked generated roots" in text
    assert "`tracked_generated_artifact_count`" in schema
    assert "`generated_local_only_tracked_paths`" in schema
    assert "`generated_local_by_default_tracked_paths`" in schema
    assert "python -m qa_z benchmark --json" in commit_plan
    assert "python -m qa_z benchmark --json" in release_pr
    assert "python -m qa_z benchmark --json" in github_release
    assert "non-blocking `scan_quality` warnings surfaced" in release_notes
    assert "non-blocking `scan_quality` warnings surfaced" in release_pr
    assert "non-blocking `scan_quality` warnings surfaced" in github_release
    assert "non-blocking `scan_quality` warnings surfaced" in release_handoff
    assert "python -m build --sdist --wheel" in commit_plan
    assert "python -m build --sdist --wheel" in release_plan
    assert "`python -m build --sdist --wheel`: passed" in release_notes
    assert "`python -m build --sdist --wheel`: passed" in release_pr
    assert "`python -m build --sdist --wheel`: passed" in github_release
    assert "python scripts/alpha_release_artifact_smoke.py --json" in commit_plan
    assert "python scripts/alpha_release_artifact_smoke.py --json" in release_plan
    assert "python scripts/alpha_release_artifact_smoke.py --json" in release_handoff
    assert "python scripts/alpha_release_artifact_smoke.py --json" in launch_plan
    assert "python scripts/alpha_release_artifact_smoke.py --json" in release_notes
    assert "python scripts/alpha_release_artifact_smoke.py --json" in release_pr
    assert "python scripts/alpha_release_artifact_smoke.py --json" in github_release
    assert "python scripts/alpha_release_gate.py --json" in release_notes
    assert "python scripts/alpha_release_gate.py --json" in release_pr
    assert "python scripts/alpha_release_gate.py --json" in github_release
    assert "python scripts/alpha_release_gate.py --json" in release_handoff
    assert (
        "python scripts/alpha_release_gate.py --json --output dist/alpha-release-gate.json"
        in release_handoff
    )
    assert "dist/alpha-release-gate.preflight.json" in release_handoff
    assert "dist/alpha-release-gate.worktree-plan.json" in release_handoff
    assert (
        "gate JSON records check_count, passed_count, failed_count, and failed_checks"
        in release_handoff
    )
    assert "gate JSON summarizes pytest, deep, and benchmark evidence" in readme
    assert (
        "gate JSON summarizes pytest, deep, and benchmark evidence" in release_handoff
    )
    assert "optional pytest skipped count" in readme
    assert "optional pytest skipped count" in release_handoff
    assert "older benchmark artifact has only counters" in readme
    assert "older benchmark artifact has only counters" in release_handoff
    assert "release_evidence_consistency" in readme
    assert "release_evidence_consistency" in release_handoff
    assert "contradictory benchmark totals" in readme
    assert "contradictory benchmark totals" in release_handoff
    assert "inspect `python -m qa_z benchmark --json`" in readme
    assert "inspect `python -m qa_z benchmark --json`" in release_handoff
    assert "worktree generated artifact split mismatch" in readme
    assert "worktree generated artifact split mismatch" in release_handoff
    assert "python scripts/worktree_commit_plan.py --include-ignored --json" in readme
    assert (
        "python scripts/worktree_commit_plan.py --include-ignored --json"
        in release_handoff
    )
    assert "gate JSON promotes preflight_failed_checks," in readme
    assert "next_actions, and next_commands" in readme
    assert "preflight_failed_checks, next_actions, and next_commands" in release_handoff
    assert (
        "gate JSON deduplicates promoted attention reasons, next_actions, and" in readme
    )
    assert (
        "gate JSON deduplicates promoted attention reasons, next_actions, and"
        in release_handoff
    )
    assert "gate reads nested preflight output file when stdout is not JSON" in readme
    assert (
        "gate reads nested preflight output file when stdout is not JSON"
        in release_handoff
    )
    assert (
        "gate reads nested worktree commit-plan output file when stdout is not JSON"
        in readme
    )
    assert (
        "gate reads nested worktree commit-plan output file when stdout is not JSON"
        in release_handoff
    )
    assert "gate supplements partial preflight stdout from the output file" in readme
    assert (
        "gate supplements partial preflight stdout from the output file"
        in release_handoff
    )
    assert "gate synthesizes dirty-worktree guidance from failed_checks" in readme
    assert (
        "gate synthesizes dirty-worktree guidance from failed_checks" in release_handoff
    )
    assert "human-readable gate output prints Next actions" in readme
    assert "human-readable gate output prints Next actions" in release_handoff
    assert "human-readable gate output prints Evidence" in readme
    assert "human-readable gate output prints Evidence" in release_handoff
    assert "`origin_state=`" in readme
    assert "`origin_state=`" in release_handoff
    assert "`origin_current_target=`" in readme
    assert "`origin_current_target=`" in release_handoff
    assert "`origin_current=`" in readme
    assert "`origin_current=`" in release_handoff
    assert "`refs=`" in readme
    assert "`refs=`" in release_handoff
    assert "`ref_sample=`" in readme
    assert "`ref_sample=`" in release_handoff
    assert "`actual_origin_target`" in readme
    assert "`actual_origin_target`" in release_handoff
    assert "`repository_http_status`" in readme
    assert "`repository_http_status`" in release_handoff
    assert "`repository_probe_state`" in readme
    assert "`repository_probe_state`" in release_handoff
    assert "`repository_probe_generated_at`" in readme
    assert "`repository_probe_generated_at`" in release_handoff
    assert "`repository_visibility`" in readme
    assert "`repository_visibility`" in release_handoff
    assert "`repository_archived`" in readme
    assert "`repository_archived`" in release_handoff
    assert "`repository_default_branch`" in readme
    assert "`repository_default_branch`" in release_handoff
    assert "`remote_ref_count`" in readme
    assert "`remote_ref_count`" in release_handoff
    assert "`remote_ref_head_count`" in readme
    assert "`remote_ref_head_count`" in release_handoff
    assert "`remote_ref_tag_count`" in readme
    assert "`remote_ref_tag_count`" in release_handoff
    assert "`remote_ref_kinds`" in readme
    assert "`remote_ref_kinds`" in release_handoff
    assert "`remote_ref_sample`" in release_handoff
    assert "`publish_strategy`" in readme
    assert "`publish_strategy`" in release_handoff
    assert "`publish_checklist`" in readme
    assert "`publish_checklist`" in release_handoff
    assert "`release_path_state`" in readme
    assert "`release_path_state`" in release_handoff
    assert "`publish_strategy=push_default_branch`" in readme
    assert "`publish_strategy=push_default_branch`" in release_handoff
    assert "`publish_strategy=push_release_branch`" in readme
    assert "`publish_strategy=push_release_branch`" in release_handoff
    assert "`publish_strategy=remote_preflight`" in readme
    assert "`publish_strategy=remote_preflight`" in release_handoff
    assert "`publish_strategy=bootstrap_origin`" in readme
    assert "`publish_strategy=bootstrap_origin`" in release_handoff
    assert "ready_for_remote_checks" in readme
    assert "ready_for_remote_checks" in release_handoff
    assert "configured but no `--expected-origin-url` was supplied" in readme
    assert "configured but no `--expected-origin-url` was supplied" in release_handoff
    assert "preflight:" in readme
    assert "preflight:" in release_handoff
    assert "artifact smoke:" in readme
    assert "artifact smoke:" in release_handoff
    assert "bundle manifest:" in readme
    assert "bundle manifest:" in release_handoff
    assert "build:" in readme
    assert "build:" in release_handoff
    assert "cli help:" in readme
    assert "cli help:" in release_handoff
    assert "warning_types=" in readme
    assert "warning_types=" in release_handoff
    assert "warning_paths=" in readme
    assert "warning_paths=" in release_handoff
    assert "warning_checks=" in readme
    assert "warning_checks=" in release_handoff
    assert "human-readable gate Evidence prints unchanged_batches" in readme
    assert "human-readable gate Evidence prints unchanged_batches" in release_handoff
    assert "human-readable gate Evidence prints batches and changed_paths" in readme
    assert (
        "human-readable gate Evidence prints batches and changed_paths"
        in release_handoff
    )
    assert "human-readable gate Evidence prints generated_files and generated_dirs" in (
        readme
    )
    assert "human-readable gate Evidence prints generated_files and generated_dirs" in (
        release_handoff
    )
    assert "reports=" in readme
    assert "reports=" in release_handoff
    assert "human-readable gate Evidence prints output=" in readme
    assert "human-readable gate Evidence prints output=" in release_handoff
    assert "human-readable gate output prints Artifacts" in readme
    assert "human-readable gate output prints Artifacts" in release_handoff
    assert "human-readable gate output prints Worktree plan attention" in readme
    assert (
        "human-readable gate output prints Worktree plan attention" in release_handoff
    )
    assert "human-readable gate Evidence prints strict=fail_on_generated" in readme
    assert (
        "human-readable gate Evidence prints strict=fail_on_generated"
        in release_handoff
    )
    assert "human-readable gate output prints `Generated at:`" in readme
    assert "human-readable gate output prints `Generated at:`" in release_handoff
    assert "Dirty worktree failures now recommend committing, stashing" in readme
    assert "worktree_clean check must be clean for release" in release_handoff
    assert "preflight JSON records check_count, passed_count, failed_count," in (
        release_handoff
    )
    assert "skipped_count, failed_checks" in release_handoff
    assert "`remote_path`" in release_handoff
    assert "`remote_blocker`" in release_handoff
    assert "`origin_state`" in release_handoff
    assert "`actual_origin_url`" in release_handoff
    assert "next_actions" in release_handoff
    assert "next_commands" in release_handoff
    assert "normalize back to the intended repository URL" in readme
    assert "normalize back to the intended repository URL" in release_handoff
    assert (
        "Create or expose the public GitHub repository qazedhq/qa-z" in release_handoff
    )
    assert "--allow-existing-refs or publish to an empty repository" in release_handoff
    assert "Remote release tag v0.9.8-alpha already exists" in release_handoff
    assert "Set origin to the intended repository URL" in release_handoff
    assert (
        "Set --repository-url to https://github.com/qazedhq/qa-z.git" in release_handoff
    )
    assert "Set --repository-url to https://github.com/qazedhq/qa-z.git" in readme
    assert "python scripts/alpha_release_gate.py --json" in launch_plan
    assert "python scripts/alpha_release_gate.py --include-remote" in readme
    assert (
        "python scripts/alpha_release_gate.py --json --output dist/alpha-release-gate.json"
        in readme
    )
    assert "dist/alpha-release-gate.preflight.json" in readme
    assert "dist/alpha-release-gate.worktree-plan.json" in readme
    assert "include `generated_at`" in readme
    assert "include `generated_at`" in release_handoff
    assert "preflight output also print `Generated at:`" in readme
    assert "preflight output also print `Generated at:`" in release_handoff
    assert "check_count, passed_count, failed_count," in readme
    assert "skipped_count, failed_checks" in readme
    assert "canonicalized repository/origin targets" in readme
    assert "`Target:`" in readme
    assert "`Origin:`" in readme
    assert "`Mode:`" in readme
    assert "`Decision:`" in readme
    assert "`target=`" in readme
    assert "`path=`" in readme
    assert "`blocker=`" in readme
    assert "`mode=`" in readme
    assert "`target_url=`" in readme
    assert "`origin_url=`" in readme
    assert "schemeless `github.com/owner/repo.git`" in readme
    assert "generated-artifact preflight" in readme
    assert "benchmarks/results-*" in readme
    assert "--expected-origin-url" in readme
    assert (
        "python scripts/alpha_release_preflight.py --skip-remote --json --output"
        in (release_handoff)
    )
    assert (
        "preflight JSON includes repository, optional canonicalized" in release_handoff
    )
    assert "`Target:`" in release_handoff
    assert "`Origin:`" in release_handoff
    assert "`Mode:`" in release_handoff
    assert "`Decision:`" in release_handoff
    assert "`target=`" in release_handoff
    assert "`path=`" in release_handoff
    assert "`blocker=`" in release_handoff
    assert "`mode=`" in release_handoff
    assert "`target_url=`" in release_handoff
    assert "`origin_url=`" in release_handoff
    assert "CLI help smoke checks" in readme
    assert "CLI help smoke checks" in release_handoff
    assert "CLI help smoke" in launch_plan
    assert "python scripts/alpha_release_bundle_manifest.py --json" in release_handoff
    assert "python scripts/alpha_release_bundle_manifest.py --json" in launch_plan
    assert "wheel and sdist metadata install smoke" in release_handoff
    assert "wheel and sdist metadata install smoke" in release_pr
    assert "wheel and sdist metadata install smoke" in github_release
    assert "54/54 fixtures" in commit_plan
    assert "54/54 fixtures, overall_rate 1.0" in release_pr
    assert "54/54 fixtures, overall_rate 1.0" in github_release
    assert "benchmark summary `snapshot` field" in commit_plan
    assert "python -m ruff check ." in commit_plan
    assert "`python -m ruff check .`: passed" in release_notes
    assert "`python -m ruff check .`: passed" in release_pr
    assert "`python -m ruff check .`: passed" in github_release
    assert "python -m ruff format --check ." in commit_plan
    assert "`python -m ruff format --check .`: 1014 files already formatted" in (
        release_notes
    )
    assert "`python -m ruff format --check .`: passed" in release_pr
    assert "`python -m ruff format --check .`: passed" in github_release
    assert "1014 files already formatted" in commit_plan
    assert "146 files already formatted" not in commit_plan
    assert "146 files already formatted" not in release_notes
    assert "146 files already formatted" not in release_pr
    assert "146 files already formatted" not in github_release
    assert "132 files already formatted" not in commit_plan
    assert "130 files already formatted" not in release_notes
    assert "130 files already formatted" not in release_pr
    assert "130 files already formatted" not in github_release
    assert "128 files already formatted" not in commit_plan
    assert "128 files already formatted" not in release_notes
    assert "128 files already formatted" not in release_pr
    assert "128 files already formatted" not in github_release
    assert "python -m mypy src tests" in commit_plan
    assert "`python -m mypy src tests`: 498 source files" in release_notes
    assert "`python -m mypy src tests`: passed" in release_pr
    assert "`python -m mypy src tests`: passed" in github_release
    assert "498 source files" in commit_plan
    assert "85 source files" not in commit_plan
    assert "85 source files" not in release_notes
    assert "85 source files" not in release_pr
    assert "85 source files" not in github_release
    assert "84 source files" not in commit_plan
    assert "84 source files" not in release_notes
    assert "84 source files" not in release_pr
    assert "84 source files" not in github_release
    assert "83 source files" not in commit_plan
    assert "83 source files" not in release_notes
    assert "83 source files" not in release_pr
    assert "83 source files" not in github_release
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
    assert "benchmarks/results-*" in release_handoff
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
    assert "configured `origin` remote" in release_plan
    assert "configured `origin` remote" in release_pr
    assert "configured `origin` remote" in github_release
    assert "qazedhq/qa-z" in release_pr
    assert "qazedhq/qa-z" in github_release
    assert "`actual_origin_target`" in release_notes
    assert "`actual_origin_target`" in release_pr
    assert "`actual_origin_target`" in github_release
    assert "`remote_ref_count`" in release_notes
    assert "`remote_ref_count`" in release_pr
    assert "`remote_ref_count`" in github_release
    assert "`remote_ref_head_count`" in release_notes
    assert "`remote_ref_head_count`" in release_pr
    assert "`remote_ref_head_count`" in github_release
    assert "`remote_ref_tag_count`" in release_notes
    assert "`remote_ref_tag_count`" in release_pr
    assert "`remote_ref_tag_count`" in github_release
    assert "`remote_ref_kinds`" in release_notes
    assert "`remote_ref_kinds`" in release_pr
    assert "`remote_ref_kinds`" in github_release
    assert "`publish_checklist`" in release_notes
    assert "`publish_checklist`" in release_pr
    assert "`publish_checklist`" in github_release
    assert "`publish_strategy=bootstrap_origin`" in release_notes
    assert "`publish_strategy=bootstrap_origin`" in release_pr
    assert "`publish_strategy=bootstrap_origin`" in github_release
    assert "`release_path_state`" in release_notes
    assert "`release_path_state`" in release_pr
    assert "`release_path_state`" in github_release
    assert "`remote_ref_sample`" in release_notes
    assert "`remote_ref_sample`" in release_pr
    assert "`remote_ref_sample`" in github_release
    assert "`next_action_count`" in release_notes
    assert "`next_action_count`" in release_pr
    assert "`next_action_count`" in github_release
    assert "`next_command_count`" in release_notes
    assert "`next_command_count`" in release_pr
    assert "`next_command_count`" in github_release
    assert "`ready_for_remote_checks`" in release_notes
    assert "`ready_for_remote_checks`" in release_pr
    assert "`ready_for_remote_checks`" in github_release
    assert "latest remote preflight still returns `404 Not Found`" in github_release
    assert "worktree is not releaseable as-is" not in release_plan
    assert "31 tracked modified files" not in release_plan
    assert "- [x] **Step 1: Run full deterministic validation**" in release_plan
    assert "- [x] **Step 2: Run CLI smoke checks**" in release_plan
    assert "- [x] **Step 3: Confirm worktree cleanliness**" in release_plan

    markdown_paths = [
        ROOT / "docs" / "releases" / "v0.9.8-alpha-github-release.md",
        ROOT / "docs" / "releases" / "v0.9.8-alpha-pr.md",
        ROOT / "docs" / "releases" / "v0.9.8-alpha-publish-handoff.md",
        ROOT / "docs" / "releases" / "v0.9.8-alpha.md",
        ROOT / "docs" / "reports" / "worktree-commit-plan.md",
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-18-github-repository-release.md",
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-19-github-repository-launch.md",
    ]
    for path in markdown_paths:
        assert not path.read_bytes().startswith(b"\xef\xbb\xbf"), path
