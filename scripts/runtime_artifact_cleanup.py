"""Preview or apply cleanup for policy-managed runtime artifacts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

sys.dont_write_bytecode = True

from qa_z.subprocess_env import build_tool_subprocess_env  # noqa: E402


def _load_runtime_artifact_cleanup_support_module():
    module_path = Path(__file__).with_name("runtime_artifact_cleanup_support.py")
    cached = sys.modules.get("runtime_artifact_cleanup_support")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == module_path.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "runtime_artifact_cleanup_support", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load runtime artifact cleanup support module: {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_RUNTIME_ARTIFACT_CLEANUP_SUPPORT = _load_runtime_artifact_cleanup_support_module()
Runner = _RUNTIME_ARTIFACT_CLEANUP_SUPPORT.Runner
candidate_cleanup_roots = _RUNTIME_ARTIFACT_CLEANUP_SUPPORT.candidate_cleanup_roots
collect_cleanup_plan = _RUNTIME_ARTIFACT_CLEANUP_SUPPORT.collect_cleanup_plan
delete_candidate_root = _RUNTIME_ARTIFACT_CLEANUP_SUPPORT.delete_candidate_root
render_human = _RUNTIME_ARTIFACT_CLEANUP_SUPPORT.render_human
tracked_paths_under = _RUNTIME_ARTIFACT_CLEANUP_SUPPORT.tracked_paths_under


def subprocess_runner(command: Sequence[str], cwd: Path) -> tuple[int, str, str]:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        env=build_tool_subprocess_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preview or apply cleanup for policy-managed runtime artifacts."
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=Path.cwd(),
        help="Repository root to inspect. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete untracked local-only roots.",
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = collect_cleanup_plan(
            args.path.resolve(),
            runner=subprocess_runner,
            apply=args.apply,
        )
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"runtime artifact cleanup failed: {exc}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render_human(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
