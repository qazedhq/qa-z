"""Support helpers for safe QA-Z package smoke rehearsal."""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from typing import Sequence

from qa_z.subprocess_env import build_tool_subprocess_env


PASS = "PASS"
FAIL = "FAIL"
NOT_RUN = "NOT RUN"
BLOCKED = "BLOCKED"
STATUSES = (PASS, FAIL, NOT_RUN, BLOCKED)


class RehearsalError(ValueError):
    """Raised when the requested package rehearsal cannot be configured."""


@dataclass(frozen=True)
class CheckResult:
    id: str
    command: tuple[str, ...]
    status: str
    reason: str
    exit_code: int | None = None


class RehearsalResult:
    def __init__(
        self,
        *,
        wheel: Path,
        sdists: Sequence[Path],
        checks: Sequence[CheckResult],
        allow_missing_tools: bool,
    ) -> None:
        self.wheel = wheel
        self.sdists = list(sdists)
        self.checks = list(checks)
        self.allow_missing_tools = allow_missing_tools

    @property
    def registry_upload_executed(self) -> bool:
        return False

    @property
    def exit_code(self) -> int:
        if any(check.status == FAIL for check in self.checks):
            return 1
        if not self.allow_missing_tools and any(
            check.status in {NOT_RUN, BLOCKED} for check in self.checks
        ):
            return 1
        return 0

    @property
    def summary(self) -> str:
        if any(check.status == FAIL for check in self.checks):
            return "package smoke rehearsal failed"
        if any(check.status in {NOT_RUN, BLOCKED} for check in self.checks):
            return "package smoke rehearsal incomplete"
        return "package smoke rehearsal passed"


Runner = Callable[[Sequence[str], Path], tuple[int, str, str]]


@dataclass(frozen=True)
class ToolSpec:
    id: str
    availability_command: tuple[str, ...]
    smoke_command: tuple[str, ...]


def subprocess_runner(command: Sequence[str], cwd: Path) -> tuple[int, str, str]:
    try:
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
    except OSError as exc:
        return 127, "", str(exc)
    return completed.returncode, completed.stdout, completed.stderr


def _sorted_paths(paths: Sequence[Path]) -> list[Path]:
    return sorted(paths, key=lambda path: path.as_posix())


def resolve_single_artifact(
    repo_root: Path,
    *,
    explicit_path: str | None,
    pattern: str,
    label: str,
    required: bool,
) -> Path | None:
    if explicit_path:
        path = Path(explicit_path)
        artifact = path if path.is_absolute() else repo_root / path
        if not artifact.exists():
            raise RehearsalError(f"{label} artifact does not exist: {path}")
        return artifact

    matches = _sorted_paths(list((repo_root / "dist").glob(pattern)))
    if not matches:
        if required:
            raise RehearsalError(
                f"no {label} artifact found under dist/{pattern}; "
                f"build artifacts first or pass --{label}"
            )
        return None
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise RehearsalError(
            f"multiple {label} artifacts found under dist/{pattern}: {names}; "
            f"pass --{label} to select one"
        )
    return matches[0]


def resolve_artifacts(
    repo_root: Path,
    *,
    wheel: str | None,
    sdist: str | None,
) -> tuple[Path, list[Path]]:
    resolved_wheel = resolve_single_artifact(
        repo_root,
        explicit_path=wheel,
        pattern="*.whl",
        label="wheel",
        required=True,
    )
    if resolved_wheel is None:
        raise RehearsalError("wheel discovery did not return an artifact")

    resolved_sdist = resolve_single_artifact(
        repo_root,
        explicit_path=sdist,
        pattern="*.tar.gz",
        label="sdist",
        required=False,
    )
    return resolved_wheel, [resolved_sdist] if resolved_sdist is not None else []


def path_argument(repo_root: Path, path: Path) -> str:
    try:
        relative = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        return str(path)
    return relative.as_posix()


def package_tool_specs(
    repo_root: Path, wheel: Path, sdists: Sequence[Path]
) -> list[ToolSpec]:
    wheel_arg = path_argument(repo_root, wheel)
    sdist_args = tuple(path_argument(repo_root, sdist) for sdist in sdists)
    artifact_args = (wheel_arg, *sdist_args)
    return [
        ToolSpec(
            id="twine_check",
            availability_command=(sys.executable, "-m", "twine", "--version"),
            smoke_command=(sys.executable, "-m", "twine", "check", *artifact_args),
        ),
        ToolSpec(
            id="pipx_wheel_help",
            availability_command=("pipx", "--version"),
            smoke_command=("pipx", "run", "--spec", wheel_arg, "qa-z", "--help"),
        ),
        ToolSpec(
            id="uvx_wheel_help",
            availability_command=("uvx", "--version"),
            smoke_command=("uvx", "--from", wheel_arg, "qa-z", "--help"),
        ),
    ]


def _command_output(exit_code: int, stdout: str, stderr: str) -> str:
    output = (stderr or stdout).strip()
    if output:
        return f"exit {exit_code}: {output}"
    return f"exit {exit_code}"


def run_tool_spec(repo_root: Path, spec: ToolSpec, runner: Runner) -> CheckResult:
    probe_exit, probe_stdout, probe_stderr = runner(
        spec.availability_command, repo_root
    )
    if probe_exit:
        return CheckResult(
            id=spec.id,
            command=spec.smoke_command,
            status=NOT_RUN,
            reason=(
                "tool unavailable; availability probe "
                f"{_command_output(probe_exit, probe_stdout, probe_stderr)}"
            ),
            exit_code=probe_exit,
        )

    smoke_exit, smoke_stdout, smoke_stderr = runner(spec.smoke_command, repo_root)
    if smoke_exit:
        return CheckResult(
            id=spec.id,
            command=spec.smoke_command,
            status=FAIL,
            reason=_command_output(smoke_exit, smoke_stdout, smoke_stderr),
            exit_code=smoke_exit,
        )
    return CheckResult(
        id=spec.id,
        command=spec.smoke_command,
        status=PASS,
        reason="smoke command passed",
        exit_code=0,
    )


def run_package_smoke_rehearsal(
    repo_root: Path,
    *,
    wheel: str | None = None,
    sdist: str | None = None,
    allow_missing_tools: bool = False,
    runner: Runner = subprocess_runner,
) -> RehearsalResult:
    resolved_wheel, resolved_sdists = resolve_artifacts(
        repo_root,
        wheel=wheel,
        sdist=sdist,
    )
    checks = [
        run_tool_spec(repo_root, spec, runner)
        for spec in package_tool_specs(repo_root, resolved_wheel, resolved_sdists)
    ]
    return RehearsalResult(
        wheel=resolved_wheel,
        sdists=resolved_sdists,
        checks=checks,
        allow_missing_tools=allow_missing_tools,
    )


def result_payload(repo_root: Path, result: RehearsalResult) -> dict[str, object]:
    return {
        "summary": result.summary,
        "exit_code": result.exit_code,
        "wheel": path_argument(repo_root, result.wheel),
        "sdist_paths": [path_argument(repo_root, sdist) for sdist in result.sdists],
        "checks": [
            {
                "id": check.id,
                "command": list(check.command),
                "status": check.status,
                "reason": check.reason,
                "exit_code": check.exit_code,
            }
            for check in result.checks
        ],
        "registry_upload_executed": result.registry_upload_executed,
    }


def error_payload(message: str) -> dict[str, object]:
    return {
        "summary": "package smoke rehearsal failed",
        "exit_code": 1,
        "wheel": None,
        "sdist_paths": [],
        "checks": [
            {
                "id": "artifact_discovery",
                "command": [],
                "status": FAIL,
                "reason": message,
                "exit_code": 1,
            }
        ],
        "registry_upload_executed": False,
    }
