"""Repository profile detection for qa-z init and doctor."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

ProfileName = Literal[
    "python",
    "typescript",
    "nextjs",
    "monorepo",
    "mixed",
    "unknown",
]
ProfileConfidence = Literal["high", "medium", "low"]

SUPPORTED_DETECTED_PROFILES: tuple[ProfileName, ...] = (
    "python",
    "typescript",
    "nextjs",
    "monorepo",
    "mixed",
    "unknown",
)

PYTHON_METADATA = ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg")
TYPESCRIPT_METADATA = ("package.json", "tsconfig.json")
NEXT_CONFIG_FILES = (
    "next.config.js",
    "next.config.cjs",
    "next.config.mjs",
    "next.config.ts",
    "next.config.mts",
)
MONOREPO_METADATA = ("pnpm-workspace.yaml", "turbo.json")
SCAN_SKIP_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".qa-z",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "venv",
}


@dataclass(frozen=True)
class ProfileDetectionResult:
    """Profile auto-detection result for first-time setup."""

    profile: ProfileName
    confidence: ProfileConfidence
    evidence_files: tuple[str, ...]
    activated_check_assumptions: tuple[str, ...]
    warnings: tuple[str, ...] = ()


def detect_profile(root: Path) -> ProfileDetectionResult:
    """Detect the closest starter profile for a repository root."""
    root = root.expanduser().resolve()
    evidence: list[str] = []
    warnings: list[str] = []

    existing_config = root / "qa-z.yaml"
    if existing_config.exists():
        evidence.append("qa-z.yaml")
        warnings.append("existing qa-z.yaml will not be overwritten by init.")

    python_evidence = existing_metadata(root, PYTHON_METADATA)
    typescript_evidence = existing_metadata(root, TYPESCRIPT_METADATA)
    next_evidence = detect_nextjs_evidence(root, typescript_evidence)
    monorepo_evidence = detect_monorepo_evidence(root)
    nested_python = nested_metadata(root, PYTHON_METADATA)
    nested_package_json = nested_package_json_evidence(root)

    python_signal = bool(python_evidence or nested_python)
    typescript_signal = bool(typescript_evidence or nested_package_json)
    next_signal = bool(next_evidence)
    monorepo_signal = bool(monorepo_evidence or len(nested_package_json) > 1)

    evidence.extend(python_evidence)
    evidence.extend(typescript_evidence)
    evidence.extend(next_evidence)
    evidence.extend(monorepo_evidence)
    evidence.extend(nested_python)
    if len(nested_package_json) > 1:
        evidence.append("multiple package.json files")

    if monorepo_signal:
        return ProfileDetectionResult(
            profile="monorepo",
            confidence="high" if python_signal or typescript_signal else "medium",
            evidence_files=unique_tuple(evidence),
            activated_check_assumptions=assumptions_for_profile("monorepo"),
            warnings=tuple(warnings),
        )
    if next_signal and not python_signal:
        return ProfileDetectionResult(
            profile="nextjs",
            confidence="high",
            evidence_files=unique_tuple(evidence),
            activated_check_assumptions=assumptions_for_profile("nextjs"),
            warnings=tuple(warnings),
        )
    if python_signal and typescript_signal:
        warnings.append(
            "Python and TypeScript signals were both found without monorepo layout signals."
        )
        return ProfileDetectionResult(
            profile="mixed",
            confidence="medium",
            evidence_files=unique_tuple(evidence),
            activated_check_assumptions=assumptions_for_profile("mixed"),
            warnings=tuple(warnings),
        )
    if python_signal:
        return ProfileDetectionResult(
            profile="python",
            confidence="high",
            evidence_files=unique_tuple(evidence),
            activated_check_assumptions=assumptions_for_profile("python"),
            warnings=tuple(warnings),
        )
    if typescript_signal or next_signal:
        return ProfileDetectionResult(
            profile="typescript",
            confidence="high" if typescript_signal else "medium",
            evidence_files=unique_tuple(evidence),
            activated_check_assumptions=assumptions_for_profile("typescript"),
            warnings=tuple(warnings),
        )

    warnings.append("No Python, TypeScript, Next.js, or monorepo signals were found.")
    return ProfileDetectionResult(
        profile="unknown",
        confidence="low",
        evidence_files=unique_tuple(evidence),
        activated_check_assumptions=assumptions_for_profile("unknown"),
        warnings=tuple(warnings),
    )


def assumptions_for_profile(profile: str) -> tuple[str, ...]:
    """Return human-readable starter check assumptions for a profile."""
    if profile == "python":
        return ("Python fast checks", "Semgrep deep checks")
    if profile == "typescript":
        return ("TypeScript fast checks", "Semgrep deep checks")
    if profile == "nextjs":
        return (
            "Next.js TypeScript surface",
            "TypeScript fast checks",
            "Semgrep deep checks",
        )
    if profile in {"monorepo", "mixed"}:
        return (
            "Python fast checks",
            "TypeScript fast checks",
            "smart selection",
            "Semgrep deep checks",
        )
    return ("manual profile review", "Semgrep deep checks")


def existing_metadata(root: Path, names: tuple[str, ...]) -> list[str]:
    """Return top-level metadata files that exist in declaration order."""
    return [name for name in names if (root / name).is_file()]


def detect_nextjs_evidence(root: Path, current: list[str]) -> list[str]:
    """Return Next.js evidence without duplicating package.json."""
    evidence: list[str] = []
    package_json = root / "package.json"
    if package_json.is_file() and package_json_has_dependency(package_json, "next"):
        if "package.json" not in current:
            evidence.append("package.json")
    evidence.extend(name for name in NEXT_CONFIG_FILES if (root / name).is_file())
    return evidence


def package_json_has_dependency(path: Path, dependency: str) -> bool:
    """Return whether package.json names a dependency or devDependency."""
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(loaded, dict):
        return False
    for section in ("dependencies", "devDependencies"):
        values = loaded.get(section)
        if isinstance(values, dict) and dependency in values:
            return True
    return False


def detect_monorepo_evidence(root: Path) -> list[str]:
    """Return workspace/layout evidence for monorepo starters."""
    evidence = existing_metadata(root, MONOREPO_METADATA)
    for directory in ("apps", "packages"):
        if (root / directory).is_dir():
            evidence.append(f"{directory}/")
    return evidence


def nested_metadata(root: Path, names: tuple[str, ...]) -> list[str]:
    """Return metadata evidence under apps/* and packages/*."""
    evidence: list[str] = []
    for base_name in ("apps", "packages"):
        base = root / base_name
        if not base.is_dir():
            continue
        for child in sorted(path for path in base.iterdir() if path.is_dir()):
            for name in names:
                candidate = child / name
                if candidate.is_file():
                    evidence.append(relative_path(candidate, root))
    return evidence


def nested_package_json_evidence(root: Path) -> list[str]:
    """Return package.json files outside ignored directories."""
    evidence: list[str] = []
    try:
        if not root.exists():
            return evidence
    except OSError:
        return evidence

    def ignore_walk_error(_error: OSError) -> None:
        return None

    try:
        for current_root, directories, filenames in os.walk(
            root,
            topdown=True,
            onerror=ignore_walk_error,
        ):
            current_path = Path(current_root)
            try:
                current_relative = current_path.relative_to(root)
            except ValueError:
                directories[:] = []
                continue
            if any(part in SCAN_SKIP_DIRS for part in current_relative.parts):
                directories[:] = []
                continue
            directories[:] = [
                name for name in directories if name not in SCAN_SKIP_DIRS
            ]
            if "package.json" not in filenames:
                continue
            path = current_path / "package.json"
            if path == root / "package.json":
                continue
            evidence.append(relative_path(path, root))
    except OSError:
        return sorted(evidence)
    return sorted(evidence)


def is_ignored(path: Path, root: Path) -> bool:
    """Return whether a path lives under directories that should not signal source."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return True
    return any(part in SCAN_SKIP_DIRS for part in relative.parts)


def relative_path(path: Path, root: Path) -> str:
    """Render a stable repository-relative path."""
    return path.relative_to(root).as_posix()


def unique_tuple(values: list[str]) -> tuple[str, ...]:
    """Return unique strings in first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return tuple(result)
