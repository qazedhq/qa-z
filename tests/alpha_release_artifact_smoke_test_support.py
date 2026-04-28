from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_artifact_smoke.py"


def load_smoke_module():
    cached = sys.modules.get("alpha_release_artifact_smoke")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "alpha_release_artifact_smoke", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeSmokeRunner:
    def __init__(self, failing_command_fragment: str = "") -> None:
        self.commands: list[tuple[str, ...]] = []
        self.failing_command_fragment = failing_command_fragment

    def __call__(self, command: Sequence[object], _cwd: Path):
        command_tuple = tuple(str(part) for part in command)
        self.commands.append(command_tuple)
        if self.failing_command_fragment and any(
            self.failing_command_fragment in part for part in command_tuple
        ):
            return 1, "", f"{self.failing_command_fragment} failed"
        self._simulate_side_effects(command_tuple)
        return 0, "ok\n", ""

    def _simulate_side_effects(self, command: tuple[str, ...]) -> None:
        if "init" not in command or "--path" not in command:
            return
        target = Path(command[command.index("--path") + 1])
        (target / "qa" / "contracts").mkdir(parents=True, exist_ok=True)
        (target / "qa-z.yaml").write_text("project:\n  name: smoke\n", encoding="utf-8")
        (target / "qa" / "contracts" / "README.md").write_text(
            "# QA Contracts\n",
            encoding="utf-8",
        )
        if "--with-agent-templates" in command:
            (target / "AGENTS.md").write_text("# AGENTS.md\n", encoding="utf-8")
            (target / "CLAUDE.md").write_text("# CLAUDE.md\n", encoding="utf-8")
