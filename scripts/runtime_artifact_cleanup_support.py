"""Support helpers for deterministic runtime artifact cleanup."""

from __future__ import annotations

import importlib.util
import shutil
import sys
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Callable
from typing import Sequence


Runner = Callable[[Sequence[str], Path], tuple[int, str, str]]

LOCAL_ONLY_FIXED_CLEANUP_ROOTS = (Path(".qa-z"),)
LOCAL_BY_DEFAULT_FIXED_CLEANUP_ROOTS = (Path("benchmarks/results"),)
LOCAL_BY_DEFAULT_GLOB_PATTERNS = ("results-*",)


class CleanupCandidate(tuple):
    __slots__ = ()

    def __new__(cls, path: Path, policy_bucket: str):
        return super().__new__(cls, (path, policy_bucket))

    @property
    def path(self) -> Path:
        return self[0]

    @property
    def policy_bucket(self) -> str:
        return self[1]


def utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _load_worktree_commit_plan_support_module():
    module_path = Path(__file__).with_name("worktree_commit_plan_support.py")
    cached = sys.modules.get("worktree_commit_plan_support")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == module_path.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "worktree_commit_plan_support", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load worktree commit-plan support module: {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def worktree_generated_policy_paths(
    root: Path,
    *,
    runner: Runner,
) -> tuple[list[str], list[str]]:
    """Return helper-derived local-only and local-by-default runtime roots."""
    exit_code, stdout, stderr = runner(
        ("git", "status", "--short", "--ignored", "--untracked-files=all"),
        root,
    )
    if exit_code != 0:
        detail = stderr.strip() or stdout.strip() or "git status failed"
        raise RuntimeError(detail)
    module = _load_worktree_commit_plan_support_module()
    payload = module.analyze_status_lines(stdout.splitlines())
    local_only_paths = payload.get("generated_local_only_paths", [])
    local_by_default_paths = payload.get("generated_local_by_default_paths", [])
    if not isinstance(local_only_paths, list) or not isinstance(
        local_by_default_paths, list
    ):
        raise RuntimeError(
            "worktree commit-plan payload missing generated policy paths"
        )
    return (
        [str(path) for path in local_only_paths if isinstance(path, str)],
        [str(path) for path in local_by_default_paths if isinstance(path, str)],
    )


def _append_candidate_roots(
    root: Path,
    *,
    relative_paths: Sequence[str],
    policy_bucket: str,
    seen: set[str],
    candidates: list[CleanupCandidate],
) -> None:
    for relative_path in relative_paths:
        candidate = root / relative_path.rstrip("/")
        if not candidate.exists():
            continue
        normalized = normalize_relative_path(root, candidate)
        if normalized in seen:
            continue
        seen.add(normalized)
        candidates.append(CleanupCandidate(candidate, policy_bucket))


def candidate_cleanup_roots(root: Path, *, runner: Runner) -> list[CleanupCandidate]:
    """Return existing helper-derived policy-managed runtime artifact roots."""
    local_only_paths, local_by_default_paths = worktree_generated_policy_paths(
        root,
        runner=runner,
    )
    candidates: list[CleanupCandidate] = []
    seen: set[str] = set()
    _append_candidate_roots(
        root,
        relative_paths=local_only_paths,
        policy_bucket="local_only",
        seen=seen,
        candidates=candidates,
    )
    _append_candidate_roots(
        root,
        relative_paths=local_by_default_paths,
        policy_bucket="local_by_default",
        seen=seen,
        candidates=candidates,
    )
    return candidates


def normalize_relative_path(root: Path, path: Path) -> str:
    """Return one normalized repo-relative path or fail if it escapes the root."""
    resolved_root = root.resolve()
    resolved_path = path.resolve(strict=False)
    relative_path = resolved_path.relative_to(resolved_root)
    return relative_path.as_posix()


def candidate_kind(path: Path) -> str:
    return "directory" if path.is_dir() else "file"


def tracked_paths_under(root: Path, path: Path, runner: Runner) -> list[str]:
    """Return tracked git paths under one cleanup candidate root."""
    relative_path = normalize_relative_path(root, path)
    exit_code, stdout, stderr = runner(("git", "ls-files", "--", relative_path), root)
    if exit_code != 0:
        detail = stderr.strip() or stdout.strip() or "git ls-files failed"
        raise RuntimeError(detail)
    return [
        line.strip().replace("\\", "/") for line in stdout.splitlines() if line.strip()
    ]


def delete_candidate_root(path: Path) -> None:
    """Delete one file or directory candidate."""
    if path.is_dir():
        shutil.rmtree(path)
        return
    path.unlink()


def cleanup_reason(status: str) -> str:
    """Return a concise operator-facing reason for one cleanup status."""
    if status == "review_local_by_default":
        return "local-by-default benchmark evidence requires operator review"
    if status == "skipped_tracked":
        return "tracked paths present; cleanup will not delete this root"
    if status == "deleted":
        return "deleted local-only untracked runtime artifact root"
    return "local-only untracked runtime artifact root can be deleted with --apply"


def collect_cleanup_plan(
    root: Path,
    *,
    runner: Runner,
    apply: bool = False,
) -> dict[str, object]:
    """Collect or apply cleanup for local-only runtime artifact roots."""
    candidates: list[dict[str, object]] = []
    planned = 0
    review_local_by_default = 0
    skipped_tracked = 0
    deleted = 0
    for candidate in candidate_cleanup_roots(root, runner=runner):
        relative_path = normalize_relative_path(root, candidate.path)
        kind = candidate_kind(candidate.path)
        tracked_paths = tracked_paths_under(root, candidate.path, runner)
        if candidate.policy_bucket == "local_by_default":
            status = "review_local_by_default"
            review_local_by_default += 1
        elif tracked_paths:
            status = "skipped_tracked"
            skipped_tracked += 1
        elif apply:
            delete_candidate_root(candidate.path)
            status = "deleted"
            deleted += 1
        else:
            status = "planned"
            planned += 1
        candidates.append(
            {
                "path": relative_path,
                "kind": kind,
                "policy_bucket": candidate.policy_bucket,
                "status": status,
                "reason": cleanup_reason(status),
                "tracked_paths": tracked_paths,
            }
        )
    return {
        "kind": "qa_z.runtime_artifact_cleanup",
        "schema_version": 1,
        "generated_at": utc_timestamp(),
        "repo_root": str(root.resolve()),
        "mode": "apply" if apply else "dry-run",
        "candidates": candidates,
        "counts": {
            "planned": planned,
            "review_local_by_default": review_local_by_default,
            "skipped_tracked": skipped_tracked,
            "deleted": deleted,
        },
    }


def render_human(payload: dict[str, object]) -> str:
    """Render a concise human summary for runtime artifact cleanup."""
    raw_counts = payload.get("counts", {})
    counts = raw_counts if isinstance(raw_counts, dict) else {}
    candidates = payload.get("candidates", [])
    lines = [
        "QA-Z Runtime Artifact Cleanup",
        "",
        f"Mode: {payload.get('mode', 'dry-run')}",
        f"Planned deletions: {counts.get('planned', 0)}",
        (
            "Review-only local-by-default roots: "
            f"{counts.get('review_local_by_default', 0)}"
        ),
        f"Deleted roots: {counts.get('deleted', 0)}",
        f"Skipped tracked roots: {counts.get('skipped_tracked', 0)}",
    ]
    if isinstance(candidates, list) and candidates:
        lines.append("")
        lines.append("Candidates:")
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            line = (
                f"- {candidate.get('status', 'unknown')}: "
                f"{candidate.get('path', 'unknown')}"
            )
            reason = candidate.get("reason")
            if isinstance(reason, str) and reason:
                line += f" - {reason}"
            tracked_paths = candidate.get("tracked_paths", [])
            if isinstance(tracked_paths, list) and tracked_paths:
                preview = ", ".join(str(path) for path in tracked_paths[:2])
                line += f" (tracked: {preview})"
            lines.append(line)
    else:
        lines.extend(["", "Candidates:", "- none"])
    return "\n".join(lines).strip() + "\n"
