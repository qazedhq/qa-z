"""Tests for the alpha release preflight helper."""

from __future__ import annotations

from tests.alpha_release_preflight_test_support import (
    FakeRunner,
    base_responses,
    load_preflight_module,
)


def test_preflight_fails_when_github_repository_is_not_public(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        "",
        "",
    )

    def private_metadata(_api_url):
        return module.GitHubMetadataResult(
            200,
            {
                "full_name": "qazedhq/qa-z",
                "private": True,
                "visibility": "private",
                "archived": False,
            },
            "",
        )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        runner=FakeRunner(responses),
        github_metadata_fetcher=private_metadata,
    )

    assert result.exit_code == 1
    assert result.by_name["github_repository"].status == "failed"
    assert "not public" in result.by_name["github_repository"].detail


def test_preflight_fails_on_existing_tag_and_tracked_generated_artifacts(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "tag", "--list", "v0.9.8-alpha")] = (
        0,
        "v0.9.8-alpha\n",
        "",
    )
    responses[
        (
            "git",
            "ls-files",
            ".qa-z",
            ".mypy_cache",
            ".mypy_cache_safe",
            ".ruff_cache",
            ".ruff_cache_safe",
            "%TEMP%",
            "benchmarks/results",
            "benchmarks/results-*",
            "benchmarks/minlock-*",
            "dist",
            "build",
            "tmp_*",
            "src/qa_z.egg-info",
        )
    ] = (
        0,
        (
            "dist/qa_z-0.9.8a0.tar.gz\n"
            ".qa-z/runs/latest-run.json\n"
            "%TEMP%/qa-z-l27-full-benchmark/report.md\n"
            "tmp_mypy_smoke.py\n"
            "benchmarks/minlock-repro/.benchmark.lock\n"
            "benchmarks/results-l11/summary.json\n"
        ),
        "",
    )

    result = module.run_preflight(
        tmp_path, skip_remote=True, runner=FakeRunner(responses)
    )

    assert result.exit_code == 1
    assert result.by_name["release_tag_absent"].status == "failed"
    assert result.by_name["generated_artifacts_untracked"].status == "failed"
    detail = result.by_name["generated_artifacts_untracked"].detail
    assert "generated_local_only_tracked_count=5" in detail
    assert "generated_local_by_default_tracked_count=1" in detail
    assert (
        "generated_local_only_tracked_paths=dist/,.qa-z/,%TEMP%/,"
        "tmp_mypy_smoke.py,benchmarks/minlock-repro/" in detail
    )
    assert "generated_local_by_default_tracked_paths=benchmarks/results-l11/" in detail


def test_preflight_payload_splits_tracked_generated_artifacts_by_policy_bucket(
    tmp_path,
):
    module = load_preflight_module()
    responses = base_responses()
    responses[
        (
            "git",
            "ls-files",
            ".qa-z",
            ".mypy_cache",
            ".mypy_cache_safe",
            ".ruff_cache",
            ".ruff_cache_safe",
            "%TEMP%",
            "benchmarks/results",
            "benchmarks/results-*",
            "benchmarks/minlock-*",
            "dist",
            "build",
            "tmp_*",
            "src/qa_z.egg-info",
        )
    ] = (
        0,
        (
            "dist/qa_z-0.9.8a0.tar.gz\n"
            ".qa-z/runs/latest-run.json\n"
            ".mypy_cache_safe/3.10/cache.db\n"
            ".ruff_cache_safe/0.15.10/cache.db\n"
            "benchmarks/results-l31/summary.json\n"
            "benchmarks/results/report.md\n"
        ),
        "",
    )

    result = module.run_preflight(
        tmp_path, skip_remote=True, runner=FakeRunner(responses)
    )
    payload = module.result_payload(result, skip_remote=True)

    assert payload["tracked_generated_artifact_count"] == 6
    assert payload["generated_local_only_tracked_count"] == 4
    assert payload["generated_local_by_default_tracked_count"] == 2
    assert payload["generated_local_only_tracked_paths"] == [
        "dist/",
        ".qa-z/",
        ".mypy_cache_safe/",
        ".ruff_cache_safe/",
    ]
    assert payload["generated_local_by_default_tracked_paths"] == [
        "benchmarks/results-l31/",
        "benchmarks/results/",
    ]
    next_actions = payload["next_actions"]
    assert (
        "Remove or untrack tracked local-only generated artifacts before publish"
        in next_actions[0]
    )
    assert ".qa-z/" in next_actions[0]
    assert "dist/" in next_actions[0]
    assert (
        "Decide whether tracked benchmark result evidence stays local or is "
        "intentionally frozen with surrounding context before publish"
        in next_actions[1]
    )
    assert "benchmarks/results-l31/" in next_actions[1]
    assert "benchmarks/results/" in next_actions[1]


def test_preflight_scans_generated_benchmark_snapshot_dirs(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    runner = FakeRunner(responses)

    result = module.run_preflight(tmp_path, skip_remote=True, runner=runner)

    assert result.exit_code == 0
    assert (
        "git",
        "ls-files",
        ".qa-z",
        ".mypy_cache",
        ".mypy_cache_safe",
        ".ruff_cache",
        ".ruff_cache_safe",
        "%TEMP%",
        "benchmarks/results",
        "benchmarks/results-*",
        "benchmarks/minlock-*",
        "dist",
        "build",
        "tmp_*",
        "src/qa_z.egg-info",
    ) in runner.commands
