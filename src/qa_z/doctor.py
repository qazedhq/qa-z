"""Environment diagnostics for qa-z doctor."""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from importlib import metadata
from importlib.resources import (
    files,
)  # nosemgrep: python.lang.compatibility.python37.python37-compatibility-importlib2
from pathlib import Path
from typing import Any, Literal

import qa_z
from qa_z.config import ConfigError, load_config
from qa_z.config_validation import validate_config

DoctorStatus = Literal["passed", "warning", "failed"]

STATUS_PREFIX: dict[str, str] = {
    "passed": "PASS",
    "warning": "WARN",
    "failed": "FAIL",
}

CHECK_LABELS: dict[str, str] = {
    "package.version": "package version",
    "runtime.python": "python",
    "runtime.platform": "platform",
    "runtime.invocation": "invocation",
    "install.mode": "install mode",
    "project.root": "project root",
    "project.git_repo": "git repo",
    "config.qa_z_yaml": "qa-z.yaml",
    "config.profile": "profile",
    "tool.git": "git",
    "tool.semgrep": "semgrep",
    "resources.auth_bug_template": "templates",
    "runtime.artifacts": ".qa-z",
    "environment.github_actions": "GitHub Actions",
}

AUTH_BUG_TEMPLATE = "templates/examples/agent-auth-bug/repo/qa-z.yaml"
find_executable = shutil.which


@dataclass(frozen=True)
class DoctorCheck:
    """One stable doctor diagnostic check."""

    id: str
    status: DoctorStatus
    message: str
    evidence: dict[str, Any]
    suggestion: str | None = None

    def to_json(self) -> dict[str, Any]:
        """Return the stable JSON representation for this check."""
        return {
            "id": self.id,
            "status": self.status,
            "message": self.message,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
        }


def build_doctor_report(root: Path, config_path: Path | None = None) -> dict[str, Any]:
    """Build the stable doctor report for a project root."""
    root = root.expanduser().resolve()
    target_config = (config_path or root / "qa-z.yaml").expanduser().resolve()
    config_exists = target_config.exists()

    config: dict[str, Any] | None = None
    errors: list[dict[str, str]] = []
    warnings: list[dict[str, str]] = []
    suggestions: list[str] = []

    try:
        config = load_config(root, config_path=target_config)
        config_report = validate_config(root, config)
        errors.extend(config_report["errors"])
        warnings.extend(config_report["warnings"])
        suggestions.extend(config_report["suggestions"])
    except ConfigError as exc:
        errors.append(
            {
                "code": "config_error",
                "path": str(target_config),
                "message": str(exc),
            }
        )

    checks = build_checks(
        root=root,
        config_path=target_config,
        config_exists=config_exists,
        config=config,
        config_load_failed=any(error["code"] == "config_error" for error in errors),
    )
    warnings.extend(
        issue_from_check(check, root) for check in checks if check.status == "warning"
    )
    errors.extend(
        issue_from_check(check, root) for check in checks if check.status == "failed"
    )

    for check in checks:
        if check.suggestion:
            suggestions.append(suggestion_command(check.suggestion))

    suggestions = unique_strings(suggestions)
    next_actions = next_actions_from_checks(checks, suggestions)

    status = status_from_parts(errors=errors, warnings=warnings, checks=checks)
    return {
        "status": status,
        "version": qa_z.__version__,
        "checks": [check.to_json() for check in checks],
        "warnings": warnings,
        "errors": errors,
        "suggestions": suggestions,
        "next_actions": next_actions,
    }


def build_checks(
    *,
    root: Path,
    config_path: Path,
    config_exists: bool,
    config: dict[str, Any] | None,
    config_load_failed: bool,
) -> list[DoctorCheck]:
    """Build deterministic doctor checks."""
    git_path = find_executable("git")
    return [
        package_version_check(),
        python_check(),
        platform_check(),
        invocation_check(root),
        install_mode_check(root),
        project_root_check(root),
        git_tool_check(git_path),
        git_repo_check(root, git_path),
        config_file_check(config_path, config_exists, config_load_failed),
        profile_check(config),
        semgrep_check(),
        auth_bug_template_check(),
        runtime_artifact_check(root),
        github_actions_check(),
    ]


def package_version_check() -> DoctorCheck:
    """Report package version and module location."""
    module_path = Path(qa_z.__file__).resolve()
    evidence: dict[str, Any] = {
        "version": qa_z.__version__,
        "module_path": str(module_path),
    }
    try:
        distribution = metadata.distribution("qa-z")
    except metadata.PackageNotFoundError:
        evidence["metadata_version"] = None
        evidence["distribution_location"] = None
    else:
        evidence["metadata_version"] = distribution.version
        evidence["distribution_location"] = str(distribution.locate_file(""))
    return DoctorCheck(
        id="package.version",
        status="passed",
        message=qa_z.__version__,
        evidence=evidence,
    )


def python_check() -> DoctorCheck:
    """Report the active Python runtime."""
    version = platform.python_version()
    return DoctorCheck(
        id="runtime.python",
        status="passed",
        message=version,
        evidence={
            "version": version,
            "executable": sys.executable,
            "prefix": sys.prefix,
            "base_prefix": sys.base_prefix,
        },
    )


def platform_check() -> DoctorCheck:
    """Report host platform details."""
    return DoctorCheck(
        id="runtime.platform",
        status="passed",
        message=platform.platform(),
        evidence={
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "platform": platform.platform(),
        },
    )


def invocation_check(root: Path) -> DoctorCheck:
    """Report how doctor was invoked."""
    return DoctorCheck(
        id="runtime.invocation",
        status="passed",
        message=sys.executable,
        evidence={
            "executable": sys.executable,
            "argv0": sys.argv[0] if sys.argv else "",
            "cwd": str(Path.cwd()),
            "doctor_root": str(root),
        },
    )


def install_mode_check(root: Path) -> DoctorCheck:
    """Detect source, editable, installed, venv, pipx, and Actions hints."""
    modes: list[str] = []
    evidence: dict[str, Any] = {
        "modes": modes,
        "module_path": str(Path(qa_z.__file__).resolve()),
        "sys_prefix": sys.prefix,
        "sys_base_prefix": sys.base_prefix,
    }

    if source_checkout_detected(root):
        modes.append("source checkout")
    if editable_install_detected():
        modes.append("editable")
    if venv_detected():
        modes.append("venv")
    if pipx_like_detected():
        modes.append("pipx-like")
    if github_actions_detected():
        modes.append("GitHub Actions")
    if installed_distribution_detected() and not any(
        mode in modes for mode in ("editable", "source checkout")
    ):
        modes.append("wheel/sdist install")
    if not modes:
        modes.append("unknown")

    return DoctorCheck(
        id="install.mode",
        status="passed",
        message=", ".join(modes),
        evidence=evidence,
    )


def source_checkout_detected(root: Path) -> bool:
    """Return whether the imported module appears to come from this checkout."""
    module_path = Path(qa_z.__file__).resolve()
    source_dir = (root / "src" / "qa_z").resolve()
    return (root / "pyproject.toml").is_file() and path_is_relative_to(
        module_path, source_dir
    )


def editable_install_detected() -> bool:
    """Return whether package metadata has a PEP 610 editable hint."""
    direct_url = distribution_text("direct_url.json")
    if not direct_url:
        return False
    try:
        payload = json.loads(direct_url)
    except json.JSONDecodeError:
        return False
    dir_info = payload.get("dir_info")
    return isinstance(dir_info, dict) and dir_info.get("editable") is True


def venv_detected() -> bool:
    """Return whether Python appears to run inside a virtual environment."""
    return sys.prefix != sys.base_prefix


def pipx_like_detected() -> bool:
    """Return whether environment paths look like pipx-managed execution."""
    values = [
        sys.prefix,
        sys.executable,
        os.environ.get("PIPX_HOME", ""),
        os.environ.get("PIPX_BIN_DIR", ""),
    ]
    return any("pipx" in value.lower() for value in values)


def github_actions_detected() -> bool:
    """Return whether this process is running in GitHub Actions."""
    return os.environ.get("GITHUB_ACTIONS", "").lower() == "true"


def installed_distribution_detected() -> bool:
    """Return whether importlib metadata can find the qa-z distribution."""
    try:
        metadata.distribution("qa-z")
    except metadata.PackageNotFoundError:
        return False
    return True


def distribution_text(name: str) -> str | None:
    """Read text from qa-z distribution metadata when available."""
    try:
        distribution = metadata.distribution("qa-z")
    except metadata.PackageNotFoundError:
        return None
    return distribution.read_text(name)


def project_root_check(root: Path) -> DoctorCheck:
    """Report the target project root."""
    if root.exists() and root.is_dir():
        return DoctorCheck(
            id="project.root",
            status="passed",
            message=str(root),
            evidence={"path": str(root), "exists": True},
        )
    return DoctorCheck(
        id="project.root",
        status="failed",
        message=f"project root not found: {root}",
        evidence={"path": str(root), "exists": False},
        suggestion="Check the `--path` value.",
    )


def git_tool_check(git_path: str | None) -> DoctorCheck:
    """Report git executable availability."""
    if git_path:
        return DoctorCheck(
            id="tool.git",
            status="passed",
            message=f"found at {git_path}",
            evidence={"path": git_path},
        )
    return DoctorCheck(
        id="tool.git",
        status="warning",
        message="not found; git repo checks are limited",
        evidence={"path": None},
        suggestion="Install git or add it to PATH.",
    )


def git_repo_check(root: Path, git_path: str | None) -> DoctorCheck:
    """Report whether the target root is inside a git repository."""
    if not git_path:
        return DoctorCheck(
            id="project.git_repo",
            status="warning",
            message="not checked because git is unavailable",
            evidence={"is_git_repo": None},
            suggestion="Install git or add it to PATH.",
        )
    try:
        completed = subprocess.run(
            [git_path, "-C", str(root), "rev-parse", "--show-toplevel"],
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return DoctorCheck(
            id="project.git_repo",
            status="warning",
            message=f"git repo check failed: {exc}",
            evidence={"is_git_repo": None, "error": str(exc)},
        )
    if completed.returncode == 0:
        top_level = completed.stdout.strip()
        return DoctorCheck(
            id="project.git_repo",
            status="passed",
            message=f"repo root {top_level}",
            evidence={"is_git_repo": True, "top_level": top_level},
        )
    return DoctorCheck(
        id="project.git_repo",
        status="passed",
        message="not inside a git repository",
        evidence={
            "is_git_repo": False,
            "stderr": completed.stderr.strip(),
        },
    )


def config_file_check(
    config_path: Path,
    config_exists: bool,
    config_load_failed: bool,
) -> DoctorCheck:
    """Report qa-z.yaml loading status."""
    if config_load_failed:
        return DoctorCheck(
            id="config.qa_z_yaml",
            status="failed",
            message="invalid",
            evidence={"path": str(config_path), "exists": config_exists},
            suggestion="Fix `qa-z.yaml` and rerun `qa-z doctor`.",
        )
    if config_exists:
        return DoctorCheck(
            id="config.qa_z_yaml",
            status="passed",
            message=str(config_path),
            evidence={"path": str(config_path), "exists": True},
        )
    return DoctorCheck(
        id="config.qa_z_yaml",
        status="warning",
        message="missing",
        evidence={"path": str(config_path), "exists": False},
        suggestion="Run `qa-z init`.",
    )


def profile_check(config: dict[str, Any] | None) -> DoctorCheck:
    """Report the configured QA-Z profile shape."""
    if config is None:
        return DoctorCheck(
            id="config.profile",
            status="warning",
            message="not evaluated",
            evidence={"profile": None},
        )
    project = config.get("project")
    languages = (
        string_list(project.get("languages")) if isinstance(project, dict) else []
    )
    profile = profile_from_languages(languages)
    return DoctorCheck(
        id="config.profile",
        status="passed",
        message=profile,
        evidence={
            "profile": profile,
            "languages": languages,
            "fast_check_count": check_count(config, "fast"),
            "deep_check_count": check_count(config, "deep"),
        },
    )


def semgrep_check() -> DoctorCheck:
    """Report Semgrep availability for deep checks."""
    semgrep_path = find_executable("semgrep")
    if semgrep_path:
        return DoctorCheck(
            id="tool.semgrep",
            status="passed",
            message=f"found at {semgrep_path}",
            evidence={"path": semgrep_path},
        )
    return DoctorCheck(
        id="tool.semgrep",
        status="warning",
        message="not found; deep checks may be limited",
        evidence={"path": None},
        suggestion="Install Semgrep if you want deep checks.",
    )


def auth_bug_template_check() -> DoctorCheck:
    """Report packaged auth-bug demo resource availability."""
    try:
        contents = files("qa_z").joinpath(AUTH_BUG_TEMPLATE).read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError, OSError) as exc:
        return DoctorCheck(
            id="resources.auth_bug_template",
            status="failed",
            message="auth-bug demo resources missing",
            evidence={"resource": AUTH_BUG_TEMPLATE, "error": str(exc)},
            suggestion="Reinstall QA-Z from the source checkout or package artifact.",
        )
    return DoctorCheck(
        id="resources.auth_bug_template",
        status="passed",
        message="auth-bug demo resources found",
        evidence={"resource": AUTH_BUG_TEMPLATE, "bytes": len(contents.encode())},
    )


def runtime_artifact_check(root: Path) -> DoctorCheck:
    """Report whether the local .qa-z runtime directory is writable."""
    runtime_dir = root / ".qa-z"
    marker = runtime_dir / f".doctor-write-test-{os.getpid()}-{uuid.uuid4().hex}"
    created_dir = not runtime_dir.exists()
    try:
        runtime_dir.mkdir(parents=True, exist_ok=True)
        marker.write_text("qa-z doctor\n", encoding="utf-8")
        marker.unlink()
        if created_dir:
            try:
                runtime_dir.rmdir()
            except OSError:
                pass
    except OSError as exc:
        return DoctorCheck(
            id="runtime.artifacts",
            status="failed",
            message=f"cannot write {runtime_dir}: {exc}",
            evidence={"runtime_dir": str(runtime_dir), "writable": False},
            suggestion="Fix directory permissions or run from a writable project path.",
        )
    return DoctorCheck(
        id="runtime.artifacts",
        status="passed",
        message=f"writable at {runtime_dir}",
        evidence={"runtime_dir": str(runtime_dir), "writable": True},
    )


def github_actions_check() -> DoctorCheck:
    """Report GitHub Actions environment hints."""
    in_actions = github_actions_detected()
    step_summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if in_actions:
        summary_phrase = "step summary available" if step_summary else "no step summary"
        return DoctorCheck(
            id="environment.github_actions",
            status="passed",
            message=(
                f"GitHub Actions detected; {summary_phrase}; SARIF/comment "
                "permissions are action-level opt-ins"
            ),
            evidence={
                "github_actions": True,
                "step_summary": step_summary,
                "step_summary_present": bool(step_summary),
            },
        )
    return DoctorCheck(
        id="environment.github_actions",
        status="passed",
        message="not running in GitHub Actions",
        evidence={
            "github_actions": False,
            "step_summary": step_summary,
            "step_summary_present": bool(step_summary),
        },
    )


def render_doctor_human(report: dict[str, Any]) -> str:
    """Render concise human doctor output."""
    lines = [f"QA-Z Doctor: {report['status']}", f"qa-z doctor: {report['status']}", ""]
    for check in report["checks"]:
        prefix = STATUS_PREFIX[str(check["status"])]
        label = CHECK_LABELS.get(str(check["id"]), str(check["id"]))
        lines.append(f"{prefix} {label}: {check['message']}")
    for item in report["errors"]:
        lines.append(f"error {item['code']} at {item['path']}: {item['message']}")
    for item in report["warnings"]:
        lines.append(f"warning {item['code']} at {item['path']}: {item['message']}")
    if report["next_actions"]:
        lines.extend(["", "Next actions:"])
        for index, action in enumerate(report["next_actions"], start=1):
            lines.append(f"{index}. {action}")
    return "\n".join(lines)


def issue_from_check(check: DoctorCheck, root: Path) -> dict[str, str]:
    """Convert warning/failed checks to the legacy issue shape."""
    return {
        "code": check.id.replace(".", "_"),
        "path": issue_path(check, root),
        "message": check.message,
    }


def issue_path(check: DoctorCheck, root: Path) -> str:
    """Return the most useful path for a doctor issue."""
    for key in ("path", "runtime_dir", "module_path"):
        value = check.evidence.get(key)
        if isinstance(value, str) and value:
            return value
    return str(root)


def status_from_parts(
    *,
    errors: list[dict[str, str]],
    warnings: list[dict[str, str]],
    checks: list[DoctorCheck],
) -> DoctorStatus:
    """Compute the overall doctor status."""
    if errors or any(check.status == "failed" for check in checks):
        return "failed"
    if warnings or any(check.status == "warning" for check in checks):
        return "warning"
    return "passed"


def suggestion_command(suggestion: str) -> str:
    """Return the suggestion list item while preserving legacy command entries."""
    if suggestion == "Run `qa-z init`.":
        return "qa-z init"
    return suggestion


def next_actions_from_checks(
    checks: list[DoctorCheck],
    suggestions: list[str],
) -> list[str]:
    """Build ordered, actionable next steps."""
    actions: list[str] = []
    for check in checks:
        if check.suggestion:
            actions.append(check.suggestion)
            if check.id == "config.qa_z_yaml":
                actions.append("Run `qa-z demo auth-bug`.")
    for suggestion in suggestions:
        if suggestion == "qa-z init":
            actions.append("Run `qa-z init`.")
        elif suggestion.startswith("qa-z "):
            actions.append(f"Run `{suggestion}`.")
        else:
            actions.append(suggestion)
    return unique_strings(actions)


def unique_strings(values: list[str]) -> list[str]:
    """Return values in first-seen order without duplicates."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def string_list(value: Any) -> list[str]:
    """Return a string-only list from config data."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def profile_from_languages(languages: list[str]) -> str:
    """Infer the starter profile from configured languages."""
    language_set = set(languages)
    if language_set == {"python"}:
        return "python"
    if language_set == {"typescript"}:
        return "typescript"
    if {"python", "typescript"}.issubset(language_set):
        return "monorepo"
    if languages:
        return "custom"
    return "default"


def check_count(config: dict[str, Any], section: str) -> int:
    """Count configured checks for a section."""
    section_value = config.get(section)
    if not isinstance(section_value, dict):
        return 0
    checks = section_value.get("checks")
    if not isinstance(checks, list):
        return 0
    return len(checks)


def path_is_relative_to(path: Path, parent: Path) -> bool:
    """Backport-friendly Path.is_relative_to helper."""
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
