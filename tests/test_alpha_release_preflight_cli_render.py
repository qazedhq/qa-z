"""CLI, payload carry-forward, and human-render tests for alpha release preflight."""

from __future__ import annotations

import json

import pytest

from tests.alpha_release_preflight_test_support import (
    FakeRunner,
    base_responses,
    load_preflight_module,
    public_github_metadata,
)


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
    assert payload.pop("generated_at").endswith("Z")
    assert payload == {
        "summary": "release preflight passed",
        "exit_code": 0,
        "check_count": 2,
        "passed_count": 1,
        "failed_count": 0,
        "skipped_count": 1,
        "failed_checks": [],
        "repository_url": "https://github.com/qazedhq/qa-z.git",
        "repository_target": "qazedhq/qa-z",
        "expected_repository": "qazedhq/qa-z",
        "expected_origin_url": None,
        "expected_branch": "codex/qa-z-bootstrap",
        "expected_tag": "v0.9.8-alpha",
        "skip_remote": True,
        "allow_existing_refs": False,
        "allow_dirty": False,
        "remote_path": "skipped",
        "repository_probe_state": "skipped",
        "release_path_state": "local_only_preflight",
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


def test_preflight_cli_can_write_json_output(monkeypatch, tmp_path, capsys):
    module = load_preflight_module()
    output_path = tmp_path / "preflight" / "evidence.json"

    def fake_run_preflight(_repo_root, **kwargs):
        assert kwargs["skip_remote"] is True
        return module.PreflightResult(
            [module.CheckResult("current_branch", "passed", "codex/qa-z-bootstrap")]
        )

    monkeypatch.setattr(module, "run_preflight", fake_run_preflight)

    exit_code = module.main(["--skip-remote", "--json", "--output", str(output_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert output_path.exists()
    assert json.loads(output_path.read_text(encoding="utf-8")) == payload


def test_preflight_cli_can_write_output_without_printing_json(
    monkeypatch, tmp_path, capsys
):
    module = load_preflight_module()
    output_path = tmp_path / "nested" / "preflight" / "evidence.json"

    def fake_run_preflight(_repo_root, **kwargs):
        assert kwargs["skip_remote"] is True
        return module.PreflightResult(
            [module.CheckResult("current_branch", "passed", "codex/qa-z-bootstrap")]
        )

    monkeypatch.setattr(module, "run_preflight", fake_run_preflight)

    exit_code = module.main(["--skip-remote", "--output", str(output_path)])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert output_path.exists()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert payload["summary"] == "release preflight passed"
    assert payload["checks"][0]["name"] == "current_branch"
    assert "Generated at:" in captured.out
    assert (
        "Target: repository=qazedhq/qa-z; url=https://github.com/qazedhq/qa-z.git; "
        "repo_probe=skipped" in captured.out
    )
    assert "Origin: expected=(unset)" in captured.out
    assert (
        "Mode: branch=codex/qa-z-bootstrap; tag=v0.9.8-alpha; "
        "skip_remote=yes; allow_existing_refs=no; allow_dirty=no" in captured.out
    )
    assert "Decision: remote_path=skipped" in captured.out
    assert "release preflight passed" in captured.out
    assert captured.err == ""


def test_preflight_cli_reuses_last_known_probe_from_existing_output(
    monkeypatch, tmp_path, capsys
):
    module = load_preflight_module()
    monkeypatch.setattr(module, "utc_timestamp", lambda: "2026-04-21T06:00:00Z")
    output_path = tmp_path / "nested" / "preflight" / "evidence.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "summary": "release preflight passed",
                "repository_target": "qazedhq/qa-z",
                "repository_url": "https://github.com/qazedhq/qa-z.git",
                "repository_probe_state": "probed",
                "repository_probe_generated_at": "2026-04-21T05:20:00Z",
                "repository_http_status": 200,
                "repository_visibility": "public",
                "repository_archived": False,
                "repository_default_branch": "release",
            }
        ),
        encoding="utf-8",
    )

    def fake_run_preflight(_repo_root, **kwargs):
        assert kwargs["skip_remote"] is True
        return module.PreflightResult(
            [module.CheckResult("current_branch", "passed", "codex/qa-z-bootstrap")]
        )

    monkeypatch.setattr(module, "run_preflight", fake_run_preflight)

    exit_code = module.main(["--skip-remote", "--output", str(output_path)])

    captured = capsys.readouterr()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["repository_probe_state"] == "skipped"
    assert payload["repository_probe_basis"] == "last_known"
    assert payload["repository_probe_generated_at"] == "2026-04-21T05:20:00Z"
    assert payload["repository_http_status"] == 200
    assert payload["repository_visibility"] == "public"
    assert payload["repository_archived"] is False
    assert payload["repository_default_branch"] == "release"
    assert (
        "Target: repository=qazedhq/qa-z; url=https://github.com/qazedhq/qa-z.git; "
        "repo_probe=skipped; repo_probe_basis=last_known; "
        "repo_probe_at=2026-04-21T05:20:00Z; repo_probe_freshness=carried_forward; "
        "repo_probe_age_hours=" in captured.out
    )
    assert (
        "repo_http=200; "
        "repo_visibility=public; repo_archived=no; repo_default_branch=release"
        in captured.out
    )


def test_preflight_cli_ignores_last_known_probe_for_mismatched_repository(
    monkeypatch, tmp_path, capsys
):
    module = load_preflight_module()
    output_path = tmp_path / "nested" / "preflight" / "evidence.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(
            {
                "summary": "release preflight passed",
                "repository_target": "other/qa-z",
                "repository_url": "https://github.com/other/qa-z.git",
                "repository_probe_state": "probed",
                "repository_probe_generated_at": "2026-04-21T05:20:00Z",
                "repository_http_status": 200,
            }
        ),
        encoding="utf-8",
    )

    def fake_run_preflight(_repo_root, **kwargs):
        assert kwargs["skip_remote"] is True
        return module.PreflightResult(
            [module.CheckResult("current_branch", "passed", "codex/qa-z-bootstrap")]
        )

    monkeypatch.setattr(module, "run_preflight", fake_run_preflight)

    exit_code = module.main(["--skip-remote", "--output", str(output_path)])

    captured = capsys.readouterr()
    payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["repository_probe_state"] == "skipped"
    assert "repository_probe_basis" not in payload
    assert "repository_probe_generated_at" not in payload
    assert "repository_http_status" not in payload
    assert "repo_probe_basis=last_known" not in captured.out
    assert "repo_probe_at=2026-04-21T05:20:00Z" not in captured.out


def test_result_payload_marks_last_known_probe_as_stale_after_24h(
    monkeypatch, tmp_path
):
    module = load_preflight_module()
    monkeypatch.setattr(module, "utc_timestamp", lambda: "2026-04-21T06:00:00Z")

    payload = module.result_payload(
        module.run_preflight(
            tmp_path,
            skip_remote=True,
            runner=FakeRunner(base_responses()),
        ),
        skip_remote=True,
        prior_payload={
            "repository_target": "qazedhq/qa-z",
            "repository_url": "https://github.com/qazedhq/qa-z.git",
            "repository_probe_state": "probed",
            "repository_probe_generated_at": "2026-04-20T04:00:00Z",
            "repository_http_status": 200,
        },
    )

    assert payload["repository_probe_state"] == "skipped"
    assert payload["repository_probe_basis"] == "last_known"
    assert payload["repository_probe_freshness"] == "stale"
    assert payload["repository_probe_age_hours"] == 26


def test_result_payload_marks_current_probe_as_current(monkeypatch, tmp_path):
    module = load_preflight_module()
    monkeypatch.setattr(module, "utc_timestamp", lambda: "2026-04-21T06:00:00Z")
    responses = base_responses()
    responses[("git", "ls-remote", "--refs", "https://github.com/qazedhq/qa-z.git")] = (
        0,
        "",
        "",
    )

    payload = module.result_payload(
        module.run_preflight(
            tmp_path,
            repository_url="https://github.com/qazedhq/qa-z.git",
            runner=FakeRunner(responses),
            github_metadata_fetcher=public_github_metadata,
        ),
        repository_url="https://github.com/qazedhq/qa-z.git",
    )

    assert payload["repository_probe_state"] == "probed"
    assert payload["repository_probe_freshness"] == "current"
    assert payload["repository_probe_age_hours"] == 0


def test_render_preflight_human_prints_remote_blocker_decision() -> None:
    module = load_preflight_module()

    output = module.render_preflight_human(
        {
            "summary": "release preflight failed",
            "repository_url": "https://github.com/qazedhq/qa-z.git",
            "repository_target": "qazedhq/qa-z",
            "repository_probe_state": "probed",
            "repository_probe_generated_at": "2026-04-21T05:20:00Z",
            "repository_http_status": 404,
            "repository_visibility": "public",
            "repository_archived": False,
            "repository_default_branch": "release",
            "expected_origin_url": "https://github.com/qazedhq/qa-z.git",
            "expected_origin_target": "qazedhq/qa-z",
            "actual_origin_url": "https://github.com/qazedhq/qa-z.git",
            "actual_origin_target": "qazedhq/qa-z",
            "origin_state": "configured",
            "expected_branch": "codex/qa-z-bootstrap",
            "expected_tag": "v0.9.8-alpha",
            "skip_remote": False,
            "allow_existing_refs": True,
            "allow_dirty": False,
            "remote_path": "blocked",
            "remote_blocker": "release_tag_exists",
            "remote_ref_head_count": 1,
            "remote_ref_tag_count": 1,
            "remote_ref_kinds": ["heads", "tags"],
            "checks": [],
        }
    )

    assert (
        "Target: repository=qazedhq/qa-z; url=https://github.com/qazedhq/qa-z.git; "
        "repo_probe=probed; repo_probe_at=2026-04-21T05:20:00Z; repo_http=404; "
        "repo_visibility=public; repo_archived=no; repo_default_branch=release"
        in output
    )
    assert (
        "Origin: expected=qazedhq/qa-z; url=https://github.com/qazedhq/qa-z.git; "
        "actual_target=qazedhq/qa-z; actual=https://github.com/qazedhq/qa-z.git"
        in output
    )
    assert (
        "Decision: remote_path=blocked; release_path_state=blocked_existing_tag; "
        "remote_blocker=release_tag_exists; "
        "remote_ref_head_count=1; remote_ref_tag_count=1; "
        "remote_ref_kinds=heads,tags" in output
    )


def test_render_preflight_human_prints_missing_origin_state() -> None:
    module = load_preflight_module()

    output = module.render_preflight_human(
        {
            "summary": "release preflight passed",
            "repository_url": "https://github.com/qazedhq/qa-z.git",
            "repository_target": "qazedhq/qa-z",
            "repository_probe_state": "skipped",
            "origin_state": "missing",
            "expected_branch": "codex/qa-z-bootstrap",
            "expected_tag": "v0.9.8-alpha",
            "skip_remote": True,
            "allow_existing_refs": False,
            "allow_dirty": False,
            "remote_path": "skipped",
            "release_path_state": "local_only_bootstrap_origin",
            "publish_strategy": "bootstrap_origin",
            "publish_checklist": [
                "Add the intended origin with `git remote add origin https://github.com/qazedhq/qa-z.git`.",
                (
                    "Rerun remote preflight with `python scripts/alpha_release_preflight.py "
                    "--repository-url https://github.com/qazedhq/qa-z.git "
                    "--expected-origin-url https://github.com/qazedhq/qa-z.git "
                    "--allow-dirty --json`."
                ),
            ],
            "remote_readiness": "needs_origin_bootstrap",
            "checks": [],
        }
    )

    assert "Origin: expected=(unset); actual=missing" in output
    assert (
        "Target: repository=qazedhq/qa-z; url=https://github.com/qazedhq/qa-z.git; "
        "repo_probe=skipped"
    ) in output
    assert (
        "Decision: remote_path=skipped; release_path_state=local_only_bootstrap_origin; "
        "remote_readiness=needs_origin_bootstrap; publish_strategy=bootstrap_origin"
        in output
    )
    assert "Publish checklist:" in output


def test_render_preflight_human_prints_last_known_probe_basis() -> None:
    module = load_preflight_module()

    output = module.render_preflight_human(
        {
            "summary": "release preflight passed",
            "repository_url": "https://github.com/qazedhq/qa-z.git",
            "repository_target": "qazedhq/qa-z",
            "repository_probe_state": "skipped",
            "repository_probe_basis": "last_known",
            "repository_probe_generated_at": "2026-04-21T05:20:00Z",
            "repository_probe_freshness": "carried_forward",
            "repository_probe_age_hours": 1,
            "repository_http_status": 200,
            "repository_visibility": "public",
            "repository_archived": False,
            "repository_default_branch": "release",
            "origin_state": "configured",
            "actual_origin_url": "https://github.com/qazedhq/qa-z.git",
            "expected_origin_url": "https://github.com/qazedhq/qa-z.git",
            "expected_origin_target": "qazedhq/qa-z",
            "expected_branch": "codex/qa-z-bootstrap",
            "expected_tag": "v0.9.8-alpha",
            "skip_remote": True,
            "allow_existing_refs": False,
            "allow_dirty": False,
            "remote_path": "skipped",
            "release_path_state": "local_only_remote_preflight",
            "checks": [],
        }
    )

    assert (
        "Target: repository=qazedhq/qa-z; url=https://github.com/qazedhq/qa-z.git; "
        "repo_probe=skipped; repo_probe_basis=last_known; "
        "repo_probe_at=2026-04-21T05:20:00Z; repo_probe_freshness=carried_forward; "
        "repo_probe_age_hours=1; repo_http=200; "
        "repo_visibility=public; repo_archived=no; repo_default_branch=release"
        in output
    )


def test_render_preflight_human_prints_ready_for_remote_checks_decision() -> None:
    module = load_preflight_module()

    output = module.render_preflight_human(
        {
            "summary": "release preflight passed",
            "repository_url": "https://github.com/qazedhq/qa-z.git",
            "repository_target": "qazedhq/qa-z",
            "expected_origin_url": "https://github.com/qazedhq/qa-z.git",
            "expected_origin_target": "qazedhq/qa-z",
            "actual_origin_url": "git@github.com:qazedhq/qa-z.git",
            "origin_state": "configured",
            "expected_branch": "codex/qa-z-bootstrap",
            "expected_tag": "v0.9.8-alpha",
            "skip_remote": True,
            "allow_existing_refs": False,
            "allow_dirty": True,
            "remote_path": "skipped",
            "remote_readiness": "ready_for_remote_checks",
            "next_commands": [
                (
                    "python scripts/alpha_release_preflight.py --repository-url "
                    "https://github.com/qazedhq/qa-z.git --expected-origin-url "
                    "https://github.com/qazedhq/qa-z.git --allow-dirty --json"
                )
            ],
            "checks": [],
        }
    )

    assert (
        "Decision: remote_path=skipped; release_path_state=local_only_remote_preflight; "
        "remote_readiness=ready_for_remote_checks" in output
    )
    assert "Next commands:" in output


def test_render_preflight_human_prints_publish_checklist() -> None:
    module = load_preflight_module()

    output = module.render_preflight_human(
        {
            "summary": "release preflight passed",
            "repository_url": "https://github.com/qazedhq/qa-z.git",
            "repository_target": "qazedhq/qa-z",
            "expected_origin_url": "https://github.com/qazedhq/qa-z.git",
            "expected_origin_target": "qazedhq/qa-z",
            "actual_origin_url": "https://github.com/qazedhq/qa-z.git",
            "origin_state": "configured",
            "expected_branch": "codex/qa-z-bootstrap",
            "expected_tag": "v0.9.8-alpha",
            "skip_remote": False,
            "allow_existing_refs": False,
            "allow_dirty": False,
            "remote_path": "direct_publish",
            "publish_strategy": "push_default_branch",
            "publish_checklist": [
                "Push the validated release baseline to main with `git push -u origin HEAD:main`.",
                "Wait for remote CI before tagging.",
            ],
            "checks": [],
        }
    )

    assert (
        "Decision: remote_path=direct_publish; release_path_state=remote_direct_publish; "
        "publish_strategy=push_default_branch" in output
    )
    assert "Publish checklist:" in output
    assert (
        "- Push the validated release baseline to main with "
        "`git push -u origin HEAD:main`."
    ) in output


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
    assert payload["generated_at"].endswith("Z")
    assert payload["summary"] == "release preflight failed"
    assert payload["exit_code"] == 1
    assert payload["check_count"] == 1
    assert payload["passed_count"] == 0
    assert payload["failed_count"] == 1
    assert payload["skipped_count"] == 0
    assert payload["failed_checks"] == ["remote_reachable"]
    assert payload["checks"][0]["status"] == "failed"


def test_preflight_cli_writes_failed_output_with_counters(
    monkeypatch, tmp_path, capsys
):
    module = load_preflight_module()
    output_path = tmp_path / "failed" / "preflight.json"

    def fake_run_preflight(_repo_root, **_kwargs):
        return module.PreflightResult(
            [
                module.CheckResult("current_branch", "passed", "codex/qa-z-bootstrap"),
                module.CheckResult("github_repository", "failed", "404 Not Found"),
                module.CheckResult(
                    "remote_reachable", "failed", "Repository not found"
                ),
            ]
        )

    monkeypatch.setattr(module, "run_preflight", fake_run_preflight)

    exit_code = module.main(["--json", "--output", str(output_path)])

    captured = capsys.readouterr()
    stdout_payload = json.loads(captured.out)
    file_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 1
    assert file_payload == stdout_payload
    assert file_payload["check_count"] == 3
    assert file_payload["passed_count"] == 1
    assert file_payload["failed_count"] == 2
    assert file_payload["failed_checks"] == [
        "github_repository",
        "remote_reachable",
    ]
    assert file_payload["next_actions"] == [
        (
            "Create or expose the public GitHub repository qazedhq/qa-z, "
            "then rerun remote preflight for https://github.com/qazedhq/qa-z.git."
        )
    ]
