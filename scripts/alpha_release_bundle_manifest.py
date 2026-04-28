"""Rebuild and verify the QA-Z alpha release bundle manifest."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path
from typing import Sequence


def _load_bundle_manifest_support_module():
    module_path = Path(__file__).with_name("alpha_release_bundle_manifest_support.py")
    cached = sys.modules.get("alpha_release_bundle_manifest_support")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == module_path.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "alpha_release_bundle_manifest_support",
        module_path,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load bundle manifest support module: {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT = _load_bundle_manifest_support_module()
DEFAULT_BRANCH = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.DEFAULT_BRANCH
DEFAULT_BUNDLE = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.DEFAULT_BUNDLE
DEFAULT_ARTIFACTS = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.DEFAULT_ARTIFACTS
CheckResult = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.CheckResult
BundleManifestResult = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.BundleManifestResult
Runner = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.Runner
time = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.time
subprocess_runner = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.subprocess_runner
unlink_with_retries = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.unlink_with_retries
actual_path = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.actual_path
command_detail = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.command_detail
sha256_file = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.sha256_file
finish_payload = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.finish_payload
run_bundle_manifest = _ALPHA_RELEASE_BUNDLE_MANIFEST_SUPPORT.run_bundle_manifest


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild, verify, and hash the QA-Z alpha release bundle."
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Branch ref to bundle. Defaults to {DEFAULT_BRANCH}.",
    )
    parser.add_argument(
        "--bundle",
        default=str(DEFAULT_BUNDLE),
        help=f"Bundle output path. Defaults to {DEFAULT_BUNDLE}.",
    )
    parser.add_argument(
        "--artifact",
        action="append",
        default=None,
        help=(
            "Release artifact to hash. May be passed multiple times. "
            "Defaults to the QA-Z alpha sdist and wheel."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable bundle manifest evidence as JSON.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    artifacts = (
        [Path(artifact) for artifact in args.artifact]
        if args.artifact
        else list(DEFAULT_ARTIFACTS)
    )
    result = run_bundle_manifest(
        Path.cwd(),
        branch=args.branch,
        bundle_path=Path(args.bundle),
        artifacts=artifacts,
    )
    if args.json:
        print(json.dumps(result.payload, indent=2))
    else:
        checks_payload = result.payload["checks"]
        assert isinstance(checks_payload, list)
        for check in checks_payload:
            assert isinstance(check, dict)
            status = str(check["status"]).upper()
            print(f"[{status}] {check['name']}: {check['detail']}")
        print(result.summary)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
