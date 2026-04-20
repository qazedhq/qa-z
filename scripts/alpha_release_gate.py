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
) -> list[GateCommand]:
    preflight_args = [
        "scripts/alpha_release_preflight.py",
        "--skip-remote",
    ]
    preflight_label_parts = [
        "python",
        "scripts/alpha_release_preflight.py",
        "--skip-remote",
    ]
    if allow_dirty:
        preflight_args.append("--allow-dirty")
        preflight_label_parts.append("--allow-dirty")
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


def run_alpha_release_gate(
    repo_root: Path,
    *,
    with_deps: bool = False,
    allow_dirty: bool = False,
    runner: Runner = subprocess_runner,
) -> AlphaReleaseGateResult:
    commands = default_gate_commands(with_deps=with_deps, allow_dirty=allow_dirty)
    checks: list[dict[str, object]] = []
    executed_commands: list[Sequence[str]] = []

    for gate_command in commands:
        executed_commands.append(gate_command.command)
        exit_code, stdout, stderr = runner(gate_command.command, repo_root)
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

    exit_code = 1 if any(check["status"] == "failed" for check in checks) else 0
    summary = "alpha release gate failed" if exit_code else "alpha release gate passed"
    payload: dict[str, object] = {
        "summary": summary,
        "exit_code": exit_code,
        "with_deps": with_deps,
        "allow_dirty": allow_dirty,
        "checks": checks,
    }
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
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = run_alpha_release_gate(
        Path.cwd(),
        with_deps=args.with_deps,
        allow_dirty=args.allow_dirty,
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
        print(result.summary)

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
