"""No-upload package smoke rehearsal for QA-Z release readiness."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Sequence


def _load_package_smoke_rehearsal_support_module():
    module_path = Path(__file__).with_name("package_smoke_rehearsal_support.py")
    cached = sys.modules.get("package_smoke_rehearsal_support")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == module_path.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "package_smoke_rehearsal_support",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load package smoke rehearsal support module: {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_PACKAGE_SMOKE_REHEARSAL_SUPPORT = _load_package_smoke_rehearsal_support_module()
DEFAULT_WHEEL = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.DEFAULT_WHEEL
DEFAULT_SDIST = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.DEFAULT_SDIST
RehearsalCheck = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.RehearsalCheck
RehearsalResult = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.RehearsalResult
Runner = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.Runner
subprocess_runner = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.subprocess_runner
result_payload = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.result_payload
run_package_smoke_rehearsal = (
    _PACKAGE_SMOKE_REHEARSAL_SUPPORT.run_package_smoke_rehearsal
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run no-upload twine/pipx/uvx package smoke checks for QA-Z artifacts."
        )
    )
    parser.add_argument(
        "--wheel",
        default=str(DEFAULT_WHEEL),
        help=f"Wheel artifact to smoke test. Defaults to {DEFAULT_WHEEL}.",
    )
    parser.add_argument(
        "--sdist",
        default=str(DEFAULT_SDIST),
        help=f"Source distribution artifact for twine check. Defaults to {DEFAULT_SDIST}.",
    )
    parser.add_argument(
        "--allow-missing-tools",
        action="store_true",
        help="Report missing twine, pipx, or uvx as NOT_RUN instead of failing.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable no-upload rehearsal evidence as JSON.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = run_package_smoke_rehearsal(
        Path.cwd(),
        wheel=Path(args.wheel),
        sdist=Path(args.sdist),
        allow_missing_tools=args.allow_missing_tools,
    )
    if args.json:
        print(json.dumps(result_payload(result), indent=2))
    else:
        for check in result.checks:
            print(f"[{check.status}] {check.name}: {check.detail}")
        print(result.summary)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
