"""Tests for tracked public text hygiene checks."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from io import BytesIO
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_text_file_hygiene.py"


def load_hygiene_module():
    cached = sys.modules.get("check_text_file_hygiene")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "check_text_file_hygiene", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_lf_text_file_passes(tmp_path: Path) -> None:
    module = load_hygiene_module()
    readme = tmp_path / "README.md"
    readme.write_text(
        "\n".join(f"line {index}" for index in range(100)) + "\n",
        newline="\n",
    )

    issues = module.check_paths(tmp_path, [readme])

    assert issues == []


def test_crlf_text_file_fails(tmp_path: Path) -> None:
    module = load_hygiene_module()
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir()
    source.write_bytes(b"print('hi')\r\n")

    issues = module.check_paths(tmp_path, [source])

    assert [(issue.path, issue.reason) for issue in issues] == [
        ("src/app.py", "contains CRLF line endings")
    ]


def test_cr_only_text_file_fails(tmp_path: Path) -> None:
    module = load_hygiene_module()
    source = tmp_path / "src" / "app.py"
    source.parent.mkdir()
    source.write_bytes(b"print('hi')\rprint('bye')\r")

    issues = module.check_paths(tmp_path, [source])

    assert [(issue.path, issue.reason) for issue in issues] == [
        ("src/app.py", "contains CR-only line endings")
    ]


def test_suspiciously_collapsed_readme_fails(tmp_path: Path) -> None:
    module = load_hygiene_module()
    readme = tmp_path / "README.md"
    readme.write_text(
        "# QA-Z " + ("collapsed " * 80) + "\n",
        encoding="utf-8",
        newline="\n",
    )

    issues = module.check_paths(tmp_path, [readme])

    assert issues
    assert issues[0].path == "README.md"
    assert "suspiciously collapsed" in issues[0].reason


def test_suspiciously_collapsed_yaml_fails(tmp_path: Path) -> None:
    module = load_hygiene_module()
    workflow = tmp_path / ".github" / "workflows" / "ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "name: CI on: [push] jobs: test: runs-on: ubuntu-latest steps: "
        + ("- run: python -m pytest " * 20),
        encoding="utf-8",
        newline="\n",
    )

    issues = module.check_paths(tmp_path, [workflow])

    assert issues
    assert issues[0].path == ".github/workflows/ci.yml"
    assert "suspiciously collapsed" in issues[0].reason


def test_suspiciously_collapsed_python_fails(tmp_path: Path) -> None:
    module = load_hygiene_module()
    source = tmp_path / "scripts" / "check_text_file_hygiene.py"
    source.parent.mkdir()
    source.write_text(
        "def check(): " + ("print('collapsed') " * 60),
        encoding="utf-8",
        newline="\n",
    )

    issues = module.check_paths(tmp_path, [source])

    assert issues
    assert issues[0].path == "scripts/check_text_file_hygiene.py"
    assert "suspiciously collapsed" in issues[0].reason


def test_collapsed_skill_front_matter_fails(tmp_path: Path) -> None:
    module = load_hygiene_module()
    skill = tmp_path / "skills" / "example" / "SKILL.md"
    skill.parent.mkdir(parents=True)
    skill.write_text(
        "--- name: example description: collapsed --- # Example",
        encoding="utf-8",
        newline="\n",
    )

    issues = module.check_paths(tmp_path, [skill])

    assert issues
    assert issues[0].path == "skills/example/SKILL.md"
    assert "YAML front matter" in issues[0].reason


def test_binary_file_is_skipped(tmp_path: Path) -> None:
    module = load_hygiene_module()
    image = tmp_path / "docs" / "assets" / "preview.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00")

    issues = module.check_paths(tmp_path, [image])

    assert issues == []


def test_source_git_head_reads_committed_blob(tmp_path: Path) -> None:
    module = load_hygiene_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "qa-z@example.com")
    run_git(repo, "config", "user.name", "QA-Z")
    readme = repo / "README.md"
    readme.write_text(
        "\n".join(f"line {index}" for index in range(100)) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "initial")
    readme.write_text("# QA-Z " + ("collapsed " * 80), encoding="utf-8")

    assert module.main(["--path", str(repo), "--source", "git-head"]) == 0
    assert module.main(["--path", str(repo), "--source", "working-tree"]) == 1


def test_source_git_ref_reads_requested_ref(tmp_path: Path) -> None:
    module = load_hygiene_module()
    repo = tmp_path / "repo"
    repo.mkdir()
    run_git(repo, "init")
    run_git(repo, "config", "user.email", "qa-z@example.com")
    run_git(repo, "config", "user.name", "QA-Z")
    readme = repo / "README.md"
    readme.write_text(
        "\n".join(f"line {index}" for index in range(100)) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "good")
    run_git(repo, "branch", "good-ref")
    readme.write_text("# QA-Z " + ("collapsed " * 80), encoding="utf-8")
    run_git(repo, "add", "README.md")
    run_git(repo, "commit", "-m", "collapsed")

    assert module.main(["--path", str(repo), "--source", "git-ref", "good-ref"]) == 0
    assert module.main(["--path", str(repo), "--source", "git-ref", "HEAD"]) == 1


def test_source_raw_url_fails_on_collapsed_content(monkeypatch) -> None:
    module = load_hygiene_module()

    def fake_urlopen(request, timeout=30):
        return FakeResponse(b"# QA-Z " + (b"collapsed " * 80))

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    assert (
        module.main(
            [
                "--source",
                "raw-url",
                "https://raw.githubusercontent.com/qazedhq/qa-z/codex/topic/README.md",
            ]
        )
        == 1
    )


def test_source_raw_url_passes_on_lf_multiline_content(monkeypatch) -> None:
    module = load_hygiene_module()

    def fake_urlopen(request, timeout=30):
        return FakeResponse(
            ("\n".join(f"line {index}" for index in range(100)) + "\n").encode()
        )

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    assert (
        module.main(
            [
                "--source",
                "raw-url",
                "https://raw.githubusercontent.com/qazedhq/qa-z/codex/topic/README.md",
            ]
        )
        == 0
    )


def test_critical_profile_public_is_accepted() -> None:
    module = load_hygiene_module()

    assert module.parse_critical_profile("public") == "public"
    assert ".github/actions/qa-z/action.yml" in module.CRITICAL_MIN_LINES


class FakeResponse:
    status = 200

    def __init__(self, data: bytes) -> None:
        self._stream = BytesIO(data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def read(self) -> bytes:
        return self._stream.read()


def run_git(repo: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
