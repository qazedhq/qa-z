"""Support helpers for no-upload package smoke rehearsals."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable
from typing import NamedTuple
from typing import Sequence

from qa_z.subprocess_env import build_tool_subprocess_env


DEFAULT_WHEEL = Path("dist/qa_z-0.9.8a0-py3-none-any.whl")
DEFAULT_SDIST = Path("dist/qa_z-0.9.8a0.tar.gz")
CREDENTIAL_ENV_VARS = (
    "TWINE_USERNAME",
    "TWINE_PASSWORD",
    "TWINE_API_TOKEN",
    "UV_PUBLISH_TOKEN",
)
BLOCKED_COMMANDS = (
    "python -m twine upload --repository testpypi dist/*",
    "python -m twine upload dist/*",
    "uv publish",
    "npm publish",
    "git tag ...",
    "gh release create ...",
    "deploy commands",
)


class RehearsalCheck(NamedTuple):
    name: str
    status: str
    detail: str


class RehearsalResult:
    def __init__(self, checks: Sequence[RehearsalCheck]) -> None:
        self.checks = list(checks)

    @property
    def exit_code(self) -> int:
        return 1 if any(check.status == "FAIL" for check in self.checks) else 0

    @property
    def overall_status(self) -> str:
        if any(check.status == "FAIL" for check in self.checks):
            return "FAIL"
        if any(check.status == "NOT_RUN" for check in self.checks):
            return "PARTIAL"
        return "PASS"

    @property
    def summary(self) -> str:
        if self.overall_status == "FAIL":
            return "package smoke rehearsal failed"
        if self.overall_status == "PARTIAL":
            return "package smoke rehearsal partial"
        return "package smoke rehearsal passed"


Runner = Callable[[Sequence[str], Path], tuple[int, str, str]]


def rehearsal_subprocess_env() -> dict[str, str]:
    env = build_tool_subprocess_env()
    for name in CREDENTIAL_ENV_VARS:
        env.pop(name, None)
    return env


def subprocess_runner(command: Sequence[str], cwd: Path) -> tuple[int, str, str]:
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
            env=rehearsal_subprocess_env(),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError as exc:
        command_name = str(command[0]) if command else "command"
        return 127, "", f"{command_name} executable not found: {exc}"
    return completed.returncode, completed.stdout, completed.stderr


def result_payload(result: RehearsalResult) -> dict[str, object]:
    return {
        "summary": result.summary,
        "overall_status": result.overall_status,
        "exit_code": result.exit_code,
        "registry_upload_executed": False,
        "credential_inputs_loaded": False,
        "blocked_commands": list(BLOCKED_COMMANDS),
        "checks": [
            {"name": check.name, "status": check.status, "detail": check.detail}
            for check in result.checks
        ],
    }


def command_detail(
    step: str,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> str:
    output = (stderr or stdout).strip()
    if output:
        return f"{step} failed with exit {exit_code}: {output}"
    return f"{step} failed with exit {exit_code}"


def missing_artifact_detail(repo_root: Path, paths: Sequence[Path]) -> str:
    missing = [
        str(path)
        for path in paths
        if not (path if path.is_absolute() else repo_root / path).exists()
    ]
    return f"missing artifact(s): {', '.join(missing)}"


def run_tool_check(
    name: str,
    *,
    availability_command: Sequence[str],
    smoke_command: Sequence[str],
    required_artifacts: Sequence[Path],
    repo_root: Path,
    allow_missing_tools: bool,
    runner: Runner,
) -> RehearsalCheck:
    exit_code, stdout, stderr = runner(availability_command, repo_root)
    if exit_code:
        status = "NOT_RUN" if allow_missing_tools else "FAIL"
        return RehearsalCheck(
            name,
            status,
            command_detail(
                "tool availability check",
                exit_code,
                stdout,
                stderr,
            ),
        )

    artifact_detail = missing_artifact_detail(repo_root, required_artifacts)
    if not artifact_detail.endswith(": "):
        return RehearsalCheck(name, "FAIL", artifact_detail)

    exit_code, stdout, stderr = runner(smoke_command, repo_root)
    if exit_code:
        return RehearsalCheck(
            name,
            "FAIL",
            command_detail("package smoke command", exit_code, stdout, stderr),
        )

    return RehearsalCheck(name, "PASS", "package smoke command passed")


def run_package_smoke_rehearsal(
    repo_root: Path,
    *,
    wheel: Path = DEFAULT_WHEEL,
    sdist: Path = DEFAULT_SDIST,
    allow_missing_tools: bool = False,
    runner: Runner = subprocess_runner,
) -> RehearsalResult:
    checks = [
        run_tool_check(
            "twine_check",
            availability_command=(sys.executable, "-m", "twine", "--version"),
            smoke_command=(
                sys.executable,
                "-m",
                "twine",
                "check",
                str(wheel),
                str(sdist),
            ),
            required_artifacts=(wheel, sdist),
            repo_root=repo_root,
            allow_missing_tools=allow_missing_tools,
            runner=runner,
        ),
        run_tool_check(
            "pipx_help_smoke",
            availability_command=("pipx", "--version"),
            smoke_command=("pipx", "run", "--spec", str(wheel), "qa-z", "--help"),
            required_artifacts=(wheel,),
            repo_root=repo_root,
            allow_missing_tools=allow_missing_tools,
            runner=runner,
        ),
        run_tool_check(
            "uvx_help_smoke",
            availability_command=("uvx", "--version"),
            smoke_command=("uvx", "--from", str(wheel), "qa-z", "--help"),
            required_artifacts=(wheel,),
            repo_root=repo_root,
            allow_missing_tools=allow_missing_tools,
            runner=runner,
        ),
    ]
    return RehearsalResult(checks)
