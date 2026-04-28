"""Remote and origin-contract tests for the alpha release preflight helper."""

from __future__ import annotations

from tests.alpha_release_preflight_test_support import (
    FakeRunner,
    base_responses,
    load_preflight_module,
    missing_github_metadata,
    public_github_metadata,
    public_release_branch_metadata,
)


def test_preflight_passes_when_local_clean_and_empty_remote_reachable(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        "",
        "",
    )
    runner = FakeRunner(responses)

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        runner=runner,
        github_metadata_fetcher=public_github_metadata,
    )

    assert result.exit_code == 0
    assert result.summary == "release preflight passed"
    assert result.by_name["github_repository"].status == "passed"
    assert result.by_name["remote_reachable"].status == "passed"
    assert result.by_name["remote_empty"].status == "passed"
    payload = module.result_payload(
        result, repository_url="https://github.com/qazedhq/qa-z.git"
    )
    assert payload["repository_http_status"] == 200
    assert payload["repository_probe_state"] == "probed"
    assert payload["repository_probe_generated_at"] == payload["generated_at"]
    assert payload["remote_path"] == "direct_publish"
    assert payload["release_path_state"] == "remote_direct_publish"
    assert payload["publish_strategy"] == "push_default_branch"
    assert payload["next_actions"] == [
        (
            "Remote is empty and ready for direct publish; push the release "
            "baseline to main, wait for remote CI, and tag only after the "
            "validated default branch is green."
        )
    ]
    assert payload["publish_checklist"] == [
        "Push the validated release baseline to main with `git push -u origin HEAD:main`.",
        "Wait for remote CI: `test`, `Build package artifacts`, `Smoke test built package artifacts`, and `qa-z` must pass.",
        "Create and verify `v0.9.8-alpha` from the validated default branch, then `git push origin v0.9.8-alpha`.",
    ]
    assert payload["next_commands"] == ["git push -u origin HEAD:main"]
    assert ("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git") in (
        runner.commands
    )


def test_preflight_preserves_github_repository_metadata_in_payload(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        "",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        runner=FakeRunner(responses),
        github_metadata_fetcher=public_release_branch_metadata,
    )

    payload = module.result_payload(
        result, repository_url="https://github.com/qazedhq/qa-z.git"
    )

    assert payload["repository_http_status"] == 200
    assert payload["repository_probe_state"] == "probed"
    assert payload["repository_probe_generated_at"] == payload["generated_at"]
    assert payload["repository_visibility"] == "public"
    assert payload["repository_archived"] is False
    assert payload["repository_default_branch"] == "release"


def test_preflight_direct_publish_guidance_uses_repository_default_branch(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        "",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        runner=FakeRunner(responses),
        github_metadata_fetcher=public_release_branch_metadata,
    )
    payload = module.result_payload(
        result, repository_url="https://github.com/qazedhq/qa-z.git"
    )

    assert payload["publish_checklist"] == [
        "Push the validated release baseline to release with `git push -u origin HEAD:release`.",
        "Wait for remote CI: `test`, `Build package artifacts`, `Smoke test built package artifacts`, and `qa-z` must pass.",
        "Create and verify `v0.9.8-alpha` from the validated default branch, then `git push origin v0.9.8-alpha`.",
    ]
    assert payload["next_actions"] == [
        (
            "Remote is empty and ready for direct publish; push the release "
            "baseline to release, wait for remote CI, and tag only after the "
            "validated default branch is green."
        )
    ]
    assert payload["next_commands"] == ["git push -u origin HEAD:release"]


def test_preflight_fails_when_remote_is_missing(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        128,
        "",
        "remote: Repository not found.\n",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        runner=FakeRunner(responses),
        github_metadata_fetcher=missing_github_metadata,
    )

    assert result.exit_code == 1
    assert result.summary == "release preflight failed"
    assert result.by_name["remote_reachable"].status == "failed"
    assert "Repository not found" in result.by_name["remote_reachable"].detail
    payload = module.result_payload(
        result, repository_url="https://github.com/qazedhq/qa-z.git"
    )
    assert payload["repository_http_status"] == 404
    assert payload["repository_probe_state"] == "probed"
    assert payload["repository_probe_generated_at"] == payload["generated_at"]
    assert payload["remote_path"] == "blocked"
    assert payload["remote_blocker"] == "repository_missing"


def test_preflight_dirty_worktree_failure_has_next_action(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "status", "--short")] = (
        0,
        " M README.md\n?? benchmarks/fixtures/new_case/\n",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        skip_remote=True,
        runner=FakeRunner(responses),
    )
    payload = module.result_payload(result, skip_remote=True)

    assert result.exit_code == 1
    assert result.by_name["worktree_clean"].status == "failed"
    assert payload["next_actions"] == [
        (
            "Commit, stash, or intentionally rerun with --allow-dirty before "
            "publishing; the worktree_clean check must be clean for release."
        )
    ]


def test_preflight_skip_remote_marks_repository_probe_state_skipped(tmp_path):
    module = load_preflight_module()
    result = module.run_preflight(
        tmp_path,
        skip_remote=True,
        runner=FakeRunner(base_responses()),
    )

    payload = module.result_payload(result, skip_remote=True)

    assert payload["repository_probe_state"] == "skipped"
    assert "repository_probe_generated_at" not in payload


def test_preflight_allows_configured_origin_when_expected_url_matches(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "remote", "get-url", "origin")] = (
        0,
        "https://github.com/qazedhq/qa-z.git\n",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
        runner=FakeRunner(responses),
    )

    assert result.exit_code == 0
    assert result.by_name["origin_matches_expected"].status == "passed"
    assert result.by_name["origin_matches_expected"].detail == (
        "https://github.com/qazedhq/qa-z.git"
    )


def test_preflight_blocks_unexpected_origin_when_expectation_is_omitted(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "remote", "get-url", "origin")] = (
        0,
        "https://github.com/qazedhq/qa-z.git\n",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
        runner=FakeRunner(responses),
    )
    payload = module.result_payload(
        result,
        repository_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
    )

    assert result.by_name["origin_absent"].status == "failed"
    assert payload["remote_path"] == "blocked"
    assert payload["remote_blocker"] == "origin_present"
    assert payload["origin_state"] == "configured"
    assert payload["actual_origin_url"] == "https://github.com/qazedhq/qa-z.git"
    assert payload["next_actions"] == [
        (
            "Origin is already configured; rerun preflight with "
            "--expected-origin-url if that remote is intentional."
        )
    ]
    assert payload["next_commands"] == [
        (
            "python scripts/alpha_release_preflight.py --skip-remote "
            "--repository-url https://github.com/qazedhq/qa-z.git "
            "--expected-origin-url https://github.com/qazedhq/qa-z.git --json"
        )
    ]


def test_preflight_allows_equivalent_origin_url_forms(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "remote", "get-url", "origin")] = (
        0,
        "git@github.com:qazedhq/qa-z.git\n",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
        runner=FakeRunner(responses),
    )

    assert result.exit_code == 0
    assert result.by_name["origin_matches_expected"].status == "passed"
    assert result.by_name["origin_matches_expected"].detail == (
        "git@github.com:qazedhq/qa-z.git"
    )


def test_preflight_allows_ssh_url_origin_form(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "remote", "get-url", "origin")] = (
        0,
        "ssh://git@github.com/qazedhq/qa-z.git\n",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
        runner=FakeRunner(responses),
    )

    assert result.exit_code == 0
    assert result.by_name["origin_matches_expected"].status == "passed"
    assert result.by_name["origin_matches_expected"].detail == (
        "ssh://git@github.com/qazedhq/qa-z.git"
    )


def test_preflight_allows_ssh_url_origin_form_with_explicit_port(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "remote", "get-url", "origin")] = (
        0,
        "ssh://git@github.com:22/qazedhq/qa-z.git\n",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
        runner=FakeRunner(responses),
    )

    assert result.exit_code == 0
    assert result.by_name["origin_matches_expected"].status == "passed"
    assert result.by_name["origin_matches_expected"].detail == (
        "ssh://git@github.com:22/qazedhq/qa-z.git"
    )


def test_preflight_allows_schemeless_github_origin_url_form(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "remote", "get-url", "origin")] = (
        0,
        "github.com/qazedhq/qa-z.git\n",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
        runner=FakeRunner(responses),
    )

    assert result.exit_code == 0
    assert result.by_name["origin_matches_expected"].status == "passed"
    assert result.by_name["origin_matches_expected"].detail == (
        "github.com/qazedhq/qa-z.git"
    )


def test_preflight_fails_when_expected_origin_targets_different_repository(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "remote", "get-url", "origin")] = (
        0,
        "https://github.com/other/qa-z.git\n",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/other/qa-z.git",
        skip_remote=True,
        runner=FakeRunner(responses),
    )

    assert result.exit_code == 1
    assert result.by_name["origin_target_matches_repository"].status == "failed"
    assert result.by_name["origin_target_matches_repository"].detail == (
        "expected origin target other/qa-z does not match repository target qazedhq/qa-z"
    )
    payload = module.result_payload(
        result,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/other/qa-z.git",
        skip_remote=True,
    )
    assert payload["next_actions"] == [
        (
            "Set origin to the intended repository URL, then rerun preflight "
            "with --expected-origin-url."
        )
    ]
    assert payload["next_commands"] == [
        "git remote set-url origin https://github.com/qazedhq/qa-z.git",
        (
            "python scripts/alpha_release_preflight.py --skip-remote "
            "--repository-url https://github.com/qazedhq/qa-z.git "
            "--expected-origin-url https://github.com/qazedhq/qa-z.git --json"
        ),
    ]


def test_preflight_origin_target_mismatch_without_origin_uses_add_origin_command(
    tmp_path,
):
    module = load_preflight_module()
    responses = base_responses()

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/other/qa-z.git",
        skip_remote=True,
        runner=FakeRunner(responses),
    )

    payload = module.result_payload(
        result,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/other/qa-z.git",
        skip_remote=True,
    )

    assert payload["remote_blocker"] == "origin_target_mismatch"
    assert payload["next_commands"] == [
        "git remote add origin https://github.com/qazedhq/qa-z.git",
        (
            "python scripts/alpha_release_preflight.py --skip-remote "
            "--repository-url https://github.com/qazedhq/qa-z.git "
            "--expected-origin-url https://github.com/qazedhq/qa-z.git --json"
        ),
    ]


def test_preflight_payload_records_expected_origin_target_when_github_url():
    module = load_preflight_module()
    result = module.PreflightResult(
        [
            module.CheckResult(
                "origin_matches_expected",
                "passed",
                "https://github.com/qazedhq/qa-z.git",
            )
        ]
    )

    payload = module.result_payload(
        result,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="ssh://git@github.com/qazedhq/qa-z.git",
        skip_remote=True,
    )

    assert payload["repository_target"] == "qazedhq/qa-z"
    assert payload["expected_origin_target"] == "qazedhq/qa-z"


def test_preflight_payload_records_missing_origin_state_when_origin_unconfigured():
    module = load_preflight_module()
    result = module.PreflightResult(
        [
            module.CheckResult("origin_absent", "passed", "origin is not configured"),
        ]
    )

    payload = module.result_payload(result, skip_remote=True)

    assert payload["origin_state"] == "missing"
    assert "actual_origin_url" not in payload


def test_preflight_payload_guides_origin_bootstrap_when_remote_checks_are_skipped():
    module = load_preflight_module()
    result = module.PreflightResult(
        [
            module.CheckResult("origin_absent", "passed", "origin is not configured"),
        ]
    )

    payload = module.result_payload(
        result,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_repository="qazedhq/qa-z",
        skip_remote=True,
        allow_dirty=True,
    )

    assert payload["remote_path"] == "skipped"
    assert payload["release_path_state"] == "local_only_bootstrap_origin"
    assert payload["remote_readiness"] == "needs_origin_bootstrap"
    assert payload["publish_strategy"] == "bootstrap_origin"
    assert payload["publish_checklist"] == [
        "Add the intended origin with `git remote add origin https://github.com/qazedhq/qa-z.git`.",
        (
            "Rerun remote preflight with `python scripts/alpha_release_preflight.py "
            "--repository-url https://github.com/qazedhq/qa-z.git "
            "--expected-origin-url https://github.com/qazedhq/qa-z.git "
            "--allow-dirty --json`."
        ),
    ]
    assert payload["next_actions"] == [
        (
            "Configure origin and rerun remote preflight before public publish; "
            "skip-remote only defers the remote bootstrap step."
        )
    ]
    assert payload["next_commands"] == [
        "git remote add origin https://github.com/qazedhq/qa-z.git",
        (
            "python scripts/alpha_release_preflight.py --repository-url "
            "https://github.com/qazedhq/qa-z.git --expected-origin-url "
            "https://github.com/qazedhq/qa-z.git --allow-dirty --json"
        ),
    ]


def test_preflight_payload_guides_remote_checks_when_origin_is_ready():
    module = load_preflight_module()
    result = module.PreflightResult(
        [
            module.CheckResult(
                "origin_matches_expected",
                "passed",
                "git@github.com:qazedhq/qa-z.git",
            ),
            module.CheckResult(
                "origin_target_matches_repository",
                "passed",
                "qazedhq/qa-z",
            ),
        ]
    )

    payload = module.result_payload(
        result,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_repository="qazedhq/qa-z",
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
        allow_dirty=True,
    )

    assert payload["remote_path"] == "skipped"
    assert payload["release_path_state"] == "local_only_remote_preflight"
    assert payload["remote_readiness"] == "ready_for_remote_checks"
    assert payload["next_actions"] == [
        (
            "Run remote preflight against qazedhq/qa-z before public publish; "
            "skip-remote only covers local readiness."
        )
    ]
    assert payload["next_commands"] == [
        (
            "python scripts/alpha_release_preflight.py --repository-url "
            "https://github.com/qazedhq/qa-z.git --expected-origin-url "
            "https://github.com/qazedhq/qa-z.git --allow-dirty --json"
        )
    ]


def test_preflight_payload_records_actual_origin_url_when_origin_is_configured(
    tmp_path,
):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "remote", "get-url", "origin")] = (
        0,
        "https://github.com/qazedhq/qa-z.git\n",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        skip_remote=True,
        runner=FakeRunner(responses),
    )
    payload = module.result_payload(result, skip_remote=True)

    assert payload["origin_state"] == "configured"
    assert payload["actual_origin_url"] == "https://github.com/qazedhq/qa-z.git"


def test_preflight_payload_records_actual_origin_target_when_origin_is_github():
    module = load_preflight_module()
    result = module.PreflightResult(
        [
            module.CheckResult(
                "origin_matches_expected",
                "failed",
                (
                    "expected origin https://github.com/qazedhq/qa-z.git, "
                    "got git@github.com:other/qa-z.git"
                ),
            )
        ]
    )

    payload = module.result_payload(
        result,
        repository_url="https://github.com/qazedhq/qa-z.git",
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
    )

    assert payload["actual_origin_url"] == "git@github.com:other/qa-z.git"
    assert payload["actual_origin_target"] == "other/qa-z"


def test_parse_github_repository_target_accepts_schemeless_github_url():
    module = load_preflight_module()

    target = module.parse_github_repository_target("github.com/qazedhq/qa-z.git")

    assert target is not None
    assert target.full_name == "qazedhq/qa-z"
    assert target.api_url == "https://api.github.com/repos/qazedhq/qa-z"
