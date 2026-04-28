from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_preflight.py"
EVIDENCE_SCRIPT_PATH = ROOT / "scripts" / "alpha_release_preflight_evidence.py"
REMOTE_TEST_PATH = ROOT / "tests" / "test_alpha_release_preflight_remote.py"
REMOTE_REFS_TEST_PATH = ROOT / "tests" / "test_alpha_release_preflight_remote_refs.py"
CLI_RENDER_TEST_PATH = ROOT / "tests" / "test_alpha_release_preflight_cli_render.py"


def _load_module(name: str, path: Path):
    cached = sys.modules.get(name)
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == path.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_preflight_module():
    return _load_module("alpha_release_preflight", SCRIPT_PATH)


def load_preflight_evidence_module():
    return _load_module("alpha_release_preflight_evidence", EVIDENCE_SCRIPT_PATH)


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
            "default_branch": "main",
        },
        "",
    )


def public_release_branch_metadata(_api_url):
    module = load_preflight_module()
    return module.GitHubMetadataResult(
        200,
        {
            "full_name": "qazedhq/qa-z",
            "private": False,
            "visibility": "public",
            "archived": False,
            "default_branch": "release",
        },
        "",
    )


def missing_github_metadata(_api_url):
    module = load_preflight_module()
    return module.GitHubMetadataResult(404, {}, "Not Found")


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
            ".mypy_cache",
            ".mypy_cache_safe",
            ".ruff_cache",
            ".ruff_cache_safe",
            "%TEMP%",
            "benchmarks/results",
            "benchmarks/results-*",
            "benchmarks/minlock-*",
            "dist",
            "build",
            "tmp_*",
            "src/qa_z.egg-info",
        ): (0, "", ""),
        ("git", "rev-parse", "HEAD"): (
            0,
            "9a51bad2018024ca8bf0a28e2d085225c802e01e\n",
            "",
        ),
    }
