"""Tests for the alpha release bundle manifest helper."""

from __future__ import annotations

import json
from pathlib import Path

from tests.alpha_release_bundle_manifest_test_support import (
    FakeBundleRunner,
    load_manifest_module,
)


def write_artifacts(tmp_path: Path) -> tuple[Path, Path]:
    sdist = tmp_path / "dist" / "qa_z-0.9.8a0.tar.gz"
    wheel = tmp_path / "dist" / "qa_z-0.9.8a0-py3-none-any.whl"
    sdist.parent.mkdir()
    sdist.write_bytes(b"sdist")
    wheel.write_bytes(b"wheel")
    return sdist, wheel


def test_bundle_manifest_recreates_bundle_and_hashes_artifacts(tmp_path):
    module = load_manifest_module()
    sdist, wheel = write_artifacts(tmp_path)
    bundle = tmp_path / "dist" / "qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle"
    runner = FakeBundleRunner()

    result = module.run_bundle_manifest(
        tmp_path,
        branch="codex/qa-z-bootstrap",
        bundle_path=bundle,
        artifacts=[sdist, wheel],
        runner=runner,
    )

    assert result.exit_code == 0
    assert result.summary == "release bundle manifest passed"
    assert result.payload["head"] == "abc123"
    assert result.payload["bundle_path"] == str(bundle)
    assert result.payload["bundle_heads"] == ["abc123 refs/heads/codex/qa-z-bootstrap"]
    assert result.payload["artifacts"][str(bundle)]["sha256"]
    assert ("git", "bundle", "create", str(bundle), "codex/qa-z-bootstrap") in (
        runner.commands
    )
    assert ("git", "bundle", "verify", str(bundle)) in runner.commands
    assert ("git", "bundle", "list-heads", str(bundle)) in runner.commands


def test_bundle_manifest_fails_when_bundle_head_does_not_match_head(tmp_path):
    module = load_manifest_module()
    sdist, wheel = write_artifacts(tmp_path)
    bundle = tmp_path / "dist" / "qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle"

    result = module.run_bundle_manifest(
        tmp_path,
        branch="codex/qa-z-bootstrap",
        bundle_path=bundle,
        artifacts=[sdist, wheel],
        runner=FakeBundleRunner(branch_head="def456"),
    )

    assert result.exit_code == 1
    assert result.summary == "release bundle manifest failed"
    failed_checks = [
        check for check in result.payload["checks"] if check["status"] == "failed"
    ]
    assert failed_checks == [
        {
            "name": "branch_matches_head",
            "status": "failed",
            "detail": "codex/qa-z-bootstrap resolves to def456, but HEAD is abc123",
        }
    ]


def test_bundle_manifest_retries_existing_bundle_unlink_once(tmp_path, monkeypatch):
    module = load_manifest_module()
    sdist, wheel = write_artifacts(tmp_path)
    bundle = tmp_path / "dist" / "qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle"
    bundle.write_bytes(b"old-bundle")
    path_type = type(bundle)
    original_unlink = path_type.unlink
    calls = {"count": 0}

    def flaky_unlink(self):
        if self == bundle and calls["count"] == 0:
            calls["count"] += 1
            raise PermissionError("locked")
        return original_unlink(self)

    monkeypatch.setattr(path_type, "unlink", flaky_unlink)
    monkeypatch.setattr(module.time, "sleep", lambda _seconds: None)

    result = module.run_bundle_manifest(
        tmp_path,
        branch="codex/qa-z-bootstrap",
        bundle_path=bundle,
        artifacts=[sdist, wheel],
        runner=FakeBundleRunner(),
    )

    assert result.exit_code == 0
    assert calls["count"] == 1
    assert bundle.exists()


def test_bundle_manifest_cli_can_emit_json(monkeypatch, capsys):
    module = load_manifest_module()

    def fake_run_bundle_manifest(_repo_root, **kwargs):
        assert kwargs["branch"] == "codex/qa-z-bootstrap"
        assert kwargs["bundle_path"] == Path("dist/custom.bundle")
        assert kwargs["artifacts"] == [Path("dist/custom.tar.gz")]
        return module.BundleManifestResult(
            summary="release bundle manifest passed",
            exit_code=0,
            payload={
                "summary": "release bundle manifest passed",
                "exit_code": 0,
                "checks": [],
                "artifacts": {},
            },
        )

    monkeypatch.setattr(module, "run_bundle_manifest", fake_run_bundle_manifest)

    exit_code = module.main(
        [
            "--bundle",
            "dist/custom.bundle",
            "--artifact",
            "dist/custom.tar.gz",
            "--json",
        ]
    )

    assert exit_code == 0
    assert json.loads(capsys.readouterr().out)["summary"] == (
        "release bundle manifest passed"
    )
