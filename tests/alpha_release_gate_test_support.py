from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_gate.py"
EVIDENCE_SCRIPT_PATH = ROOT / "scripts" / "alpha_release_gate_evidence.py"
WORKTREE_PLAN_SCRIPT_PATH = ROOT / "scripts" / "worktree_commit_plan.py"
GATE_TEST_PATH = ROOT / "tests" / "test_alpha_release_gate.py"
EVIDENCE_TEST_PATH = ROOT / "tests" / "test_alpha_release_gate_evidence.py"
RENDER_TEST_PATH = ROOT / "tests" / "test_alpha_release_gate_render.py"
OPTIONS_TEST_PATH = ROOT / "tests" / "test_alpha_release_gate_options.py"
CLI_TEST_PATH = ROOT / "tests" / "test_alpha_release_gate_cli.py"


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


def load_gate_module():
    return _load_module("alpha_release_gate", SCRIPT_PATH)


def load_gate_evidence_module():
    return _load_module("alpha_release_gate_evidence", EVIDENCE_SCRIPT_PATH)


def load_worktree_plan_module():
    return _load_module("worktree_commit_plan", WORKTREE_PLAN_SCRIPT_PATH)


class RecordingRunner:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.commands = []

    def __call__(self, command, cwd):
        self.commands.append(tuple(command))
        return self.responses.get(tuple(command), (0, "ok\n", ""))


def labels_from_result(result):
    return [check["label"] for check in result.payload["checks"]]
