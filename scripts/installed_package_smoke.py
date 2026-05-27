"""Installed-package runtime smoke matrix for QA-Z."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import venv
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from typing import Sequence


PASS = "PASS"
FAIL = "FAIL"


@dataclass(frozen=True)
class PackageArtifacts:
    wheel: Path
    sdist: Path


@dataclass(frozen=True)
class CommandSpec:
    id: str
    artifact_kind: str
    command: tuple[str, ...]
    display_command: tuple[str, ...]
    cwd: Path
    allowed_exit_codes: frozenset[int] = frozenset({0})
    pass_reason: str = "command passed"


@dataclass(frozen=True)
class CheckResult:
    id: str
    artifact_kind: str
    command: tuple[str, ...]
    status: str
    reason: str
    exit_code: int


@dataclass(frozen=True)
class InstalledPackageSmokeResult:
    artifacts: PackageArtifacts
    checks: tuple[CheckResult, ...]

    @property
    def registry_upload_executed(self) -> bool:
        return False

    @property
    def exit_code(self) -> int:
        return 1 if any(check.status == FAIL for check in self.checks) else 0

    @property
    def summary(self) -> str:
        if self.exit_code:
            return "installed package smoke failed"
        return "installed package smoke passed"


Runner = Callable[
    [Sequence[str], Path],
    tuple[int, str, str],
]
VenvFactory = Callable[[Path], None]


def subprocess_runner(
    command: Sequence[str],
    cwd: Path,
    *,
    check_id: str,
    allowed_exit_codes: set[int],
) -> tuple[int, str, str]:
    del check_id
    del allowed_exit_codes
    try:
        completed = subprocess.run(
            list(command),
            cwd=cwd,
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


def create_package_venv(path: Path) -> None:
    venv.EnvBuilder(with_pip=True, clear=True).create(path)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build QA-Z locally, install the wheel and sdist into fresh venvs, "
            "and run installed CLI smoke checks without publishing."
        )
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print machine-readable smoke evidence as JSON",
    )
    return parser.parse_args(argv)


def run_installed_package_smoke(
    repo_root: Path,
    *,
    artifacts: PackageArtifacts | None = None,
    runner=subprocess_runner,
    create_venv: VenvFactory = create_package_venv,
    work_root: Path,
) -> InstalledPackageSmokeResult:
    work_root.mkdir(parents=True, exist_ok=True)
    resolved_artifacts = artifacts or build_local_artifacts(
        repo_root,
        work_root=work_root,
        runner=runner,
    )
    checks: list[CheckResult] = []
    for artifact_kind, artifact_path in (
        ("wheel", resolved_artifacts.wheel),
        ("sdist", resolved_artifacts.sdist),
    ):
        checks.extend(
            run_artifact_smoke(
                repo_root,
                artifact_kind=artifact_kind,
                artifact_path=artifact_path,
                work_root=work_root,
                runner=runner,
                create_venv=create_venv,
            )
        )
    return InstalledPackageSmokeResult(
        artifacts=resolved_artifacts,
        checks=tuple(checks),
    )


def build_local_artifacts(
    repo_root: Path,
    *,
    work_root: Path,
    runner,
) -> PackageArtifacts:
    source_copy = work_root / "source"
    artifacts_dir = work_root / "artifacts"
    if source_copy.exists():
        shutil.rmtree(source_copy)
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    copy_source_tree(repo_root, source_copy)
    command = (
        sys.executable,
        "-m",
        "build",
        "--sdist",
        "--wheel",
        "--outdir",
        str(artifacts_dir),
    )
    exit_code, stdout, stderr = runner(
        command,
        source_copy,
        check_id="build_artifacts",
        allowed_exit_codes={0},
    )
    if exit_code != 0:
        raise RuntimeError(
            "artifact build failed: " + command_output(exit_code, stdout, stderr)
        )
    return PackageArtifacts(
        wheel=resolve_single_artifact(artifacts_dir, "*.whl", "wheel"),
        sdist=resolve_single_artifact(artifacts_dir, "*.tar.gz", "sdist"),
    )


def copy_source_tree(repo_root: Path, destination: Path) -> None:
    def ignore(_directory: str, names: list[str]) -> set[str]:
        ignored_names = {
            ".git",
            ".worktrees",
            ".qa-z",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "__pycache__",
            "build",
            "dist",
        }
        ignored = {name for name in names if name in ignored_names}
        ignored.update(name for name in names if name.endswith(".egg-info"))
        return ignored

    shutil.copytree(repo_root, destination, ignore=ignore)


def resolve_single_artifact(directory: Path, pattern: str, label: str) -> Path:
    matches = sorted(directory.glob(pattern), key=lambda path: path.name)
    if not matches:
        raise RuntimeError(f"no {label} artifact found in {directory}")
    if len(matches) > 1:
        names = ", ".join(path.name for path in matches)
        raise RuntimeError(f"multiple {label} artifacts found in {directory}: {names}")
    return matches[0]


def run_artifact_smoke(
    repo_root: Path,
    *,
    artifact_kind: str,
    artifact_path: Path,
    work_root: Path,
    runner,
    create_venv: VenvFactory,
) -> list[CheckResult]:
    smoke_root = work_root / artifact_kind
    venv_dir = smoke_root / "venv"
    demo_workspace = smoke_root / "workspace"
    create_venv(venv_dir)
    demo_workspace.mkdir(parents=True, exist_ok=True)
    venv_python = venv_python_path(venv_dir)
    qa_z = qa_z_executable_path(venv_dir)
    specs = artifact_command_specs(
        artifact_kind=artifact_kind,
        artifact_path=artifact_path,
        venv_python=venv_python,
        qa_z=qa_z,
        demo_workspace=demo_workspace,
    )
    return [run_check(repo_root, spec, runner) for spec in specs]


def artifact_command_specs(
    *,
    artifact_kind: str,
    artifact_path: Path,
    venv_python: Path,
    qa_z: Path,
    demo_workspace: Path,
) -> list[CommandSpec]:
    demo_root = demo_workspace / ".qa-z" / "demo" / "auth-bug"
    config_args = ("--path", str(demo_root), "--config", "qa-z.demo.yaml")
    python_label = "python.exe" if os.name == "nt" else "python"
    qa_z_label = "qa-z"
    apply_fix_command = (
        str(venv_python),
        "-c",
        (
            "from pathlib import Path; import shutil; "
            "shutil.copyfile(Path('app') / 'auth.fixed.py', "
            "Path('app') / 'auth.py')"
        ),
    )
    apply_fix_display = (
        python_label,
        "-c",
        (
            "from pathlib import Path; import shutil; "
            "shutil.copyfile(Path('app') / 'auth.fixed.py', "
            "Path('app') / 'auth.py')"
        ),
    )
    return [
        CommandSpec(
            id=f"{artifact_kind}_install",
            artifact_kind=artifact_kind,
            command=(
                str(venv_python),
                "-m",
                "pip",
                "install",
                str(artifact_path),
            ),
            display_command=(python_label, "-m", "pip", "install", str(artifact_path)),
            cwd=demo_workspace,
        ),
        CommandSpec(
            id=f"{artifact_kind}_cli_help",
            artifact_kind=artifact_kind,
            command=(str(qa_z), "--help"),
            display_command=(qa_z_label, "--help"),
            cwd=demo_workspace,
        ),
        CommandSpec(
            id=f"{artifact_kind}_module_help",
            artifact_kind=artifact_kind,
            command=(str(venv_python), "-m", "qa_z", "--help"),
            display_command=(python_label, "-m", "qa_z", "--help"),
            cwd=demo_workspace,
        ),
        CommandSpec(
            id=f"{artifact_kind}_demo_auth_bug",
            artifact_kind=artifact_kind,
            command=(
                str(qa_z),
                "demo",
                "auth-bug",
                "--json",
                "--path",
                str(demo_workspace),
            ),
            display_command=(
                qa_z_label,
                "demo",
                "auth-bug",
                "--json",
                "--path",
                str(demo_workspace),
            ),
            cwd=demo_workspace,
        ),
        CommandSpec(
            id=f"{artifact_kind}_doctor",
            artifact_kind=artifact_kind,
            command=(str(qa_z), "doctor", "--json", *config_args),
            display_command=(qa_z_label, "doctor", "--json", *config_args),
            cwd=demo_root,
        ),
        CommandSpec(
            id=f"{artifact_kind}_guard",
            artifact_kind=artifact_kind,
            command=(
                str(qa_z),
                "guard",
                "--from-run",
                "latest",
                "--adapter",
                "codex",
                *config_args,
            ),
            display_command=(
                qa_z_label,
                "guard",
                "--from-run",
                "latest",
                "--adapter",
                "codex",
                *config_args,
            ),
            cwd=demo_root,
        ),
        CommandSpec(
            id=f"{artifact_kind}_repair_prompt",
            artifact_kind=artifact_kind,
            command=(
                str(qa_z),
                "repair-prompt",
                "--from-run",
                "latest",
                "--adapter",
                "codex",
                *config_args,
            ),
            display_command=(
                qa_z_label,
                "repair-prompt",
                "--from-run",
                "latest",
                "--adapter",
                "codex",
                *config_args,
            ),
            cwd=demo_root,
        ),
        CommandSpec(
            id=f"{artifact_kind}_apply_auth_fix",
            artifact_kind=artifact_kind,
            command=apply_fix_command,
            display_command=apply_fix_display,
            cwd=demo_root,
        ),
        CommandSpec(
            id=f"{artifact_kind}_verify",
            artifact_kind=artifact_kind,
            command=(
                str(qa_z),
                "verify",
                "--from-run",
                "latest",
                "--json",
                *config_args,
            ),
            display_command=(
                qa_z_label,
                "verify",
                "--from-run",
                "latest",
                "--json",
                *config_args,
            ),
            cwd=demo_root,
            pass_reason="command reported improved repair verification",
        ),
    ]


def run_check(repo_root: Path, spec: CommandSpec, runner) -> CheckResult:
    exit_code, stdout, stderr = runner(
        spec.command,
        spec.cwd,
        check_id=spec.id,
        allowed_exit_codes=set(spec.allowed_exit_codes),
    )
    if exit_code in spec.allowed_exit_codes:
        reason = spec.pass_reason
        if exit_code:
            reason = f"{reason}: {command_output(exit_code, stdout, stderr)}"
        return CheckResult(
            id=spec.id,
            artifact_kind=spec.artifact_kind,
            command=relative_command(repo_root, spec.display_command),
            status=PASS,
            reason=reason,
            exit_code=exit_code,
        )
    return CheckResult(
        id=spec.id,
        artifact_kind=spec.artifact_kind,
        command=relative_command(repo_root, spec.display_command),
        status=FAIL,
        reason=command_output(exit_code, stdout, stderr),
        exit_code=exit_code,
    )


def venv_python_path(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def qa_z_executable_path(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "qa-z.exe"
    return venv_dir / "bin" / "qa-z"


def command_output(exit_code: int, stdout: str, stderr: str) -> str:
    output = (stderr or stdout).strip()
    if output:
        return f"exit {exit_code}: {output}"
    return f"exit {exit_code}"


def relative_command(repo_root: Path, command: Sequence[str]) -> tuple[str, ...]:
    return tuple(relative_path_argument(repo_root, part) for part in command)


def relative_path_argument(repo_root: Path, value: str) -> str:
    path = Path(value)
    if not path.is_absolute():
        return value
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def result_payload(
    repo_root: Path, result: InstalledPackageSmokeResult
) -> dict[str, object]:
    return {
        "summary": result.summary,
        "exit_code": result.exit_code,
        "registry_upload_executed": result.registry_upload_executed,
        "artifacts": {
            "wheel": relative_path_argument(repo_root, str(result.artifacts.wheel)),
            "sdist": relative_path_argument(repo_root, str(result.artifacts.sdist)),
        },
        "checks": [
            {
                "id": check.id,
                "artifact_kind": check.artifact_kind,
                "command": list(check.command),
                "status": check.status,
                "reason": check.reason,
                "exit_code": check.exit_code,
            }
            for check in result.checks
        ],
    }


def _print_human(payload: dict[str, object]) -> None:
    print(f"{payload['summary']} (exit_code={payload['exit_code']})")
    checks = payload.get("checks")
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, dict):
                continue
            command = check.get("command")
            rendered = " ".join(command) if isinstance(command, list) else ""
            print(
                f"[{check.get('status')}] {check.get('artifact_kind')}:"
                f"{check.get('id')} :: {rendered} :: {check.get('reason')}"
            )
    print(f"registry_upload_executed={payload['registry_upload_executed']}")


def error_payload(message: str) -> dict[str, object]:
    return {
        "summary": "installed package smoke failed",
        "exit_code": 1,
        "registry_upload_executed": False,
        "artifacts": {"wheel": None, "sdist": None},
        "checks": [
            {
                "id": "installed_package_smoke",
                "artifact_kind": "matrix",
                "command": [],
                "status": FAIL,
                "reason": message,
                "exit_code": 1,
            }
        ],
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = Path.cwd()
    try:
        with tempfile.TemporaryDirectory(prefix="qa-z-installed-smoke-") as tmp:
            result = run_installed_package_smoke(
                repo_root,
                work_root=Path(tmp),
            )
            payload = result_payload(repo_root, result)
    except Exception as exc:  # noqa: BLE001 - CLI evidence should be JSON on failure.
        payload = error_payload(str(exc))

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_human(payload)
    return int(payload["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
