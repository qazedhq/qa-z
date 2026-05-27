from __future__ import annotations

from pathlib import Path

import pytest

from qa_z.cli import main
from qa_z import profile_detection
from qa_z.profile_detection import detect_profile, nested_package_json_evidence


def write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_detects_python_repo_from_python_metadata(tmp_path: Path) -> None:
    write(tmp_path / "pyproject.toml", "[project]\nname = 'demo'\n")

    result = detect_profile(tmp_path)

    assert result.profile == "python"
    assert result.confidence == "high"
    assert "pyproject.toml" in result.evidence_files
    assert "Python fast checks" in result.activated_check_assumptions


def test_detects_typescript_repo_from_package_and_tsconfig(tmp_path: Path) -> None:
    write(tmp_path / "package.json", '{"scripts":{"test":"vitest run"}}\n')
    write(tmp_path / "tsconfig.json", "{}\n")

    result = detect_profile(tmp_path)

    assert result.profile == "typescript"
    assert result.confidence == "high"
    assert result.evidence_files == ("package.json", "tsconfig.json")
    assert "TypeScript fast checks" in result.activated_check_assumptions


def test_detects_nextjs_repo_from_config_and_dependency(tmp_path: Path) -> None:
    write(
        tmp_path / "package.json",
        '{"dependencies":{"next":"15.0.0","react":"19.0.0"}}\n',
    )
    write(tmp_path / "next.config.mjs", "export default {}\n")
    write(tmp_path / "tsconfig.json", "{}\n")

    result = detect_profile(tmp_path)

    assert result.profile == "nextjs"
    assert result.confidence == "high"
    assert result.evidence_files == (
        "package.json",
        "tsconfig.json",
        "next.config.mjs",
    )
    assert "Next.js TypeScript surface" in result.activated_check_assumptions


def test_detects_monorepo_from_workspace_and_layout(tmp_path: Path) -> None:
    write(tmp_path / "pnpm-workspace.yaml", "packages:\n  - apps/*\n  - packages/*\n")
    write(tmp_path / "turbo.json", '{"tasks":{}}\n')
    write(tmp_path / "apps" / "web" / "package.json", "{}\n")
    write(tmp_path / "packages" / "api" / "pyproject.toml", "[project]\n")

    result = detect_profile(tmp_path)

    assert result.profile == "monorepo"
    assert result.confidence == "high"
    assert "pnpm-workspace.yaml" in result.evidence_files
    assert "apps/" in result.evidence_files
    assert "packages/" in result.evidence_files
    assert "smart selection" in result.activated_check_assumptions


def test_detects_mixed_repo_warning_without_workspace(tmp_path: Path) -> None:
    write(tmp_path / "requirements.txt", "pytest\n")
    write(tmp_path / "package.json", '{"devDependencies":{"typescript":"latest"}}\n')

    result = detect_profile(tmp_path)

    assert result.profile == "mixed"
    assert result.confidence == "medium"
    assert "requirements.txt" in result.evidence_files
    assert "package.json" in result.evidence_files
    assert result.warnings == (
        "Python and TypeScript signals were both found without monorepo layout signals.",
    )


def test_detects_unknown_repo_with_repair_hint(tmp_path: Path) -> None:
    result = detect_profile(tmp_path)

    assert result.profile == "unknown"
    assert result.confidence == "low"
    assert result.evidence_files == ()
    assert result.warnings == (
        "No Python, TypeScript, Next.js, or monorepo signals were found.",
    )


def test_auto_dry_run_does_not_write_config_and_explains_evidence(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    write(tmp_path / "pyproject.toml", "[project]\nname = 'demo'\n")

    exit_code = main(
        ["init", "--path", str(tmp_path), "--profile", "auto", "--dry-run"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert not (tmp_path / "qa-z.yaml").exists()
    assert "QA-Z init profile detection: python" in output
    assert "confidence: high" in output
    assert "evidence: pyproject.toml" in output
    assert "activated checks: Python fast checks, Semgrep deep checks" in output
    assert "would write: qa-z.yaml" in output
    assert "next command: qa-z init --profile python" in output


def test_auto_dry_run_preserves_existing_config(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    existing = "project:\n  profile: python\n"
    write(tmp_path / "qa-z.yaml", existing)
    write(tmp_path / "package.json", "{}\n")

    exit_code = main(
        ["init", "--path", str(tmp_path), "--profile", "auto", "--dry-run"]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert (tmp_path / "qa-z.yaml").read_text(encoding="utf-8") == existing
    assert "evidence: qa-z.yaml" in output
    assert "existing qa-z.yaml will not be overwritten" in output


def test_nested_package_json_evidence_prunes_generated_directories(
    tmp_path: Path,
) -> None:
    write(tmp_path / "node_modules" / "dep" / "package.json", "{}\n")
    write(tmp_path / "dist" / "bundle" / "package.json", "{}\n")
    write(tmp_path / "build" / "tmp" / "package.json", "{}\n")
    write(tmp_path / "packages" / "web" / "package.json", "{}\n")

    evidence = nested_package_json_evidence(tmp_path)

    assert evidence == ["packages/web/package.json"]


def test_nested_package_json_evidence_ignores_walk_errors(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write(tmp_path / "packages" / "web" / "package.json", "{}\n")

    def fail_walk(*_args: object, **_kwargs: object) -> object:
        raise PermissionError("blocked")

    monkeypatch.setattr(profile_detection.os, "walk", fail_walk)

    assert nested_package_json_evidence(tmp_path) == []
