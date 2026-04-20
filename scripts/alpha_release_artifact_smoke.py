"""Install-smoke checks for QA-Z alpha release artifacts."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable
from typing import NamedTuple
from typing import Sequence


DEFAULT_VERSION = "0.9.8a0"
DEFAULT_WHEEL = Path("dist/qa_z-0.9.8a0-py3-none-any.whl")
DEFAULT_SDIST = Path("dist/qa_z-0.9.8a0.tar.gz")


class CheckResult(NamedTuple):
    name: str
    status: str
    detail: str


class SmokeResult:
    def __init__(self, checks: Sequence[CheckResult]) -> None:
        self.checks = list(checks)

    @property
    def exit_code(self) -> int:
        return 1 if any(check.status == "failed" for check in self.checks) else 0

    @property
    def summary(self) -> str:
        if self.exit_code:
            return "artifact smoke failed"
        return "artifact smoke passed"


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


def result_payload(result: SmokeResult) -> dict[str, object]:
    return {
        "summary": result.summary,
        "exit_code": result.exit_code,
        "checks": [
            {"name": check.name, "status": check.status, "detail": check.detail}
            for check in result.checks
        ],
    }


def artifact_label(path: Path) -> str:
    name = path.name
    if name.endswith(".whl"):
        return "wheel"
    if name.endswith(".tar.gz"):
        return "sdist"
    return path.stem.replace("-", "_")


def venv_python_path(venv_dir: Path) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def venv_script_path(venv_dir: Path, script_name: str) -> Path:
    if os.name == "nt":
        return venv_dir / "Scripts" / f"{script_name}.exe"
    return venv_dir / "bin" / script_name


def validation_code(expected_version: str) -> str:
    return "\n".join(
        [
            "import importlib.metadata as metadata",
            "import qa_z",
            f"expected = {expected_version!r}",
            "assert metadata.version('qa-z') == expected, metadata.version('qa-z')",
            "assert qa_z.__version__ == expected, qa_z.__version__",
            "entry_points = metadata.entry_points(group='console_scripts')",
            "assert any(",
            "    entry.name == 'qa-z' and entry.value == 'qa_z.cli:main'",
            "    for entry in entry_points",
            "), 'missing qa-z console script entry point'",
            "print(f'qa-z {expected} artifact smoke ok')",
        ]
    )


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


def smoke_artifact(
    repo_root: Path,
    artifact: Path,
    *,
    expected_version: str,
    with_deps: bool,
    runner: Runner,
) -> CheckResult:
    label = artifact_label(artifact)
    check_name = f"{label}_install_smoke"
    artifact_path = artifact if artifact.is_absolute() else repo_root / artifact
    if not artifact_path.exists():
        return CheckResult(check_name, "failed", f"missing artifact: {artifact}")

    with tempfile.TemporaryDirectory(prefix=f"qa-z-{label}-smoke-") as tempdir:
        temp_path = Path(tempdir)
        venv_dir = temp_path / "venv"
        exit_code, stdout, stderr = runner(
            (sys.executable, "-m", "venv", str(venv_dir)),
            repo_root,
        )
        if exit_code:
            return CheckResult(
                check_name,
                "failed",
                command_detail("venv creation", exit_code, stdout, stderr),
            )

        venv_python = venv_python_path(venv_dir)
        pip_install = [str(venv_python), "-m", "pip", "install"]
        if not with_deps:
            pip_install.append("--no-deps")
        pip_install.append(str(artifact_path))
        exit_code, stdout, stderr = runner(tuple(pip_install), repo_root)
        if exit_code:
            return CheckResult(
                check_name,
                "failed",
                command_detail("artifact install", exit_code, stdout, stderr),
            )

        exit_code, stdout, stderr = runner(
            (str(venv_python), "-c", validation_code(expected_version)),
            repo_root,
        )
        if exit_code:
            return CheckResult(
                check_name,
                "failed",
                command_detail("metadata validation", exit_code, stdout, stderr),
            )

        if with_deps:
            exit_code, stdout, stderr = runner(
                (str(venv_python), "-m", "qa_z", "--help"),
                repo_root,
            )
            if exit_code:
                return CheckResult(
                    check_name,
                    "failed",
                    command_detail("python -m qa_z help", exit_code, stdout, stderr),
                )

            exit_code, stdout, stderr = runner(
                (str(venv_script_path(venv_dir, "qa-z")), "--help"),
                repo_root,
            )
            if exit_code:
                return CheckResult(
                    check_name,
                    "failed",
                    command_detail("qa-z console help", exit_code, stdout, stderr),
                )

            init_target = temp_path / "init-target"
            exit_code, stdout, stderr = runner(
                (str(venv_python), "-m", "qa_z", "init", "--path", str(init_target)),
                repo_root,
            )
            if exit_code:
                return CheckResult(
                    check_name,
                    "failed",
                    command_detail("qa-z init smoke", exit_code, stdout, stderr),
                )
            expected_files = (
                init_target / "qa-z.yaml",
                init_target / "qa" / "contracts" / "README.md",
            )
            missing = [str(path) for path in expected_files if not path.exists()]
            if missing:
                return CheckResult(
                    check_name,
                    "failed",
                    f"qa-z init smoke missing files: {', '.join(missing)}",
                )

    mode = (
        "with dependency resolution" if with_deps else "without dependency resolution"
    )
    return CheckResult(check_name, "passed", f"{artifact} installed {mode}")


def run_artifact_smoke(
    repo_root: Path,
    *,
    artifacts: Sequence[Path],
    expected_version: str = DEFAULT_VERSION,
    with_deps: bool = False,
    runner: Runner = subprocess_runner,
) -> SmokeResult:
    checks = [
        smoke_artifact(
            repo_root,
            artifact,
            expected_version=expected_version,
            with_deps=with_deps,
            runner=runner,
        )
        for artifact in artifacts
    ]
    return SmokeResult(checks)


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
