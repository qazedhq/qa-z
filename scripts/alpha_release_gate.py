"""Run the deterministic local QA-Z alpha release gate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable
from typing import NamedTuple
from typing import Sequence


TAIL_LIMIT = 4000
DEFAULT_REPOSITORY_FULL_NAME = "qazedhq/qa-z"
DEFAULT_REPOSITORY_URL = "https://github.com/qazedhq/qa-z.git"


class GateCommand(NamedTuple):
    name: str
    label: str
    command: tuple[str, ...]


class AlphaReleaseGateResult(NamedTuple):
    summary: str
    exit_code: int
    commands: Sequence[Sequence[str]]
    payload: dict[str, object]


Runner = Callable[[Sequence[str], Path], tuple[int, str, str]]


def subprocess_runner(command: Sequence[str], cwd: Path) -> tuple[int, str, str]:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.returncode, completed.stdout, completed.stderr


def python_command(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


def cli_help_commands() -> list[GateCommand]:
    help_surfaces = [
        (),
        ("init",),
        ("plan",),
        ("fast",),
        ("deep",),
        ("review",),
        ("repair-prompt",),
        ("repair-session",),
        ("github-summary",),
        ("verify",),
        ("benchmark",),
        ("self-inspect",),
        ("select-next",),
        ("backlog",),
        ("autonomy",),
        ("executor-bridge",),
        ("executor-result",),
    ]
    commands: list[GateCommand] = []
    for surface in help_surfaces:
        name = "cli_help_root" if not surface else f"cli_help_{surface[0]}"
        label = " ".join(("python", "-m", "qa_z", *surface, "--help"))
        commands.append(
            GateCommand(
                name.replace("-", "_"),
                label,
                python_command("-m", "qa_z", *surface, "--help"),
            )
        )
    return commands


def default_gate_commands(
    *,
    with_deps: bool = False,
    allow_dirty: bool = False,
    include_remote: bool = False,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    expected_origin_url: str | None = None,
    allow_existing_refs: bool = False,
    preflight_output: Path | None = None,
) -> list[GateCommand]:
    remote_options_requested = (
        repository_url != DEFAULT_REPOSITORY_URL
        or expected_repository != DEFAULT_REPOSITORY_FULL_NAME
        or expected_origin_url is not None
        or allow_existing_refs
    )
    effective_include_remote = include_remote or remote_options_requested
    effective_expected_origin_url = (
        repository_url
        if effective_include_remote and expected_origin_url is None
        else expected_origin_url
    )
    preflight_args = ["scripts/alpha_release_preflight.py"]
    preflight_label_parts = ["python", "scripts/alpha_release_preflight.py"]
    if effective_include_remote:
        preflight_args.extend(["--repository-url", repository_url])
        preflight_label_parts.extend(["--repository-url", repository_url])
        if expected_repository != DEFAULT_REPOSITORY_FULL_NAME:
            preflight_args.extend(["--expected-repository", expected_repository])
            preflight_label_parts.extend(["--expected-repository", expected_repository])
        if effective_expected_origin_url is not None:
            preflight_args.extend(
                ["--expected-origin-url", effective_expected_origin_url]
            )
            preflight_label_parts.extend(
                ["--expected-origin-url", effective_expected_origin_url]
            )
        if allow_existing_refs:
            preflight_args.append("--allow-existing-refs")
            preflight_label_parts.append("--allow-existing-refs")
    else:
        preflight_args.append("--skip-remote")
        preflight_label_parts.append("--skip-remote")
    if allow_dirty:
        preflight_args.append("--allow-dirty")
        preflight_label_parts.append("--allow-dirty")
    if preflight_output is not None:
        preflight_args.extend(["--output", str(preflight_output)])
        preflight_label_parts.extend(["--output", str(preflight_output)])
    preflight_args.append("--json")
    preflight_label_parts.append("--json")

    commands = [
        GateCommand(
            "local_preflight",
            " ".join(preflight_label_parts),
            python_command(*preflight_args),
        ),
        GateCommand(
            "ruff_format",
            "python -m ruff format --check .",
            python_command("-m", "ruff", "format", "--check", "."),
        ),
        GateCommand(
            "ruff_check",
            "python -m ruff check .",
            python_command("-m", "ruff", "check", "."),
        ),
        GateCommand(
            "mypy",
            "python -m mypy src tests",
            python_command("-m", "mypy", "src", "tests"),
        ),
        GateCommand(
            "pytest",
            "python -m pytest",
            python_command("-m", "pytest"),
        ),
        *cli_help_commands(),
        GateCommand(
            "qa_z_fast",
            "python -m qa_z fast --selection smart --json",
            python_command("-m", "qa_z", "fast", "--selection", "smart", "--json"),
        ),
        GateCommand(
            "qa_z_deep",
            "python -m qa_z deep --selection smart --json",
            python_command("-m", "qa_z", "deep", "--selection", "smart", "--json"),
        ),
        GateCommand(
            "qa_z_benchmark",
            "python -m qa_z benchmark --json",
            python_command("-m", "qa_z", "benchmark", "--json"),
        ),
        GateCommand(
            "build",
            "python -m build --sdist --wheel",
            python_command("-m", "build", "--sdist", "--wheel"),
        ),
        GateCommand(
            "artifact_smoke",
            "python scripts/alpha_release_artifact_smoke.py --json",
            python_command("scripts/alpha_release_artifact_smoke.py", "--json"),
        ),
    ]

    if with_deps:
        commands.append(
            GateCommand(
                "artifact_smoke_with_deps",
                "python scripts/alpha_release_artifact_smoke.py --with-deps --json",
                python_command(
                    "scripts/alpha_release_artifact_smoke.py",
                    "--with-deps",
                    "--json",
                ),
            )
        )

    commands.append(
        GateCommand(
            "bundle_manifest",
            "python scripts/alpha_release_bundle_manifest.py --json",
            python_command("scripts/alpha_release_bundle_manifest.py", "--json"),
        )
    )
    return commands


def output_tail(output: str) -> str:
    return output.strip()[-TAIL_LIMIT:]


def preflight_next_actions(payload: dict[str, object] | None) -> list[str]:
    if payload is None:
        return []
    actions = payload.get("next_actions")
    if not isinstance(actions, list):
        return []
    return [action for action in actions if isinstance(action, str)]


def preflight_has_next_actions(payload: dict[str, object] | None) -> bool:
    return payload is not None and "next_actions" in payload


def preflight_failed_checks(payload: dict[str, object] | None) -> list[str]:
    if payload is None:
        return []
    failed_checks = payload.get("failed_checks")
    if not isinstance(failed_checks, list):
        return []
    return [check for check in failed_checks if isinstance(check, str)]


def preflight_payload(
    stdout: str, output_path: Path | None
) -> dict[str, object] | None:
    payload = parse_json_object(stdout)
    if output_path is None or not output_path.exists():
        return payload
    try:
        file_payload = parse_json_object(output_path.read_text(encoding="utf-8"))
    except OSError:
        return payload
    if payload is None:
        return file_payload
    if file_payload is None:
        return payload
    merged_payload = dict(file_payload)
    merged_payload.update(payload)
    return merged_payload


def parse_json_object(stdout: str) -> dict[str, object] | None:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def run_alpha_release_gate(
    repo_root: Path,
    *,
    with_deps: bool = False,
    allow_dirty: bool = False,
    include_remote: bool = False,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    expected_origin_url: str | None = None,
    allow_existing_refs: bool = False,
    preflight_output: Path | None = None,
    runner: Runner = subprocess_runner,
) -> AlphaReleaseGateResult:
    remote_options_requested = (
        repository_url != DEFAULT_REPOSITORY_URL
        or expected_repository != DEFAULT_REPOSITORY_FULL_NAME
        or expected_origin_url is not None
        or allow_existing_refs
    )
    effective_include_remote = include_remote or remote_options_requested
    effective_expected_origin_url = (
        repository_url
        if effective_include_remote and expected_origin_url is None
        else expected_origin_url
    )
    commands = default_gate_commands(
        with_deps=with_deps,
        allow_dirty=allow_dirty,
        include_remote=effective_include_remote,
        repository_url=repository_url,
        expected_repository=expected_repository,
        expected_origin_url=effective_expected_origin_url,
        allow_existing_refs=allow_existing_refs,
        preflight_output=preflight_output,
    )
    checks: list[dict[str, object]] = []
    executed_commands: list[Sequence[str]] = []
    next_actions: list[str] = []
    has_preflight_next_actions = False
    preflight_failures: list[str] = []

    for gate_command in commands:
        executed_commands.append(gate_command.command)
        exit_code, stdout, stderr = runner(gate_command.command, repo_root)
        if gate_command.name == "local_preflight" and exit_code != 0:
            nested_preflight_payload = preflight_payload(stdout, preflight_output)
            has_preflight_next_actions = preflight_has_next_actions(
                nested_preflight_payload
            )
            next_actions.extend(preflight_next_actions(nested_preflight_payload))
            preflight_failures.extend(preflight_failed_checks(nested_preflight_payload))
        checks.append(
            {
                "name": gate_command.name,
                "label": gate_command.label,
                "status": "passed" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "stdout_tail": output_tail(stdout),
                "stderr_tail": output_tail(stderr),
            }
        )

    failed_checks = [
        str(check["name"]) for check in checks if check["status"] == "failed"
    ]
    passed_count = sum(1 for check in checks if check["status"] == "passed")
    failed_count = len(failed_checks)
    check_count = len(checks)
    exit_code = 1 if failed_checks else 0
    summary = "alpha release gate failed" if exit_code else "alpha release gate passed"
    payload: dict[str, object] = {
        "summary": summary,
        "exit_code": exit_code,
        "check_count": check_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "failed_checks": failed_checks,
        "with_deps": with_deps,
        "allow_dirty": allow_dirty,
        "include_remote": effective_include_remote,
        "repository_url": repository_url if effective_include_remote else None,
        "expected_repository": (
            expected_repository if effective_include_remote else None
        ),
        "expected_origin_url": effective_expected_origin_url
        if effective_include_remote
        else None,
        "allow_existing_refs": allow_existing_refs
        if effective_include_remote
        else False,
        "preflight_output": str(preflight_output)
        if preflight_output is not None
        else None,
        "checks": checks,
    }
    if preflight_failures:
        payload["preflight_failed_checks"] = preflight_failures
    if has_preflight_next_actions:
        payload["next_actions"] = next_actions
    return AlphaReleaseGateResult(
        summary=summary,
        exit_code=exit_code,
        commands=executed_commands,
        payload=payload,
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the deterministic local QA-Z alpha release gate."
    )
    parser.add_argument(
        "--with-deps",
        action="store_true",
        help=(
            "Also run the stronger artifact smoke with dependency resolution. "
            "This may contact the configured Python package index."
        ),
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help=(
            "Pass --allow-dirty to local preflight. Use only while developing the "
            "release gate itself; omit for publish evidence."
        ),
    )
    parser.add_argument(
        "--include-remote",
        action="store_true",
        help=(
            "Include GitHub metadata and git ls-remote preflight checks. "
            "Use after the public repository exists."
        ),
    )
    parser.add_argument(
        "--repository-url",
        default=DEFAULT_REPOSITORY_URL,
        help=f"Git repository URL for --include-remote. Defaults to {DEFAULT_REPOSITORY_URL}.",
    )
    parser.add_argument(
        "--expected-repository",
        default=DEFAULT_REPOSITORY_FULL_NAME,
        help=(
            "Expected GitHub owner/repository full name for --include-remote. "
            f"Defaults to {DEFAULT_REPOSITORY_FULL_NAME}."
        ),
    )
    parser.add_argument(
        "--expected-origin-url",
        default=None,
        help=(
            "Require local origin to match this URL during --include-remote preflight."
        ),
    )
    parser.add_argument(
        "--allow-existing-refs",
        action="store_true",
        help=(
            "With --include-remote, allow a reachable repository that already "
            "has refs while still rejecting an existing release tag."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable gate evidence as JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path where the JSON evidence payload should be written.",
    )
    parser.add_argument(
        "--preflight-output",
        type=Path,
        default=None,
        help=(
            "Optional path where the nested preflight JSON evidence should be "
            "written. Defaults to <output>.preflight.json when --output is set."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    preflight_output = args.preflight_output
    if preflight_output is None and args.output is not None:
        preflight_output = args.output.with_suffix(".preflight.json")
    result = run_alpha_release_gate(
        Path.cwd(),
        with_deps=args.with_deps,
        allow_dirty=args.allow_dirty,
        include_remote=args.include_remote,
        repository_url=args.repository_url,
        expected_repository=args.expected_repository,
        expected_origin_url=args.expected_origin_url,
        allow_existing_refs=args.allow_existing_refs,
        preflight_output=preflight_output,
    )
    payload_json = json.dumps(result.payload, indent=2)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload_json}\n", encoding="utf-8")

    if args.json:
        print(payload_json)
    else:
        checks = result.payload["checks"]
        assert isinstance(checks, list)
        for check in checks:
            assert isinstance(check, dict)
            print(f"[{str(check['status']).upper()}] {check['name']}: {check['label']}")
            if check["status"] != "passed":
                detail = check["stderr_tail"] or check["stdout_tail"]
                print(f"  {detail}")
        next_actions = result.payload.get("next_actions")
        if isinstance(next_actions, list) and next_actions:
            print("Next actions:")
            for action in next_actions:
                if isinstance(action, str):
                    print(f"- {action}")
        print(result.summary)

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
