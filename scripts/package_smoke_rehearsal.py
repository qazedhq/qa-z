"""Safe local package smoke rehearsal for QA-Z release readiness."""

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
RehearsalError = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.RehearsalError
CheckResult = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.CheckResult
RehearsalResult = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.RehearsalResult
Runner = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.Runner
ToolSpec = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.ToolSpec
subprocess_runner = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.subprocess_runner
resolve_single_artifact = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.resolve_single_artifact
resolve_artifacts = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.resolve_artifacts
path_argument = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.path_argument
package_tool_specs = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.package_tool_specs
run_tool_spec = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.run_tool_spec
run_package_smoke_rehearsal = (
    _PACKAGE_SMOKE_REHEARSAL_SUPPORT.run_package_smoke_rehearsal
)
result_payload = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.result_payload
error_payload = _PACKAGE_SMOKE_REHEARSAL_SUPPORT.error_payload


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run local-only package smoke rehearsal checks without publishing, "
            "tagging, releasing, or deploying."
        )
    )
    parser.add_argument(
        "--wheel",
        help="Exact wheel artifact to use. Defaults to discovering one dist/*.whl.",
    )
    parser.add_argument(
        "--sdist",
        help=(
            "Exact source distribution artifact to include in twine check. "
            "Defaults to discovering one dist/*.tar.gz when present."
        ),
    )
    parser.add_argument(
        "--allow-missing-tools",
        action="store_true",
        help=(
            "Return success when missing twine, pipx, or uvx are recorded as "
            "NOT RUN instead of failing the whole rehearsal."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable rehearsal evidence as JSON.",
    )
    return parser.parse_args(argv)


def _print_human(payload: dict[str, object]) -> None:
    checks = payload.get("checks")
    print(f"{payload['summary']} (exit_code={payload['exit_code']})")
    print(f"wheel: {payload['wheel']}")
    print(f"sdist_paths: {payload['sdist_paths']}")
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, dict):
                continue
            command = check.get("command")
            rendered_command = " ".join(command) if isinstance(command, list) else ""
            print(
                f"[{check.get('status')}] {check.get('id')}: "
                f"{rendered_command} :: {check.get('reason')}"
            )
    print(f"registry_upload_executed={payload['registry_upload_executed']}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = Path.cwd()
    try:
        result = run_package_smoke_rehearsal(
            repo_root,
            wheel=args.wheel,
            sdist=args.sdist,
            allow_missing_tools=args.allow_missing_tools,
        )
        payload = result_payload(repo_root, result)
    except RehearsalError as exc:
        payload = error_payload(str(exc))

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_human(payload)
    return int(payload["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
