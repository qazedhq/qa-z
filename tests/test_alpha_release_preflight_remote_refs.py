from __future__ import annotations

from tests.alpha_release_preflight_test_support import (
    FakeRunner,
    base_responses,
    load_preflight_module,
    public_github_metadata,
)


def test_preflight_fails_when_configured_origin_does_not_match_expected_url(tmp_path):
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
        expected_origin_url="https://github.com/qazedhq/qa-z.git",
        skip_remote=True,
        runner=FakeRunner(responses),
    )

    assert result.exit_code == 1
    assert result.by_name["origin_matches_expected"].status == "failed"
    assert result.by_name["origin_matches_expected"].detail == (
        "expected origin https://github.com/qazedhq/qa-z.git, "
        "got https://github.com/other/qa-z.git"
    )


def test_preflight_fails_when_remote_has_any_refs(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        (
            "1111111111111111111111111111111111111111\trefs/heads/main\n"
            "2222222222222222222222222222222222222222\trefs/heads/release/v0.9.8-alpha\n"
        ),
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        runner=FakeRunner(responses),
        github_metadata_fetcher=public_github_metadata,
    )

    assert result.exit_code == 1
    assert result.by_name["remote_reachable"].status == "passed"
    assert result.by_name["remote_empty"].status == "failed"
    assert "refs/heads/main" in result.by_name["remote_empty"].detail
    payload = module.result_payload(result)
    assert payload["next_actions"] == [
        (
            "Remote already has refs; choose the release PR path with "
            "--allow-existing-refs or publish to an empty repository."
        )
    ]
    assert payload["remote_ref_count"] == 2
    assert payload["remote_ref_head_count"] == 2
    assert payload["remote_ref_tag_count"] == 0
    assert payload["remote_ref_kinds"] == ["heads"]
    assert payload["remote_ref_sample"] == [
        "refs/heads/main",
        "refs/heads/release/v0.9.8-alpha",
    ]
    assert payload["next_commands"] == [
        "git ls-remote --refs https://github.com/qazedhq/qa-z.git",
        (
            "python scripts/alpha_release_preflight.py --repository-url "
            "https://github.com/qazedhq/qa-z.git --allow-existing-refs --json"
        ),
    ]


def test_preflight_allows_existing_refs_when_explicitly_requested(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        (
            "1111111111111111111111111111111111111111\trefs/heads/main\n"
            "2222222222222222222222222222222222222222\trefs/heads/release/v0.9.8-alpha\n"
        ),
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        allow_existing_refs=True,
        runner=FakeRunner(responses),
        github_metadata_fetcher=public_github_metadata,
    )

    assert result.exit_code == 0
    assert result.by_name["remote_reachable"].status == "passed"
    assert result.by_name["remote_empty"].status == "passed"
    assert "existing refs allowed for release PR path" in (
        result.by_name["remote_empty"].detail
    )
    assert "refs/heads/main" in result.by_name["remote_empty"].detail
    payload = module.result_payload(
        result,
        repository_url="https://github.com/qazedhq/qa-z.git",
        allow_existing_refs=True,
    )
    assert payload["remote_path"] == "release_pr"
    assert payload["release_path_state"] == "remote_release_pr"
    assert payload["publish_strategy"] == "push_release_branch"
    assert payload["remote_ref_count"] == 2
    assert payload["remote_ref_head_count"] == 2
    assert payload["remote_ref_tag_count"] == 0
    assert payload["remote_ref_kinds"] == ["heads"]
    assert payload["remote_ref_sample"] == [
        "refs/heads/main",
        "refs/heads/release/v0.9.8-alpha",
    ]
    assert payload["next_actions"] == [
        (
            "Remote bootstrap refs are present and the release PR path is ready; "
            "push codex/qa-z-bootstrap, open the release PR, and wait for remote "
            "CI before tagging."
        )
    ]
    assert payload["publish_checklist"] == [
        "Push the release branch with `git push -u origin codex/qa-z-bootstrap`.",
        "Open the release PR titled `Release QA-Z v0.9.8-alpha` with body `docs/releases/v0.9.8-alpha-pr.md`.",
        "Wait for remote CI: `test`, `Build package artifacts`, `Smoke test built package artifacts`, and `qa-z` must pass.",
        "Tag only after the release PR merges and the validated baseline is on the default branch.",
    ]
    assert payload["next_commands"] == ["git push -u origin codex/qa-z-bootstrap"]


def test_preflight_fails_when_existing_refs_include_release_tag_even_if_allowed(
    tmp_path,
):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        (
            "1111111111111111111111111111111111111111\trefs/heads/main\n"
            "2222222222222222222222222222222222222222\trefs/tags/v0.9.8-alpha\n"
        ),
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        allow_existing_refs=True,
        runner=FakeRunner(responses),
        github_metadata_fetcher=public_github_metadata,
    )

    assert result.exit_code == 1
    assert result.by_name["remote_reachable"].status == "passed"
    assert result.by_name["remote_empty"].status == "failed"
    assert "remote release tag already exists" in result.by_name["remote_empty"].detail
    assert "refs/tags/v0.9.8-alpha" in result.by_name["remote_empty"].detail
    payload = module.result_payload(result)
    assert payload["remote_path"] == "blocked"
    assert payload["release_path_state"] == "blocked_existing_tag"
    assert payload["remote_blocker"] == "release_tag_exists"
    assert payload["remote_ref_count"] == 2
    assert payload["remote_ref_head_count"] == 1
    assert payload["remote_ref_tag_count"] == 1
    assert payload["remote_ref_kinds"] == ["heads", "tags"]
    assert payload["remote_ref_sample"] == [
        "refs/tags/v0.9.8-alpha",
        "refs/heads/main",
    ]
    assert payload["next_actions"] == [
        (
            "Remote release tag v0.9.8-alpha already exists; inspect the existing "
            "tag before publishing a new alpha tag."
        )
    ]
    assert payload["next_commands"] == [
        "git ls-remote --refs https://github.com/qazedhq/qa-z.git refs/tags/v0.9.8-alpha"
    ]


def test_preflight_fails_for_wrong_github_repository_target(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/other/qa-z.git")] = (
        0,
        "",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/other/qa-z.git",
        runner=FakeRunner(responses),
        github_metadata_fetcher=public_github_metadata,
    )

    assert result.exit_code == 1
    assert result.by_name["github_repository"].status == "failed"
    assert "expected qazedhq/qa-z" in result.by_name["github_repository"].detail
    payload = module.result_payload(
        result, repository_url="https://github.com/other/qa-z.git"
    )
    assert payload["remote_path"] == "blocked"
    assert payload["remote_blocker"] == "repository_target_mismatch"
    assert "repository_probe_state" not in payload
    assert "repository_probe_generated_at" not in payload
    assert "repository_http_status" not in payload
    assert payload["next_actions"] == [
        (
            "Set --repository-url to https://github.com/qazedhq/qa-z.git, "
            "or update --expected-repository if a different public GitHub "
            "repository is intentional."
        )
    ]
    assert payload["next_commands"] == [
        (
            "python scripts/alpha_release_preflight.py --repository-url "
            "https://github.com/qazedhq/qa-z.git --json"
        )
    ]


def test_preflight_fails_for_non_github_repository_url(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://gitlab.com/qazedhq/qa-z.git")] = (
        0,
        "",
        "",
    )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://gitlab.com/qazedhq/qa-z.git",
        runner=FakeRunner(responses),
        github_metadata_fetcher=public_github_metadata,
    )

    assert result.exit_code == 1
    assert result.by_name["github_repository"].status == "failed"
    assert "github.com/qazedhq/qa-z" in result.by_name["github_repository"].detail
    payload = module.result_payload(
        result, repository_url="https://gitlab.com/qazedhq/qa-z.git"
    )
    assert "repository_probe_state" not in payload
    assert "repository_probe_generated_at" not in payload
    assert "repository_http_status" not in payload
    assert payload["next_actions"] == [
        (
            "Set --repository-url to https://github.com/qazedhq/qa-z.git, "
            "or update --expected-repository if a different public GitHub "
            "repository is intentional."
        )
    ]


def test_preflight_missing_repository_payload_handles_github_error_body(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        128,
        "",
        "remote: Repository not found.\nfatal: repository 'https://github.com/qazedhq/qa-z.git/' not found\n",
    )

    def github_not_found_with_docs_url(_api_url):
        return module.GitHubMetadataResult(
            404,
            {},
            (
                '{"message":"Not Found","documentation_url":"https://docs.github.com/rest/repos/repos#get-a-repository","status":"404"}'
            ),
        )

    result = module.run_preflight(
        tmp_path,
        repository_url="https://github.com/qazedhq/qa-z.git",
        runner=FakeRunner(responses),
        github_metadata_fetcher=github_not_found_with_docs_url,
    )

    payload = module.result_payload(
        result, repository_url="https://github.com/qazedhq/qa-z.git"
    )

    assert payload["repository_http_status"] == 404
    assert payload["repository_probe_state"] == "probed"
    assert payload["release_path_state"] == "blocked_repository"
    assert payload["remote_readiness"] == "needs_repository_bootstrap"
    assert payload["remote_blocker"] == "repository_missing"
