"""Tests for the alpha release bundle manifest helper."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_bundle_manifest.py"


def load_manifest_module():
    spec = importlib.util.spec_from_file_location(
        "alpha_release_bundle_manifest", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeRunner:
    def __init__(self, branch_head: str = "abc123") -> None:
        self.branch_head = branch_head
        self.commands: list[tuple[str, ...]] = []

    def __call__(self, command, cwd):
        command_tuple = tuple(str(part) for part in command)
        self.commands.append(command_tuple)
        if command_tuple == ("git", "rev-parse", "HEAD"):
            return 0, "abc123\n", ""
        if command_tuple == ("git", "rev-parse", "codex/qa-z-bootstrap"):
            return 0, f"{self.branch_head}\n", ""
        if command_tuple[:3] == ("git", "bundle", "create"):
            Path(command_tuple[3]).write_bytes(b"bundle")
            return 0, "", ""
        if command_tuple[:3] == ("git", "bundle", "verify"):
            return 0, "bundle is okay\n", ""
        if command_tuple[:3] == ("git", "bundle", "list-heads"):
            return 0, f"{self.branch_head} refs/heads/codex/qa-z-bootstrap\n", ""
        return 0, "", ""


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
    runner = FakeRunner()

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
        runner=FakeRunner(branch_head="def456"),
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
