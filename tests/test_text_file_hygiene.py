"""Tests for tracked public text hygiene checks."""

from __future__ import annotations

import importlib.util
import sys
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
        "\n".join(f"line {index}" for index in range(30)) + "\n",
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


def test_suspiciously_collapsed_public_file_fails(tmp_path: Path) -> None:
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


def test_binary_file_is_skipped(tmp_path: Path) -> None:
    module = load_hygiene_module()
    image = tmp_path / "docs" / "assets" / "preview.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00")

    issues = module.check_paths(tmp_path, [image])

    assert issues == []
