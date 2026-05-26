"""Read-only QA-Z repository readiness scorecard."""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any, Literal

from qa_z.artifacts import format_path
from qa_z.config import ConfigError, load_config
from qa_z.config_validation import validate_config
from qa_z.evidence_summary import build_evidence_summary

SCORECARD_KIND = "qa_z.scorecard"
SCORECARD_SCHEMA_VERSION = 1

ScorecardStatus = Literal[
    "ready",
    "warning",
    "blocked",
    "not_configured",
    "unknown",
]

STATUS_ORDER: dict[str, int] = {
    "blocked": 5,
    "warning": 4,
    "not_configured": 3,
    "ready": 2,
    "unknown": 1,
}

STATUS_LABELS = {
    "ready": "READY",
    "warning": "WARN",
    "blocked": "BLOCK",
    "not_configured": "MISS",
    "unknown": "UNKNOWN",
}

KNOWN_PROFILES = {"python", "typescript", "nextjs", "monorepo", "mixed", "unknown"}


@dataclass(frozen=True)
class ScorecardDimension:
    """One user-facing readiness dimension."""

    id: str
    status: ScorecardStatus
    message: str
    evidence: dict[str, Any]
    suggestion: str | None = None
    next_actions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        """Return a stable JSON-safe dimension payload."""
        return {
            "id": self.id,
            "status": self.status,
            "message": self.message,
            "evidence": self.evidence,
            "suggestion": self.suggestion,
            "next_actions": list(self.next_actions),
        }


def build_scorecard(
    *, root: Path, config_path: Path | None = None, from_run: str | None = "latest"
) -> dict[str, Any]:
    """Build a read-only scorecard from local config, artifacts, and tool signals."""
    root = root.expanduser().resolve()
    config, config_dimension, config_status = load_scorecard_config(
        root=root, config_path=config_path
    )
    evidence_summary = build_optional_evidence_summary(
        root=root,
        config=config,
        from_run=from_run,
    )
    dimensions = [
        config_dimension,
        profile_dimension(root=root, config=config, config_status=config_status),
        fast_checks_dimension(config=config, config_status=config_status),
        deep_semgrep_dimension(config=config, config_status=config_status),
        benchmark_corpus_dimension(root=root),
        repair_prompt_dimension(evidence_summary=evidence_summary),
        verify_dimension(evidence_summary=evidence_summary),
        github_action_dimension(root=root),
        installed_package_smoke_dimension(root=root),
        evidence_freshness_dimension(evidence_summary=evidence_summary),
    ]
    dimension_payloads = [dimension.to_dict() for dimension in dimensions]
    summary = summarize_dimensions(dimensions)
    status = overall_status(summary)

    return {
        "kind": SCORECARD_KIND,
        "schema_version": SCORECARD_SCHEMA_VERSION,
        "status": status,
        "version": package_version(),
        "root": str(root),
        "generated_at": datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "dimensions": dimension_payloads,
        "summary": summary,
        "next_actions": collect_next_actions(dimensions),
        "warnings": collect_warnings(dimensions),
    }


def load_scorecard_config(
    *, root: Path, config_path: Path | None
) -> tuple[dict[str, Any] | None, ScorecardDimension, str]:
    """Load and validate qa-z.yaml without falling back to starter config."""
    if not root.exists():
        return (
            None,
            ScorecardDimension(
                id="project_config",
                status="blocked",
                message=f"repository root does not exist: {root}",
                evidence={"root": str(root), "exists": False},
                suggestion="Run scorecard from an existing repository root.",
            ),
            "blocked",
        )

    target = config_path if config_path is not None else root / "qa-z.yaml"
    if config_path is not None and not config_path.is_absolute():
        target = (root / config_path).resolve()
    else:
        target = target.expanduser().resolve()

    if not target.is_file():
        return (
            None,
            ScorecardDimension(
                id="project_config",
                status="blocked",
                message="qa-z.yaml is missing.",
                evidence={"path": format_path(target, root), "exists": False},
                suggestion="Initialize QA-Z project configuration.",
                next_actions=("qa-z init",),
            ),
            "blocked",
        )

    try:
        config = load_config(root, config_path=target)
    except ConfigError as exc:
        return (
            None,
            ScorecardDimension(
                id="project_config",
                status="blocked",
                message=f"qa-z.yaml could not be loaded: {exc}",
                evidence={"path": format_path(target, root), "exists": True},
                suggestion="Fix qa-z.yaml syntax and rerun `qa-z doctor`.",
                next_actions=("qa-z doctor --json",),
            ),
            "blocked",
        )

    validation = validate_config(root, config)
    if validation["status"] == "failed":
        return (
            config,
            ScorecardDimension(
                id="project_config",
                status="blocked",
                message="qa-z.yaml loaded but validation failed.",
                evidence={
                    "path": format_path(target, root),
                    "exists": True,
                    "errors": validation["errors"],
                    "warnings": validation["warnings"],
                },
                suggestion="Fix config validation errors before relying on QA-Z gates.",
                next_actions=("qa-z doctor --json",),
            ),
            "blocked",
        )
    if validation["status"] == "warning":
        return (
            config,
            ScorecardDimension(
                id="project_config",
                status="warning",
                message="qa-z.yaml loaded with validation warnings.",
                evidence={
                    "path": format_path(target, root),
                    "exists": True,
                    "warnings": validation["warnings"],
                },
                suggestion="Review `qa-z doctor` warnings.",
                next_actions=("qa-z doctor --json",),
            ),
            "warning",
        )
    return (
        config,
        ScorecardDimension(
            id="project_config",
            status="ready",
            message="qa-z.yaml loaded and validated.",
            evidence={"path": format_path(target, root), "exists": True},
        ),
        "ready",
    )


def profile_dimension(
    *, root: Path, config: dict[str, Any] | None, config_status: str
) -> ScorecardDimension:
    """Report configured profile/language fit against repository signals."""
    signals = detect_profile_signals(root)
    detected = signals["detected_profile"]
    if config is None:
        return ScorecardDimension(
            id="profile",
            status="unknown" if config_status != "blocked" else "not_configured",
            message="profile cannot be assessed without qa-z.yaml.",
            evidence=signals,
            suggestion="Initialize QA-Z with the closest project profile.",
            next_actions=("qa-z init --profile python",),
        )

    languages = configured_languages(config)
    evidence = {
        "configured_languages": languages,
        "detected_profile": detected,
        "signals": signals["signals"],
    }
    if not languages:
        return ScorecardDimension(
            id="profile",
            status="warning",
            message="project.languages is not configured.",
            evidence=evidence,
            suggestion="Set project.languages to match this repository.",
            next_actions=("qa-z doctor --json",),
        )
    if profile_matches_languages(str(detected), languages):
        return ScorecardDimension(
            id="profile",
            status="ready",
            message=f"profile signals match configured languages: {', '.join(languages)}.",
            evidence=evidence,
        )
    return ScorecardDimension(
        id="profile",
        status="warning",
        message=(
            f"configured languages ({', '.join(languages)}) may not match "
            f"repo signals ({detected})."
        ),
        evidence=evidence,
        suggestion="Review profile assumptions before trusting selected checks.",
        next_actions=("qa-z doctor --json",),
    )


def fast_checks_dimension(
    *, config: dict[str, Any] | None, config_status: str
) -> ScorecardDimension:
    """Report whether fast checks are configured."""
    checks = configured_checks(config, "fast") if config is not None else []
    enabled = enabled_checks(checks)
    if config is None:
        return ScorecardDimension(
            id="fast_checks",
            status="not_configured" if config_status == "blocked" else "unknown",
            message="fast checks cannot be assessed without qa-z.yaml.",
            evidence={"configured_count": 0, "enabled_count": 0},
            suggestion="Initialize QA-Z project configuration.",
            next_actions=("qa-z init",),
        )
    if not enabled:
        return ScorecardDimension(
            id="fast_checks",
            status="not_configured",
            message="no enabled fast checks are configured.",
            evidence={"configured_count": len(checks), "enabled_count": 0},
            suggestion="Add deterministic fast checks before using guard gates.",
            next_actions=("qa-z init",),
        )
    return ScorecardDimension(
        id="fast_checks",
        status="ready",
        message=f"{len(enabled)} enabled fast check(s) configured.",
        evidence={
            "configured_count": len(checks),
            "enabled_count": len(enabled),
            "check_ids": check_ids(enabled),
        },
        next_actions=("qa-z fast --json",),
    )


def deep_semgrep_dimension(
    *, config: dict[str, Any] | None, config_status: str
) -> ScorecardDimension:
    """Report whether deep Semgrep checks are configured and executable."""
    checks = configured_checks(config, "deep") if config is not None else []
    enabled = enabled_checks(checks)
    semgrep_configured = any(check_uses_semgrep(check) for check in enabled)
    semgrep_path = shutil.which("semgrep")
    evidence = {
        "configured_count": len(checks),
        "enabled_count": len(enabled),
        "semgrep_configured": semgrep_configured,
        "semgrep_path": semgrep_path,
    }
    if config is None:
        return ScorecardDimension(
            id="deep_semgrep",
            status="not_configured" if config_status == "blocked" else "unknown",
            message="deep checks cannot be assessed without qa-z.yaml.",
            evidence=evidence,
            suggestion="Initialize QA-Z project configuration.",
        )
    if not enabled or not semgrep_configured:
        return ScorecardDimension(
            id="deep_semgrep",
            status="not_configured",
            message="no enabled Semgrep deep check is configured.",
            evidence=evidence,
            suggestion="Enable the built-in sg_scan deep check for stronger coverage.",
            next_actions=("qa-z init",),
        )
    if not semgrep_path:
        return ScorecardDimension(
            id="deep_semgrep",
            status="warning",
            message="Semgrep not found; deep checks may be limited.",
            evidence=evidence,
            suggestion="Install Semgrep when deep static-analysis coverage is needed.",
            next_actions=("Install Semgrep", "qa-z deep --from-run latest"),
        )
    return ScorecardDimension(
        id="deep_semgrep",
        status="ready",
        message="Semgrep deep check is configured and semgrep is on PATH.",
        evidence=evidence,
        next_actions=("qa-z deep --from-run latest",),
    )


def benchmark_corpus_dimension(*, root: Path) -> ScorecardDimension:
    """Report whether the local seeded benchmark corpus is available."""
    fixtures_dir = root / "benchmarks" / "fixtures"
    summary_path = root / "benchmarks" / "results" / "summary.json"
    fixture_count = (
        len([path for path in fixtures_dir.iterdir() if path.is_dir()])
        if fixtures_dir.is_dir()
        else 0
    )
    evidence = {
        "fixtures_dir": format_path(fixtures_dir, root),
        "fixtures_dir_exists": fixtures_dir.is_dir(),
        "fixture_count": fixture_count,
        "summary_path": format_path(summary_path, root),
        "summary_exists": summary_path.is_file(),
    }
    if not fixtures_dir.is_dir():
        return ScorecardDimension(
            id="benchmark_corpus",
            status="unknown",
            message="benchmark corpus is not present in this repository.",
            evidence=evidence,
            suggestion="This dimension applies to QA-Z source checkouts.",
        )
    if summary_path.is_file():
        summary = load_json_object(summary_path)
        if summary is None:
            return ScorecardDimension(
                id="benchmark_corpus",
                status="warning",
                message="benchmark summary exists but could not be parsed.",
                evidence=evidence,
                suggestion="Rerun the benchmark to refresh local evidence.",
                next_actions=("qa-z benchmark --json",),
            )
        failed = int_value(summary.get("fixtures_failed"))
        snapshot = summary.get("snapshot")
        status: ScorecardStatus = "ready" if failed == 0 else "warning"
        message = (
            f"benchmark summary available: {snapshot}"
            if isinstance(snapshot, str)
            else "benchmark summary available."
        )
        evidence["summary"] = {
            "snapshot": snapshot,
            "fixtures_failed": failed,
            "fixtures_total": int_value(summary.get("fixtures_total")),
        }
        return ScorecardDimension(
            id="benchmark_corpus",
            status=status,
            message=message,
            evidence=evidence,
            next_actions=("qa-z benchmark --json",),
        )
    return ScorecardDimension(
        id="benchmark_corpus",
        status="ready",
        message=f"{fixture_count} benchmark fixture(s) available for local readiness proof.",
        evidence=evidence,
        next_actions=("qa-z benchmark --json",),
    )


def repair_prompt_dimension(
    *, evidence_summary: dict[str, Any] | None
) -> ScorecardDimension:
    """Report whether repair handoff evidence is ready."""
    if evidence_summary is None:
        return ScorecardDimension(
            id="repair_prompt",
            status="not_configured",
            message="no latest run is available for repair prompt readiness.",
            evidence={"run_dir": None},
            suggestion="Run a guard flow to create evidence first.",
            next_actions=("qa-z guard --adapter codex --deep auto",),
        )
    repair_prompt = evidence_summary.get("repair_prompt")
    verdict = string_value(evidence_summary.get("verdict"))
    evidence = {
        "run_dir": evidence_summary.get("run_dir"),
        "verdict": verdict,
        "repair_prompt": repair_prompt,
    }
    if isinstance(repair_prompt, dict) and repair_prompt.get("exists") is True:
        return ScorecardDimension(
            id="repair_prompt",
            status="ready",
            message="repair prompt artifact is available.",
            evidence=evidence,
            next_actions=("qa-z repair-prompt --from-run latest --adapter codex",),
        )
    if verdict in {"do_not_merge", "needs_review", "error"}:
        return ScorecardDimension(
            id="repair_prompt",
            status="warning",
            message="latest evidence needs repair guidance but no repair prompt exists.",
            evidence=evidence,
            suggestion="Generate a repair prompt before handing work to an executor.",
            next_actions=("qa-z repair-prompt --from-run latest --adapter codex",),
        )
    return ScorecardDimension(
        id="repair_prompt",
        status="not_configured",
        message="repair prompt is not needed until a failed or review-needed run exists.",
        evidence=evidence,
        next_actions=("qa-z guard --adapter codex --deep auto",),
    )


def verify_dimension(*, evidence_summary: dict[str, Any] | None) -> ScorecardDimension:
    """Report whether repair verification evidence is available."""
    if evidence_summary is None:
        return ScorecardDimension(
            id="verify",
            status="not_configured",
            message="no latest run is available for verify readiness.",
            evidence={"run_dir": None},
            suggestion="Run guard and repair-prompt before verify.",
            next_actions=("qa-z guard --adapter codex --deep auto",),
        )
    verify_report = evidence_summary.get("verify_report")
    repair_prompt = evidence_summary.get("repair_prompt")
    evidence = {
        "run_dir": evidence_summary.get("run_dir"),
        "repair_prompt": repair_prompt,
        "verify_report": verify_report,
    }
    if isinstance(verify_report, dict) and verify_report.get("exists") is True:
        return ScorecardDimension(
            id="verify",
            status="ready",
            message="verify report artifact is available.",
            evidence=evidence,
            next_actions=("qa-z verify --from-run latest",),
        )
    if isinstance(repair_prompt, dict) and repair_prompt.get("exists") is True:
        return ScorecardDimension(
            id="verify",
            status="warning",
            message="repair prompt exists but verify has not run yet.",
            evidence=evidence,
            suggestion="Run verify after the repair is applied.",
            next_actions=("qa-z verify --from-run latest",),
        )
    return ScorecardDimension(
        id="verify",
        status="not_configured",
        message="verify waits for a repair prompt and candidate fix.",
        evidence=evidence,
        next_actions=("qa-z repair-prompt --from-run latest --adapter codex",),
    )


def github_action_dimension(*, root: Path) -> ScorecardDimension:
    """Report whether a QA-Z GitHub Actions workflow appears configured."""
    workflows_dir = root / ".github" / "workflows"
    workflow_paths = sorted(
        path
        for pattern in ("*.yml", "*.yaml")
        for path in workflows_dir.glob(pattern)
        if path.is_file()
    )
    qa_z_paths = [path for path in workflow_paths if workflow_mentions_qa_z(path)]
    evidence = {
        "workflow_paths": [format_path(path, root) for path in qa_z_paths],
        "workflow_count": len(qa_z_paths),
    }
    if qa_z_paths:
        return ScorecardDimension(
            id="github_action",
            status="ready",
            message=f"{len(qa_z_paths)} QA-Z GitHub Actions workflow(s) found.",
            evidence=evidence,
            next_actions=("qa-z github-summary --from-run latest",),
        )
    return ScorecardDimension(
        id="github_action",
        status="not_configured",
        message="no QA-Z GitHub Actions workflow was found.",
        evidence=evidence,
        suggestion="Add the starter workflow when PR gate evidence should run in CI.",
        next_actions=("qa-z init --with-github-workflow",),
    )


def installed_package_smoke_dimension(*, root: Path) -> ScorecardDimension:
    """Report QA-Z installed-package smoke evidence when applicable."""
    smoke_script = root / "scripts" / "installed_package_smoke.py"
    smoke_report = root / "docs" / "reports" / "v0.10.0-beta-installed-package-smoke.md"
    evidence = {
        "script_path": format_path(smoke_script, root),
        "script_exists": smoke_script.is_file(),
        "report_path": format_path(smoke_report, root),
        "report_exists": smoke_report.is_file(),
    }
    if not smoke_script.is_file():
        return ScorecardDimension(
            id="installed_package_smoke",
            status="unknown",
            message="installed-package smoke is not applicable outside a QA-Z source checkout.",
            evidence=evidence,
        )
    if smoke_report.is_file():
        return ScorecardDimension(
            id="installed_package_smoke",
            status="ready",
            message="installed-package smoke script and report are present.",
            evidence=evidence,
            next_actions=("python scripts/installed_package_smoke.py --json",),
        )
    return ScorecardDimension(
        id="installed_package_smoke",
        status="warning",
        message="installed-package smoke script exists but no smoke report was found.",
        evidence=evidence,
        suggestion="Run the installed-package smoke before packaging decisions.",
        next_actions=("python scripts/installed_package_smoke.py --json",),
    )


def evidence_freshness_dimension(
    *, evidence_summary: dict[str, Any] | None
) -> ScorecardDimension:
    """Report whether latest run evidence exists and is easy to navigate."""
    if evidence_summary is None:
        return ScorecardDimension(
            id="evidence_freshness",
            status="not_configured",
            message="no latest QA-Z run evidence was found.",
            evidence={"run_dir": None},
            suggestion="Run guard or demo to create a first evidence bundle.",
            next_actions=(
                "qa-z guard --adapter codex --deep auto",
                "qa-z demo auth-bug",
            ),
        )
    warnings = evidence_summary.get("warnings")
    verdict = string_value(evidence_summary.get("verdict"))
    status = string_value(evidence_summary.get("status"))
    verify_report = evidence_summary.get("verify_report")
    verify_status = (
        string_value(verify_report.get("status"))
        if isinstance(verify_report, dict)
        else None
    )
    evidence = {
        "run_dir": evidence_summary.get("run_dir"),
        "status": status,
        "verdict": verdict,
        "verify_status": verify_status,
        "warnings": warnings if isinstance(warnings, list) else [],
        "top_findings_count": list_count(evidence_summary.get("top_findings")),
    }
    if isinstance(warnings, list) and warnings:
        return ScorecardDimension(
            id="evidence_freshness",
            status="warning",
            message="latest evidence exists but has missing or stale pieces.",
            evidence=evidence,
            suggestion="Open the local evidence navigator for exact paths.",
            next_actions=("qa-z summary --from-run latest",),
        )
    if verify_status == "improved":
        return ScorecardDimension(
            id="evidence_freshness",
            status="ready",
            message="latest evidence includes an improved verify result.",
            evidence=evidence,
            next_actions=("qa-z summary --from-run latest",),
        )
    if verdict in {"do_not_merge", "needs_review", "error"}:
        return ScorecardDimension(
            id="evidence_freshness",
            status="warning",
            message=f"latest evidence is present with verdict {verdict}.",
            evidence=evidence,
            next_actions=("qa-z summary --from-run latest",),
        )
    return ScorecardDimension(
        id="evidence_freshness",
        status="ready",
        message="latest evidence is present and navigable.",
        evidence=evidence,
        next_actions=("qa-z summary --from-run latest",),
    )


def build_optional_evidence_summary(
    *, root: Path, config: dict[str, Any] | None, from_run: str | None
) -> dict[str, Any] | None:
    """Return evidence summary only when a real run exists."""
    if config is None:
        return None
    summary = build_evidence_summary(root=root, config=config, from_run=from_run)
    if summary.get("status") == "missing":
        return None
    return summary


def configured_languages(config: dict[str, Any]) -> list[str]:
    project = config.get("project")
    if not isinstance(project, dict):
        return []
    languages = project.get("languages")
    if not isinstance(languages, list):
        return []
    return sorted(
        {
            str(language).strip().lower()
            for language in languages
            if str(language).strip()
        }
    )


def detect_profile_signals(root: Path) -> dict[str, Any]:
    """Detect lightweight repository language/profile signals."""
    signal_paths = {
        "pyproject.toml": root / "pyproject.toml",
        "requirements.txt": root / "requirements.txt",
        "setup.py": root / "setup.py",
        "setup.cfg": root / "setup.cfg",
        "package.json": root / "package.json",
        "tsconfig.json": root / "tsconfig.json",
        "pnpm-workspace.yaml": root / "pnpm-workspace.yaml",
        "turbo.json": root / "turbo.json",
    }
    signals: dict[str, object] = {
        name: path.exists() for name, path in signal_paths.items()
    }
    next_config = any(root.glob("next.config.*"))
    apps_dir = root / "apps"
    packages_dir = root / "packages"
    package_json_count = len(list(root.glob("**/package.json")))
    python = any(
        signals[name]
        for name in ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg")
    )
    typescript = signals["package.json"] or signals["tsconfig.json"]
    monorepo = (
        signals["pnpm-workspace.yaml"]
        or signals["turbo.json"]
        or apps_dir.is_dir()
        or packages_dir.is_dir()
        or package_json_count > 1
    )
    if monorepo and python and typescript:
        detected = "mixed"
    elif monorepo:
        detected = "monorepo"
    elif next_config:
        detected = "nextjs"
    elif python and typescript:
        detected = "mixed"
    elif python:
        detected = "python"
    elif typescript:
        detected = "typescript"
    else:
        detected = "unknown"
    signals["next_config"] = next_config
    signals["apps_dir"] = apps_dir.is_dir()
    signals["packages_dir"] = packages_dir.is_dir()
    signals["package_json_count"] = package_json_count
    return {"detected_profile": detected, "signals": signals}


def profile_matches_languages(profile: str, languages: list[str]) -> bool:
    language_set = set(languages)
    if profile == "unknown":
        return True
    if profile == "python":
        return "python" in language_set
    if profile in {"typescript", "nextjs"}:
        return "typescript" in language_set or "javascript" in language_set
    if profile in {"mixed", "monorepo"}:
        return "python" in language_set and (
            "typescript" in language_set or "javascript" in language_set
        )
    return profile in KNOWN_PROFILES


def configured_checks(config: dict[str, Any] | None, section_name: str) -> list[Any]:
    if config is None:
        return []
    section = config.get(section_name)
    if not isinstance(section, dict):
        return []
    checks = section.get("checks")
    return checks if isinstance(checks, list) else []


def enabled_checks(checks: list[Any]) -> list[Any]:
    return [
        check
        for check in checks
        if not (isinstance(check, dict) and check.get("enabled") is False)
    ]


def check_ids(checks: list[Any]) -> list[str]:
    ids: list[str] = []
    for check in checks:
        if isinstance(check, str):
            ids.append(check)
        elif isinstance(check, dict) and isinstance(check.get("id"), str):
            ids.append(check["id"])
    return ids


def check_uses_semgrep(check: Any) -> bool:
    if isinstance(check, str):
        return check == "sg_scan"
    if not isinstance(check, dict):
        return False
    check_id = str(check.get("id") or "")
    command = check.get("run")
    return check_id == "sg_scan" or (
        isinstance(command, list) and any(str(part) == "semgrep" for part in command)
    )


def workflow_mentions_qa_z(path: Path) -> bool:
    try:
        text = path.read_text(encoding="utf-8").lower()
    except OSError:
        return False
    return "qa-z" in text or "qa_z" in text


def load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def summarize_dimensions(dimensions: list[ScorecardDimension]) -> dict[str, int]:
    summary = {status: 0 for status in STATUS_ORDER}
    for dimension in dimensions:
        summary[dimension.status] += 1
    return summary


def overall_status(summary: dict[str, int]) -> ScorecardStatus:
    if summary["blocked"]:
        return "blocked"
    if summary["warning"]:
        return "warning"
    if summary["not_configured"]:
        return "not_configured"
    if summary["ready"]:
        return "ready"
    return "unknown"


def collect_next_actions(dimensions: list[ScorecardDimension]) -> list[str]:
    actions: list[str] = []
    seen: set[str] = set()
    ordered = sorted(
        dimensions,
        key=lambda dimension: STATUS_ORDER[dimension.status],
        reverse=True,
    )
    for dimension in ordered:
        for action in dimension.next_actions:
            if action not in seen:
                actions.append(action)
                seen.add(action)
    return actions


def collect_warnings(dimensions: list[ScorecardDimension]) -> list[str]:
    return [
        f"{dimension.id}: {dimension.message}"
        for dimension in dimensions
        if dimension.status in {"warning", "blocked"}
    ]


def package_version() -> str:
    try:
        return version("qa-z")
    except PackageNotFoundError:
        return "unknown"


def string_value(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def int_value(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if not isinstance(value, str):
        return None
    try:
        return int(value)
    except ValueError:
        return None


def list_count(value: object) -> int:
    return len(value) if isinstance(value, list) else 0
