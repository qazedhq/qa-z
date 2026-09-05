from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "package_smoke_rehearsal.py"


def load_rehearsal_module():
    cached = sys.modules.get("package_smoke_rehearsal")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "package_smoke_rehearsal", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class FakeRehearsalRunner:
    def __init__(self, unavailable_tools: set[str] | None = None) -> None:
        self.commands: list[tuple[str, ...]] = []
        self.unavailable_tools = unavailable_tools or set()

    def __call__(self, command: Sequence[object], _cwd: Path):
        command_tuple = tuple(str(part) for part in command)
        self.commands.append(command_tuple)
        label = " ".join(command_tuple)
        if self._is_unavailable(command_tuple):
            return 1, "", f"{command_tuple[0]} missing"
        return 0, f"{label} ok\n", ""

    def _is_unavailable(self, command: tuple[str, ...]) -> bool:
        if "twine" in self.unavailable_tools and "twine" in command:
            return True
        if "pipx" in self.unavailable_tools and command and command[0] == "pipx":
            return True
        if "uvx" in self.unavailable_tools and command and command[0] == "uvx":
            return True
        return False
