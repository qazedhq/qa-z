"""Install-smoke checks for QA-Z alpha release artifacts."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Sequence


def _load_artifact_smoke_support_module():
    module_path = Path(__file__).with_name("alpha_release_artifact_smoke_support.py")
    cached = sys.modules.get("alpha_release_artifact_smoke_support")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == module_path.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "alpha_release_artifact_smoke_support",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load artifact smoke support module: {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT = _load_artifact_smoke_support_module()
DEFAULT_VERSION = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.DEFAULT_VERSION
DEFAULT_WHEEL = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.DEFAULT_WHEEL
DEFAULT_SDIST = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.DEFAULT_SDIST
CheckResult = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.CheckResult
SmokeResult = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.SmokeResult
Runner = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.Runner
subprocess_runner = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.subprocess_runner
result_payload = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.result_payload
artifact_label = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.artifact_label
venv_python_path = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.venv_python_path
venv_script_path = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.venv_script_path
validation_code = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.validation_code
command_detail = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.command_detail
smoke_artifact = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.smoke_artifact
run_artifact_smoke = _ALPHA_RELEASE_ARTIFACT_SMOKE_SUPPORT.run_artifact_smoke


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install built QA-Z alpha artifacts in fresh virtualenvs."
    )
    parser.add_argument(
        "--wheel",
        default=str(DEFAULT_WHEEL),
        help=f"Wheel artifact to smoke test. Defaults to {DEFAULT_WHEEL}.",
    )
    parser.add_argument(
        "--sdist",
        default=str(DEFAULT_SDIST),
        help=f"Source distribution artifact to smoke test. Defaults to {DEFAULT_SDIST}.",
    )
    parser.add_argument(
        "--expected-version",
        default=DEFAULT_VERSION,
        help=f"Expected qa-z package version. Defaults to {DEFAULT_VERSION}.",
    )
    parser.add_argument(
        "--with-deps",
        action="store_true",
        help=(
            "Allow pip dependency resolution and additionally run installed CLI help "
            "and init smoke checks. May contact the configured package index."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable install-smoke evidence as JSON.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    artifacts = [Path(args.wheel), Path(args.sdist)]
    result = run_artifact_smoke(
        Path.cwd(),
        artifacts=artifacts,
        expected_version=args.expected_version,
        with_deps=args.with_deps,
    )
    if args.json:
        print(json.dumps(result_payload(result), indent=2))
    else:
        for check in result.checks:
            print(f"[{check.status.upper()}] {check.name}: {check.detail}")
        print(result.summary)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
