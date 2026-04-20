"""Tests for the alpha release preflight helper."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_preflight.py"


def load_preflight_module():
    spec = importlib.util.spec_from_file_location(
        "alpha_release_preflight", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses
        self.commands = []

    def __call__(self, command, cwd):
        self.commands.append(tuple(command))
        response = self.responses.get(tuple(command))
        if response is None:
            return 0, "", ""
        return response


def public_github_metadata(_api_url):
    module = load_preflight_module()
    return module.GitHubMetadataResult(
        200,
        {
            "full_name": "qazedhq/qa-z",
            "private": False,
            "visibility": "public",
            "archived": False,
        },
        "",
    )


def base_responses():
    return {
        ("git", "branch", "--show-current"): (0, "codex/qa-z-bootstrap\n", ""),
        ("git", "status", "--short"): (0, "", ""),
        ("git", "remote", "get-url", "origin"): (2, "", "No such remote 'origin'\n"),
        ("git", "tag", "--list", "v0.9.8-alpha"): (0, "", ""),
        (
            "git",
            "ls-files",
            ".qa-z",
            "benchmarks/results",
            "dist",
            "build",
            "src/qa_z.egg-info",
        ): (0, "", ""),
        ("git", "rev-parse", "HEAD"): (
            0,
            "9a51bad2018024ca8bf0a28e2d085225c802e01e\n",
            "",
        ),
    }


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
    assert ("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git") in (
        runner.commands
    )


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
        github_metadata_fetcher=public_github_metadata,
    )

    assert result.exit_code == 1
    assert result.summary == "release preflight failed"
    assert result.by_name["remote_reachable"].status == "failed"
    assert "Repository not found" in result.by_name["remote_reachable"].detail


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
        "1111111111111111111111111111111111111111\trefs/heads/main\n",
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


def test_preflight_allows_existing_refs_when_explicitly_requested(tmp_path):
    module = load_preflight_module()
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        "1111111111111111111111111111111111111111\trefs/heads/main\n",
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


def test_preflight_cli_accepts_existing_ref_pr_path_flag(capsys):
    module = load_preflight_module()

    args = module.parse_args(["--allow-existing-refs"])

    assert args.allow_existing_refs is True

    with pytest.raises(SystemExit) as excinfo:
        module.parse_args(["--help"])

    captured = capsys.readouterr()
    assert excinfo.value.code == 0
    assert "Skip GitHub metadata and git ls-remote checks" in captured.out


def test_preflight_cli_accepts_expected_repository_override():
    module = load_preflight_module()

    args = module.parse_args(["--expected-repository", "example/qa-z"])

    assert args.expected_repository == "example/qa-z"


def test_preflight_cli_accepts_expected_origin_url_override():
    module = load_preflight_module()

    args = module.parse_args(
        ["--expected-origin-url", "https://github.com/qazedhq/qa-z.git"]
    )

    assert args.expected_origin_url == "https://github.com/qazedhq/qa-z.git"


def test_preflight_cli_can_emit_json_summary(monkeypatch, capsys):
    module = load_preflight_module()

    def fake_run_preflight(_repo_root, **kwargs):
        assert kwargs["expected_repository"] == "qazedhq/qa-z"
        assert kwargs["expected_origin_url"] is None
        return module.PreflightResult(
            [
                module.CheckResult("current_branch", "passed", "codex/qa-z-bootstrap"),
                module.CheckResult("remote_empty", "skipped", "remote check skipped"),
            ]
        )

    monkeypatch.setattr(module, "run_preflight", fake_run_preflight)

    exit_code = module.main(["--skip-remote", "--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload == {
        "summary": "release preflight passed",
        "exit_code": 0,
        "checks": [
            {
                "name": "current_branch",
                "status": "passed",
                "detail": "codex/qa-z-bootstrap",
            },
            {
                "name": "remote_empty",
                "status": "skipped",
                "detail": "remote check skipped",
            },
        ],
    }
    assert captured.err == ""


def test_preflight_cli_json_preserves_failed_exit_code(monkeypatch, capsys):
    module = load_preflight_module()

    def fake_run_preflight(_repo_root, **_kwargs):
        return module.PreflightResult(
            [module.CheckResult("remote_reachable", "failed", "Repository not found")]
        )

    monkeypatch.setattr(module, "run_preflight", fake_run_preflight)

    exit_code = module.main(["--json"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 1
    assert payload["summary"] == "release preflight failed"
    assert payload["exit_code"] == 1
    assert payload["checks"][0]["status"] == "failed"


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
            "benchmarks/results",
            "dist",
            "build",
            "src/qa_z.egg-info",
        )
    ] = (0, "dist/qa_z-0.9.8a0.tar.gz\n.qa-z/runs/latest-run.json\n", "")

    result = module.run_preflight(
        tmp_path, skip_remote=True, runner=FakeRunner(responses)
    )

    assert result.exit_code == 1
    assert result.by_name["release_tag_absent"].status == "failed"
    assert result.by_name["generated_artifacts_untracked"].status == "failed"
    assert "dist/qa_z-0.9.8a0.tar.gz" in (
        result.by_name["generated_artifacts_untracked"].detail
    )
