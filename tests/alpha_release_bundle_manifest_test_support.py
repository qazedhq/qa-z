from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_bundle_manifest.py"


def load_manifest_module():
    cached = sys.modules.get("alpha_release_bundle_manifest")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "alpha_release_bundle_manifest", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeBundleRunner:
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
