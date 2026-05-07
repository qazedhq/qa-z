"""Tests for public raw GitHub text hygiene checks."""

from __future__ import annotations

import importlib.util
import sys
from io import BytesIO
from pathlib import Path
from urllib.error import URLError


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "check_public_raw_urls.py"


def load_public_raw_module():
    cached = sys.modules.get("check_public_raw_urls")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location("check_public_raw_urls", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def good_multiline_bytes(module, url: str) -> bytes:
    for path, minimum in module.CRITICAL_MIN_LF.items():
        if url.endswith(path):
            return (
                "\n".join(f"{path} line {index}" for index in range(minimum)) + "\n"
            ).encode()
    raise AssertionError(f"unexpected URL: {url}")


def run_main_with_fake_urls(module, monkeypatch, fake_bytes_for_url) -> int:
    def fake_urlopen(request, timeout=30):
        url = request.full_url
        return FakeResponse(fake_bytes_for_url(url))

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)
    return module.main(
        [
            "--repo",
            "qazedhq/qa-z",
            "--ref",
            "codex/topic",
            "--commit",
            "abc123",
        ]
    )


def test_collapsed_readme_fails(monkeypatch, capsys) -> None:
    module = load_public_raw_module()

    def fake_bytes(url: str) -> bytes:
        if url.endswith("README.md"):
            return b"# QA-Z " + (b"collapsed " * 80)
        return good_multiline_bytes(module, url)

    assert run_main_with_fake_urls(module, monkeypatch, fake_bytes) == 1

    output = capsys.readouterr().out
    assert "README.md" in output
    assert "critical file appears collapsed" in output


def test_collapsed_python_fails(monkeypatch, capsys) -> None:
    module = load_public_raw_module()

    def fake_bytes(url: str) -> bytes:
        if url.endswith("scripts/check_text_file_hygiene.py"):
            return b"def check(): " + (b"print('collapsed') " * 60)
        return good_multiline_bytes(module, url)

    assert run_main_with_fake_urls(module, monkeypatch, fake_bytes) == 1

    output = capsys.readouterr().out
    assert "scripts/check_text_file_hygiene.py" in output
    assert "critical file appears collapsed" in output


def test_lf_multiline_files_pass(monkeypatch, capsys) -> None:
    module = load_public_raw_module()

    assert (
        run_main_with_fake_urls(
            module,
            monkeypatch,
            lambda url: good_multiline_bytes(module, url),
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "public raw URL hygiene passed" in output


def test_cr_only_fails(monkeypatch, capsys) -> None:
    module = load_public_raw_module()

    def fake_bytes(url: str) -> bytes:
        if url.endswith("pyproject.toml"):
            return b"[project]\rname = 'qa-z'\r"
        return good_multiline_bytes(module, url)

    assert run_main_with_fake_urls(module, monkeypatch, fake_bytes) == 1

    output = capsys.readouterr().out
    assert "pyproject.toml" in output
    assert "contains CR-only line endings" in output


def test_crlf_fails(monkeypatch, capsys) -> None:
    module = load_public_raw_module()

    def fake_bytes(url: str) -> bytes:
        if url.endswith(".github/actions/guard/action.yml"):
            return b"name: QA-Z Guard\r\nruns:\r\n  using: composite\r\n"
        return good_multiline_bytes(module, url)

    assert run_main_with_fake_urls(module, monkeypatch, fake_bytes) == 1

    output = capsys.readouterr().out
    assert ".github/actions/guard/action.yml" in output
    assert "contains CRLF line endings" in output


def test_url_fetch_failure_fails_clearly(monkeypatch, capsys) -> None:
    module = load_public_raw_module()

    def fake_urlopen(request, timeout=30):
        raise URLError("network unavailable")

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    assert (
        module.main(
            [
                "--repo",
                "qazedhq/qa-z",
                "--ref",
                "codex/topic",
                "--commit",
                "abc123",
            ]
        )
        == 1
    )

    output = capsys.readouterr().out
    assert "fetch failed" in output
    assert "network unavailable" in output


def test_checks_branch_and_commit_refs(monkeypatch) -> None:
    module = load_public_raw_module()
    requested_urls: list[str] = []

    def fake_urlopen(request, timeout=30):
        requested_urls.append(request.full_url)
        return FakeResponse(good_multiline_bytes(module, request.full_url))

    monkeypatch.setattr(module.urllib.request, "urlopen", fake_urlopen)

    assert (
        module.main(
            [
                "--repo",
                "qazedhq/qa-z",
                "--ref",
                "codex/topic",
                "--commit",
                "abc123",
            ]
        )
        == 0
    )

    assert any("/qazedhq/qa-z/codex/topic/README.md" in url for url in requested_urls)
    assert any("/qazedhq/qa-z/abc123/README.md" in url for url in requested_urls)
    assert len(requested_urls) == len(module.CRITICAL_MIN_LF) * 2


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
