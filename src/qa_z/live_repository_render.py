"""Rendering and classification helpers for live repository signals."""

from __future__ import annotations

from typing import Any

LOCAL_ONLY_RUNTIME_PREFIXES = (
    ".mypy_cache",
    ".mypy_cache_safe",
    ".pytest_cache",
    ".qa-z",
    ".ruff_cache",
    ".ruff_cache_safe",
    "%TEMP%",
    "build",
    "dist",
    "src/qa_z.egg-info",
)


def live_repository_summary(live_signals: dict[str, Any]) -> dict[str, Any]:
    """Return the compact live state recorded in self-inspection artifacts."""
    from qa_z.live_repository import (
        dirty_benchmark_result_paths,
        dirty_worktree_paths,
        generated_artifact_policy_is_explicit,
    )

    dirty_paths = dirty_worktree_paths(live_signals)
    dirty_benchmark_paths = dirty_benchmark_result_paths(live_signals)
    return {
        "modified_count": _int_value(live_signals.get("modified_count")),
        "untracked_count": _int_value(live_signals.get("untracked_count")),
        "staged_count": _int_value(live_signals.get("staged_count")),
        "runtime_artifact_count": len(
            list_signal_paths(live_signals, "runtime_artifact_paths")
        ),
        "benchmark_result_count": len(
            list_signal_paths(live_signals, "benchmark_result_paths")
        ),
        "dirty_benchmark_result_count": len(dirty_benchmark_paths),
        "release_evidence_count": len(
            list_signal_paths(live_signals, "release_evidence_paths")
        ),
        "current_branch": str(live_signals.get("current_branch") or "").strip() or None,
        "current_head": str(live_signals.get("current_head") or "").strip() or None,
        "generated_artifact_policy_explicit": generated_artifact_policy_is_explicit(
            live_signals
        ),
        "dirty_area_summary": worktree_area_summary(dirty_paths),
    }


def render_live_repository_summary(live_repository: object) -> str:
    """Render compact live repository state for human operator surfaces."""
    if not isinstance(live_repository, dict):
        return "not recorded"
    parts = [
        f"modified={_int_value(live_repository.get('modified_count'))}",
        f"untracked={_int_value(live_repository.get('untracked_count'))}",
        f"staged={_int_value(live_repository.get('staged_count'))}",
        "runtime_artifacts="
        + str(_int_value(live_repository.get("runtime_artifact_count"))),
        f"benchmark_results={_int_value(live_repository.get('benchmark_result_count'))}",
        "dirty_benchmark_results="
        + str(_int_value(live_repository.get("dirty_benchmark_result_count"))),
        f"release_evidence={_int_value(live_repository.get('release_evidence_count'))}",
        "generated_policy="
        + (
            "true"
            if live_repository.get("generated_artifact_policy_explicit")
            else "false"
        ),
    ]
    current_branch = str(live_repository.get("current_branch") or "").strip()
    if current_branch:
        parts.append(
            "branch=detached"
            if current_branch == "HEAD"
            else f"branch={current_branch}"
        )
    current_head = str(live_repository.get("current_head") or "").strip()
    if current_head:
        parts.append(f"head={current_head}")
    dirty_area_summary = str(live_repository.get("dirty_area_summary") or "").strip()
    if dirty_area_summary:
        parts.append(f"areas={dirty_area_summary}")
    return "; ".join(parts)


def list_signal_paths(signals: dict[str, Any], key: str) -> list[str]:
    """Return stable string paths from one live-signal field."""
    value = signals.get(key)
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def sample_signal_paths(paths: list[str], limit: int = 3) -> list[str]:
    """Return a stable sample of signal paths for concise evidence text."""
    return sorted({path for path in paths if path.strip()})[:limit]


def _is_local_by_default_benchmark_result_path(path_text: str) -> bool:
    """Return whether a path is benchmark result evidence, not runtime cleanup."""
    normalized = path_text.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized in {
        "benchmarks/results/summary.json",
        "benchmarks/results/report.md",
    }:
        return True
    if normalized.startswith("benchmarks/results/") and not normalized.startswith(
        "benchmarks/results/work/"
    ):
        return True
    return normalized.startswith("benchmarks/results-")


def classify_worktree_path_area(path_text: str) -> str:
    """Classify a dirty worktree path into a stable repository area."""
    normalized = path_text.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if _is_local_by_default_benchmark_result_path(normalized):
        return "benchmark"
    if is_runtime_artifact_path(normalized):
        return "runtime_artifact"
    if normalized.startswith(".github/workflows/"):
        return "workflow"
    if normalized.startswith("src/"):
        return "source"
    if normalized.startswith("tests/"):
        return "tests"
    if normalized == "README.md" or normalized.startswith("docs/"):
        return "docs"
    if normalized.startswith("benchmarks/") or normalized.startswith("benchmark/"):
        return "benchmark"
    if normalized.startswith("examples/"):
        return "examples"
    if normalized.startswith("templates/"):
        return "templates"
    if normalized in {".gitignore", "mypy.ini", "pyproject.toml", "qa-z.yaml.example"}:
        return "config"
    return "other"


def worktree_area_summary(paths: list[str], *, limit: int = 5) -> str:
    """Return concise dirty-path area counts for worktree triage evidence."""
    counts: dict[str, int] = {}
    for path in paths:
        if not str(path).strip():
            continue
        area = classify_worktree_path_area(str(path))
        counts[area] = counts.get(area, 0) + 1
    if not counts:
        return ""
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return ", ".join(f"{area}:{count}" for area, count in ordered[:limit])


def is_runtime_artifact_path(path_text: str) -> bool:
    """Return whether a path points at local runtime or generated artifact output."""
    normalized = path_text.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    if normalized.startswith("tmp_"):
        return True
    if normalized.startswith("benchmarks/minlock-"):
        return True
    if "__pycache__" in normalized.split("/"):
        return True
    if any(
        normalized == prefix or normalized.startswith(f"{prefix}/")
        for prefix in LOCAL_ONLY_RUNTIME_PREFIXES
    ):
        return True
    return normalized.startswith("benchmarks/results/") or normalized.startswith(
        "benchmarks/results-"
    )


def is_release_evidence_path(path_text: str) -> bool:
    """Return whether a worktree path is generated alpha release evidence."""
    normalized = path_text.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.startswith("dist/alpha-release-gate") and normalized.endswith(
        ".json"
    )


def _int_value(value: object) -> int:
    """Return an integer value, or zero when absent or invalid."""
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
