from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "runtime_artifact_cleanup.py"


def load_cleanup_module():
    cached = sys.modules.get("runtime_artifact_cleanup")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "runtime_artifact_cleanup", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRunner:
    def __init__(self, responses):
        self.responses = responses
        self.commands = []

    def __call__(self, command, cwd):
        key = tuple(command)
        self.commands.append(key)
        return self.responses[key]
