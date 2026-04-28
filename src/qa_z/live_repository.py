"""Live repository signal collection and rendering for QA-Z operator flows."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path
from qa_z.live_repository_git import (
    empty_live_repository_signals,
    git_current_branch,
    git_current_head,
    git_worktree_snapshot,
)
from qa_z.live_repository_render import (
    _int_value,
    classify_worktree_path_area,
    is_release_evidence_path,
    is_runtime_artifact_path,
    list_signal_paths,
    live_repository_summary,
    render_live_repository_summary,
    sample_signal_paths,
    worktree_area_summary,
)

BENCHMARK_RESULT_ARTIFACTS = (
    Path("benchmarks/results/summary.json"),
    Path("benchmarks/results/report.md"),
)
GENERATED_ARTIFACT_POLICY_DOC = Path("docs/generated-vs-frozen-evidence-policy.md")
GENERATED_ARTIFACT_POLICY_RULES = (
    ".qa-z/",
    ".mypy_cache_safe/",
    ".ruff_cache_safe/",
    "%TEMP%/",
    "/tmp_*",
    "/benchmarks/minlock-*",
    "benchmarks/results/work/",
    "benchmarks/results-*",
    "benchmarks/results/summary.json",
    "benchmarks/results/report.md",
)
GENERATED_ARTIFACT_POLICY_TERMS = (
    ".qa-z",
    ".mypy_cache_safe",
    ".ruff_cache_safe",
    "%TEMP%",
    "/tmp_*",
    "/benchmarks/minlock-*",
    "benchmarks/results/work",
    "benchmarks/results-*",
    "benchmarks/results/summary.json",
    "benchmarks/results/report.md",
    "local-only runtime artifacts",
    "local-by-default benchmark evidence",
    "intentional frozen evidence",
    "benchmarks/fixtures",
)

__all__ = [
    "classify_worktree_path_area",
    "collect_live_repository_signals",
    "dirty_benchmark_result_paths",
    "empty_live_repository_signals",
    "generated_artifact_policy_evidence",
    "generated_artifact_policy_is_explicit",
    "git_current_branch",
    "git_current_head",
    "git_worktree_snapshot",
    "has_cleanup_artifact_pressure",
    "has_commit_isolation_worktree_pressure",
    "has_live_worktree_changes",
    "has_non_current_truth_worktree_pressure",
    "is_runtime_artifact_path",
    "list_signal_paths",
    "live_repository_summary",
    "render_live_repository_summary",
    "sample_signal_paths",
    "worktree_area_summary",
]


def _normalize_worktree_path(path_text: object) -> str:
    """Return a stable forward-slash worktree path for policy checks."""
    normalized = str(path_text or "").strip().replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _is_local_by_default_benchmark_result_path(path_text: object) -> bool:
    """Return whether a path is benchmark result evidence, not local-only runtime."""
    normalized = _normalize_worktree_path(path_text)
    if not normalized:
        return False
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


def _ordered_unique_paths(paths: list[str]) -> list[str]:
    """Preserve input order while removing duplicate worktree paths."""
    seen: set[str] = set()
    unique_paths: list[str] = []
    for path in paths:
        normalized = _normalize_worktree_path(path)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        unique_paths.append(path)
    return unique_paths


def generated_artifact_policy_is_explicit(live_signals: dict[str, Any]) -> bool:
    """Return whether ignore rules and policy docs cover generated artifacts."""
    return bool(live_signals.get("generated_artifact_policy_explicit"))


def has_live_worktree_changes(live_signals: dict[str, Any]) -> bool:
    """Return whether the current git status has source-facing changes."""
    return any(
        _int_value(live_signals.get(key))
        for key in ("modified_count", "untracked_count", "staged_count")
    )


def dirty_worktree_paths(live_signals: dict[str, Any]) -> list[str]:
    """Return dirty worktree paths from live git-status signals."""
    return list_signal_paths(live_signals, "modified_paths") + list_signal_paths(
        live_signals, "untracked_paths"
    )


def normalize_signal_path(path: object) -> str:
    """Return a normalized relative path for live-signal comparisons."""
    return str(path or "").strip().replace("\\", "/")


def dirty_benchmark_result_paths(live_signals: dict[str, Any]) -> list[str]:
    """Return benchmark summary/report paths that are also dirty in git status."""
    benchmark_paths = {
        normalize_signal_path(path)
        for path in list_signal_paths(live_signals, "benchmark_result_paths")
    }
    if not benchmark_paths:
        return []
    matches: list[str] = []
    seen: set[str] = set()
    for path in dirty_worktree_paths(live_signals):
        normalized = normalize_signal_path(path)
        if normalized in benchmark_paths and normalized not in seen:
            seen.add(normalized)
            matches.append(path)
    return matches


def has_non_current_truth_worktree_pressure(live_signals: dict[str, Any]) -> bool:
    """Return whether dirty paths extend beyond docs/current-truth test churn."""
    dirty_paths = dirty_worktree_paths(live_signals)
    areas = {
        classify_worktree_path_area(path)
        for path in dirty_paths
        if str(path).strip() and not _is_local_by_default_benchmark_result_path(path)
    }
    return bool(areas - {"docs", "tests"})


def has_commit_isolation_worktree_pressure(live_signals: dict[str, Any]) -> bool:
    """Return whether dirty paths still need a source-facing commit split."""
    dirty_paths = dirty_worktree_paths(live_signals)
    areas = {
        classify_worktree_path_area(path)
        for path in dirty_paths
        if str(path).strip()
        and classify_worktree_path_area(path) != "runtime_artifact"
        and not _is_local_by_default_benchmark_result_path(path)
    }
    return bool(areas - {"docs", "tests"})


def has_cleanup_artifact_pressure(live_signals: dict[str, Any]) -> bool:
    """Return whether generated outputs still need a cleanup decision."""
    if list_signal_paths(live_signals, "runtime_artifact_paths"):
        return True
    return bool(dirty_benchmark_result_paths(live_signals)) and not (
        generated_artifact_policy_is_explicit(live_signals)
    )


def generated_artifact_policy_snapshot(root: Path) -> dict[str, Any]:
    """Return whether generated-artifact ignore and doc policies are present."""
    rules = gitignore_rules(root)
    missing_rules = [
        rule for rule in GENERATED_ARTIFACT_POLICY_RULES if rule not in rules
    ]
    missing_terms = generated_artifact_policy_missing_terms(root)
    ignore_policy_explicit = not missing_rules
    documented_policy_explicit = not missing_terms
    return {
        "generated_artifact_ignore_policy_explicit": ignore_policy_explicit,
        "generated_artifact_documented_policy_explicit": documented_policy_explicit,
        "generated_artifact_policy_explicit": (
            ignore_policy_explicit and documented_policy_explicit
        ),
        "missing_generated_artifact_policy_rules": missing_rules,
        "missing_generated_artifact_policy_terms": missing_terms,
        "generated_artifact_policy_doc_path": str(GENERATED_ARTIFACT_POLICY_DOC),
    }


def generated_artifact_policy_missing_terms(root: Path) -> list[str]:
    """Return missing terms from the generated-versus-frozen policy document."""
    path = root / GENERATED_ARTIFACT_POLICY_DOC
    if not path.is_file():
        return ["generated-vs-frozen evidence policy document is missing"]
    text = " ".join(_read_text(path).lower().replace("\\", "/").split())
    return [
        f"policy document missing required term: {term}"
        for term in GENERATED_ARTIFACT_POLICY_TERMS
        if term.lower() not in text
    ]


def generated_artifact_policy_evidence(
    root: Path, live_signals: dict[str, Any]
) -> list[dict[str, Any]]:
    """Render missing generated-artifact policy pieces as inspection evidence."""
    evidence: list[dict[str, Any]] = []
    missing_rules = list_signal_paths(
        live_signals, "missing_generated_artifact_policy_rules"
    )
    if missing_rules:
        evidence.append(
            {
                "source": "generated_artifact_policy",
                "path": ".gitignore",
                "summary": "missing generated-artifact ignore rules: "
                + ", ".join(missing_rules),
            }
        )
    missing_terms = list_signal_paths(
        live_signals, "missing_generated_artifact_policy_terms"
    )
    if missing_terms:
        policy_doc_path = str(
            live_signals.get("generated_artifact_policy_doc_path")
            or GENERATED_ARTIFACT_POLICY_DOC
        )
        evidence.append(
            {
                "source": "generated_artifact_policy",
                "path": format_path(root / policy_doc_path, root),
                "summary": "; ".join(missing_terms),
            }
        )
    return evidence


def gitignore_rules(root: Path) -> set[str]:
    """Return normalized `.gitignore` rules for lightweight policy checks."""
    text = _read_text(root / ".gitignore")
    return {
        line.strip()
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }


def collect_live_repository_signals(root: Path) -> dict[str, Any]:
    """Collect live worktree, runtime-artifact, and generated-evidence signals."""
    benchmark_result_paths = [
        format_path(root / relative_path, root)
        for relative_path in BENCHMARK_RESULT_ARTIFACTS
        if (root / relative_path).exists()
    ]
    snapshot = git_worktree_snapshot(root)
    dirty_paths = list_signal_paths(snapshot, "modified_paths") + list_signal_paths(
        snapshot, "untracked_paths"
    )
    benchmark_result_paths.extend(
        path for path in dirty_paths if _is_local_by_default_benchmark_result_path(path)
    )
    runtime_artifact_paths = [
        path
        for path in dirty_paths
        if is_runtime_artifact_path(path)
        and not _is_local_by_default_benchmark_result_path(path)
    ]
    release_evidence_paths = [
        path for path in dirty_paths if is_release_evidence_path(path)
    ]
    snapshot["runtime_artifact_paths"] = runtime_artifact_paths
    snapshot["release_evidence_paths"] = release_evidence_paths
    snapshot["benchmark_result_paths"] = _ordered_unique_paths(benchmark_result_paths)
    snapshot["current_branch"] = git_current_branch(root)
    snapshot["current_head"] = git_current_head(root)
    snapshot.update(generated_artifact_policy_snapshot(root))
    return snapshot


def _read_text(path: Path) -> str:
    """Read text for optional documentation checks."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""
