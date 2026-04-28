"""Decision, payload, and render helpers for alpha release preflight."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping
from typing import NamedTuple
from typing import Protocol
from typing import Sequence
from urllib.parse import urlparse


DEFAULT_BRANCH = "codex/qa-z-bootstrap"
DEFAULT_REPOSITORY_FULL_NAME = "qazedhq/qa-z"
DEFAULT_REPOSITORY_URL = "https://github.com/qazedhq/qa-z.git"
DEFAULT_TAG = "v0.9.8-alpha"


class CheckResult(NamedTuple):
    name: str
    status: str
    detail: str


class GitHubRepositoryTarget(NamedTuple):
    full_name: str
    api_url: str


class RemoteDecision(NamedTuple):
    remote_path: str
    remote_blocker: str | None


class RemoteRefEvidence(NamedTuple):
    ref_count: int
    ref_sample: list[str]
    head_count: int
    tag_count: int
    ref_kinds: list[str]


class PreflightResult(Protocol):
    checks: Sequence[CheckResult]

    @property
    def exit_code(self) -> int: ...

    @property
    def summary(self) -> str: ...

    @property
    def by_name(self) -> dict[str, CheckResult]: ...


def _detail_field(detail: str, field: str) -> str | None:
    marker = f"{field}="
    for part in detail.split(";"):
        stripped = part.strip()
        if stripped.startswith(marker):
            value = stripped[len(marker) :].strip()
            return value or None
    return None


def _detail_int_field(detail: str, field: str) -> int | None:
    value = _detail_field(detail, field)
    if value is None:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def _detail_list_field(detail: str, field: str) -> list[str]:
    value = _detail_field(detail, field)
    if value is None:
        return []
    return [item for item in value.split(",") if item]


def tracked_generated_artifact_fields_from_result(
    result: "PreflightResult",
) -> dict[str, object]:
    generated_check = result.by_name.get("generated_artifacts_untracked")
    if generated_check is None:
        return {}

    tracked_paths = _detail_list_field(
        generated_check.detail, "tracked_generated_artifact_paths"
    )
    local_only_paths = _detail_list_field(
        generated_check.detail, "generated_local_only_tracked_paths"
    )
    local_by_default_paths = _detail_list_field(
        generated_check.detail, "generated_local_by_default_tracked_paths"
    )
    tracked_count = _detail_int_field(
        generated_check.detail, "tracked_generated_artifact_count"
    )
    if tracked_count is None and tracked_paths:
        tracked_count = len(tracked_paths)
    local_only_count = _detail_int_field(
        generated_check.detail, "generated_local_only_tracked_count"
    )
    if local_only_count is None and local_only_paths:
        local_only_count = len(local_only_paths)
    local_by_default_count = _detail_int_field(
        generated_check.detail, "generated_local_by_default_tracked_count"
    )
    if local_by_default_count is None and local_by_default_paths:
        local_by_default_count = len(local_by_default_paths)

    fields: dict[str, object] = {}
    if isinstance(tracked_count, int):
        fields["tracked_generated_artifact_count"] = tracked_count
    if tracked_paths:
        fields["tracked_generated_artifact_paths"] = tracked_paths
    if isinstance(local_only_count, int):
        fields["generated_local_only_tracked_count"] = local_only_count
    if local_only_paths:
        fields["generated_local_only_tracked_paths"] = local_only_paths
    if isinstance(local_by_default_count, int):
        fields["generated_local_by_default_tracked_count"] = local_by_default_count
    if local_by_default_paths:
        fields["generated_local_by_default_tracked_paths"] = local_by_default_paths
    return fields


def github_repository_metadata_from_result(
    result: "PreflightResult",
) -> dict[str, object]:
    github_check = result.by_name.get("github_repository")
    if github_check is None:
        return {}

    metadata: dict[str, object] = {}
    status_code = _status_code_from_detail(github_check.detail)
    if status_code is not None:
        metadata["repository_http_status"] = status_code

    visibility = _detail_field(github_check.detail, "visibility")
    if visibility is not None:
        metadata["repository_visibility"] = visibility

    archived = _detail_field(github_check.detail, "archived")
    if archived is not None:
        metadata["repository_archived"] = archived == "yes"

    default_branch = _detail_field(github_check.detail, "default_branch")
    if default_branch is not None:
        metadata["repository_default_branch"] = default_branch
    return metadata


def repository_default_branch_from_result(result: "PreflightResult") -> str | None:
    default_branch = github_repository_metadata_from_result(result).get(
        "repository_default_branch"
    )
    if isinstance(default_branch, str) and default_branch:
        return default_branch
    return None


def repository_probe_state_from_result(result: "PreflightResult") -> str | None:
    github_check = result.by_name.get("github_repository")
    if github_check is None:
        return None
    if github_check.status == "skipped":
        return "skipped"
    status_code = _status_code_from_detail(github_check.detail)
    if github_check.status in {"passed", "failed"} and isinstance(status_code, int):
        return "probed"
    return None


def existing_preflight_payload(output_path: Path | None) -> dict[str, object] | None:
    if output_path is None or not output_path.exists():
        return None
    try:
        raw = output_path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def parse_utc_timestamp(value: str) -> datetime | None:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_github_repository_target(
    repository_url: str,
) -> GitHubRepositoryTarget | None:
    url = repository_url.strip().rstrip("/")
    if url.startswith("git@github.com:"):
        path = url.removeprefix("git@github.com:")
    elif url.lower().startswith("github.com/"):
        path = url[len("github.com/") :]
    elif url.lower().startswith("www.github.com/"):
        path = url[len("www.github.com/") :]
    else:
        parsed = urlparse(url)
        host = parsed.hostname
        if host is None:
            host = parsed.netloc.rsplit("@", 1)[-1].split(":", 1)[0]
        host = host.lower()
        if host != "github.com":
            return None
        path = parsed.path.lstrip("/")
    if path.endswith(".git"):
        path = path[:-4]
    parts = [part for part in path.split("/") if part]
    if len(parts) != 2:
        return None
    owner, repo = parts
    full_name = f"{owner}/{repo}"
    return GitHubRepositoryTarget(
        full_name, f"https://api.github.com/repos/{full_name}"
    )


def repository_urls_match(actual_url: str, expected_url: str) -> bool:
    actual_target = parse_github_repository_target(actual_url)
    expected_target = parse_github_repository_target(expected_url)
    if actual_target is None or expected_target is None:
        return actual_url.strip().rstrip("/") == expected_url.strip().rstrip("/")
    return actual_target.full_name.lower() == expected_target.full_name.lower()


def repository_identity_matches_payload(
    payload: Mapping[str, object],
    *,
    repository_target: GitHubRepositoryTarget | None,
    repository_url: str,
) -> bool:
    prior_target = payload.get("repository_target")
    if (
        repository_target is not None
        and isinstance(prior_target, str)
        and prior_target == repository_target.full_name
    ):
        return True

    prior_url = payload.get("repository_url")
    if not isinstance(prior_url, str) or not prior_url:
        return False
    if prior_url == repository_url:
        return True

    prior_target_from_url = parse_github_repository_target(prior_url)
    if repository_target is None or prior_target_from_url is None:
        return False
    return prior_target_from_url.full_name == repository_target.full_name


def last_known_probe_snapshot(
    payload: Mapping[str, object] | None,
    *,
    repository_target: GitHubRepositoryTarget | None,
    repository_url: str,
) -> dict[str, object]:
    if not isinstance(payload, Mapping):
        return {}
    if not repository_identity_matches_payload(
        payload,
        repository_target=repository_target,
        repository_url=repository_url,
    ):
        return {}

    probe_state = payload.get("repository_probe_state")
    probe_basis = payload.get("repository_probe_basis")
    if not (
        probe_state == "probed"
        or (probe_state == "skipped" and probe_basis == "last_known")
    ):
        return {}

    probe_generated_at = payload.get("repository_probe_generated_at")
    if not isinstance(probe_generated_at, str) or not probe_generated_at:
        return {}

    snapshot: dict[str, object] = {
        "repository_probe_basis": "last_known",
        "repository_probe_generated_at": probe_generated_at,
    }
    repository_http_status = payload.get("repository_http_status")
    if isinstance(repository_http_status, int) and repository_http_status > 0:
        snapshot["repository_http_status"] = repository_http_status
    for metadata_key in (
        "repository_visibility",
        "repository_archived",
        "repository_default_branch",
    ):
        metadata_value = payload.get(metadata_key)
        if isinstance(metadata_value, str) and metadata_value:
            snapshot[metadata_key] = metadata_value
        if isinstance(metadata_value, bool):
            snapshot[metadata_key] = metadata_value
    return snapshot


def probe_freshness_fields(
    *,
    generated_at: str,
    probe_state: object,
    probe_basis: object,
    probe_generated_at: object,
) -> dict[str, object]:
    if not isinstance(probe_generated_at, str) or not probe_generated_at:
        return {}

    generated_at_dt = parse_utc_timestamp(generated_at)
    probe_generated_at_dt = parse_utc_timestamp(probe_generated_at)
    if generated_at_dt is None or probe_generated_at_dt is None:
        return {}

    age_seconds = max(0.0, (generated_at_dt - probe_generated_at_dt).total_seconds())
    age_hours = int(age_seconds // 3600)
    if probe_state == "probed":
        return {
            "repository_probe_freshness": "current",
            "repository_probe_age_hours": age_hours,
        }
    if probe_state == "skipped" and probe_basis == "last_known":
        return {
            "repository_probe_freshness": "stale"
            if age_hours > 24
            else "carried_forward",
            "repository_probe_age_hours": age_hours,
        }
    return {}


def publish_strategy_for_result(
    result: "PreflightResult", *, skip_remote: bool
) -> str | None:
    remote_decision = classify_remote_decision(result, skip_remote=skip_remote)
    if remote_decision.remote_path == "direct_publish":
        return "push_default_branch"
    if remote_decision.remote_path == "release_pr":
        return "push_release_branch"
    if remote_decision.remote_path == "skipped":
        origin_state = origin_state_from_result(result)
        if origin_state == "configured":
            return "remote_preflight"
        if origin_state == "missing":
            return "bootstrap_origin"
    return None


def publish_checklist_for_result(
    result: "PreflightResult",
    *,
    repository_url: str,
    expected_repository: str,
    skip_remote: bool,
    expected_tag: str,
    expected_branch: str,
    allow_dirty: bool,
) -> list[str]:
    publish_strategy = publish_strategy_for_result(result, skip_remote=skip_remote)
    publish_branch = repository_default_branch_from_result(result) or "main"
    if publish_strategy == "push_default_branch":
        return [
            f"Push the validated release baseline to {publish_branch} with `git push -u origin HEAD:{publish_branch}`.",
            "Wait for remote CI: `test`, `Build package artifacts`, `Smoke test built package artifacts`, and `qa-z` must pass.",
            f"Create and verify `{expected_tag}` from the validated default branch, then `git push origin {expected_tag}`.",
        ]
    if publish_strategy == "push_release_branch":
        return [
            f"Push the release branch with `git push -u origin {expected_branch}`.",
            f"Open the release PR titled `Release QA-Z {expected_tag}` with body `docs/releases/{expected_tag}-pr.md`.",
            "Wait for remote CI: `test`, `Build package artifacts`, `Smoke test built package artifacts`, and `qa-z` must pass.",
            "Tag only after the release PR merges and the validated baseline is on the default branch.",
        ]
    if publish_strategy == "bootstrap_origin":
        rerun_command = preflight_rerun_command(
            repository_url=repository_url,
            expected_repository=expected_repository,
            expected_origin_url=repository_url,
            allow_dirty=allow_dirty,
        )
        return [
            f"Add the intended origin with `git remote add origin {repository_url}`.",
            f"Rerun remote preflight with `{rerun_command}`.",
        ]
    return []


def release_path_state_for_result(
    result: "PreflightResult", *, skip_remote: bool
) -> str | None:
    remote_decision = classify_remote_decision(result, skip_remote=skip_remote)
    if remote_decision.remote_path == "direct_publish":
        return "remote_direct_publish"
    if remote_decision.remote_path == "release_pr":
        return "remote_release_pr"
    if remote_decision.remote_path == "skipped":
        origin_state = origin_state_from_result(result)
        if origin_state == "missing":
            return "local_only_bootstrap_origin"
        if origin_state == "configured":
            return "local_only_remote_preflight"
        return "local_only_preflight"

    blocker_state = {
        "release_tag_exists": "blocked_existing_tag",
        "existing_refs_present": "blocked_existing_refs",
        "origin_mismatch": "blocked_origin_alignment",
        "origin_target_mismatch": "blocked_origin_alignment",
        "origin_present": "blocked_origin_alignment",
        "repository_target_mismatch": "blocked_repository",
        "repository_not_public": "blocked_repository",
        "repository_archived": "blocked_repository",
        "repository_unavailable": "blocked_repository",
        "repository_missing": "blocked_repository",
        "remote_unreachable": "blocked_remote_access",
    }
    if remote_decision.remote_blocker is not None:
        return blocker_state.get(
            remote_decision.remote_blocker, "blocked_remote_publish"
        )
    return "blocked_remote_publish"


def release_path_state_from_payload(payload: Mapping[str, object]) -> str | None:
    state = payload.get("release_path_state")
    if isinstance(state, str) and state:
        return state

    remote_path = payload.get("remote_path")
    if not isinstance(remote_path, str) or not remote_path:
        return None
    if remote_path == "direct_publish":
        return "remote_direct_publish"
    if remote_path == "release_pr":
        return "remote_release_pr"
    if remote_path == "skipped":
        origin_state = payload.get("origin_state")
        if origin_state == "missing":
            return "local_only_bootstrap_origin"
        if origin_state == "configured":
            return "local_only_remote_preflight"
        return "local_only_preflight"

    blocker_state = {
        "release_tag_exists": "blocked_existing_tag",
        "existing_refs_present": "blocked_existing_refs",
        "origin_mismatch": "blocked_origin_alignment",
        "origin_target_mismatch": "blocked_origin_alignment",
        "origin_present": "blocked_origin_alignment",
        "repository_target_mismatch": "blocked_repository",
        "repository_not_public": "blocked_repository",
        "repository_archived": "blocked_repository",
        "repository_unavailable": "blocked_repository",
        "repository_missing": "blocked_repository",
        "remote_unreachable": "blocked_remote_access",
    }
    blocker = payload.get("remote_blocker")
    if isinstance(blocker, str) and blocker:
        return blocker_state.get(blocker, "blocked_remote_publish")
    return "blocked_remote_publish"


def _status_code_from_detail(detail: str) -> int | None:
    lowered = detail.lower()
    status_match = re.search(r"status_code=(\d{3})\b", lowered)
    if status_match is not None:
        return int(status_match.group(1))
    http_marker = "http "
    if http_marker in lowered:
        suffix = lowered.split(http_marker, 1)[1]
        digits = "".join(char for char in suffix[:3] if char.isdigit())
        if len(digits) == 3:
            return int(digits)
    if "repository not found" in lowered:
        return 404
    return None


def repository_http_status_from_result(result: "PreflightResult") -> int | None:
    github_check = result.by_name.get("github_repository")
    if github_check is not None:
        detail_status = _status_code_from_detail(github_check.detail)
        if detail_status is not None:
            return detail_status
        if github_check.status == "passed":
            return 200
    return None


def remote_readiness_for_result(
    result: "PreflightResult", *, skip_remote: bool
) -> str | None:
    remote_decision = classify_remote_decision(result, skip_remote=skip_remote)
    if remote_decision.remote_path == "direct_publish":
        return "ready_for_direct_publish"
    if remote_decision.remote_path == "release_pr":
        return "ready_for_release_pr"
    if remote_decision.remote_path == "skipped":
        origin_state = origin_state_from_result(result)
        if origin_state == "missing":
            return "needs_origin_bootstrap"
        if origin_state == "configured":
            return "ready_for_remote_checks"
        return None

    readiness_by_blocker = {
        "origin_mismatch": "needs_origin_alignment",
        "origin_present": "needs_origin_expectation",
        "origin_target_mismatch": "needs_origin_alignment",
        "repository_target_mismatch": "needs_repository_alignment",
        "repository_missing": "needs_repository_bootstrap",
        "repository_unavailable": "needs_repository_access",
        "repository_not_public": "needs_repository_public_access",
        "repository_archived": "needs_repository_unarchive",
        "remote_unreachable": "needs_remote_access",
        "existing_refs_present": "needs_release_pr_path",
        "release_tag_exists": "blocked_existing_tag",
    }
    blocker = remote_decision.remote_blocker
    if blocker is None:
        return None
    return readiness_by_blocker.get(blocker, "blocked_remote_publish")


def origin_state_from_result(result: "PreflightResult") -> str | None:
    origin_absent_check = result.by_name.get("origin_absent")
    if origin_absent_check is not None:
        return "missing" if origin_absent_check.status == "passed" else "configured"

    origin_check = result.by_name.get("origin_matches_expected")
    if origin_check is None:
        return None
    return "missing" if origin_remote_is_missing(result) else "configured"


def actual_origin_url_from_result(result: "PreflightResult") -> str | None:
    origin_absent_check = result.by_name.get("origin_absent")
    if origin_absent_check is not None:
        detail = origin_absent_check.detail.strip()
        if (
            origin_absent_check.status == "failed"
            and detail
            and detail != "origin exists"
        ):
            return detail
        return None

    origin_check = result.by_name.get("origin_matches_expected")
    if origin_check is None:
        return None
    detail = origin_check.detail.strip()
    if not detail:
        return None
    if origin_check.status == "passed":
        return detail
    lowered = detail.lower()
    if "no such remote" in lowered or "not configured" in lowered:
        return None
    marker = ", got "
    if marker in detail:
        return detail.split(marker, 1)[1].strip()
    return None


def remote_ref_names(refs: str) -> list[str]:
    names: list[str] = []
    for line in refs.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if parts:
            names.append(parts[-1])
    return names


def remote_ref_kind_summary(
    ref_names: Sequence[str],
) -> tuple[int, int, list[str]]:
    head_count = sum(1 for name in ref_names if name.startswith("refs/heads/"))
    tag_count = sum(1 for name in ref_names if name.startswith("refs/tags/"))
    other_count = len(ref_names) - head_count - tag_count
    ref_kinds: list[str] = []
    if head_count:
        ref_kinds.append("heads")
    if tag_count:
        ref_kinds.append("tags")
    if other_count:
        ref_kinds.append("other")
    return head_count, tag_count, ref_kinds


def format_remote_ref_detail(prefix: str, ref_names: Sequence[str]) -> str:
    ref_count = len(ref_names)
    head_count, tag_count, ref_kinds = remote_ref_kind_summary(ref_names)
    ref_sample = ", ".join(ref_names[:3])
    if not ref_sample:
        return prefix
    kinds_text = ",".join(ref_kinds) if ref_kinds else "none"
    return (
        f"{prefix} (ref_count={ref_count}; head_count={head_count}; "
        f"tag_count={tag_count}; kinds={kinds_text}; sample={ref_sample})"
    )


def remote_ref_evidence_from_result(
    result: "PreflightResult",
) -> RemoteRefEvidence | None:
    remote_empty = result.by_name.get("remote_empty")
    if remote_empty is None:
        return None
    detail = remote_empty.detail
    count_match = re.search(r"ref_count=(\d+)", detail)
    sample_match = re.search(r"sample=([^)]+)", detail)
    head_count_match = re.search(r"head_count=(\d+)", detail)
    tag_count_match = re.search(r"tag_count=(\d+)", detail)
    kinds_match = re.search(r"kinds=([^;^)]+)", detail)
    if (
        count_match is None
        or sample_match is None
        or head_count_match is None
        or tag_count_match is None
        or kinds_match is None
    ):
        return None
    ref_sample = [
        item.strip() for item in sample_match.group(1).split(",") if item.strip()
    ]
    ref_kinds = [
        item.strip() for item in kinds_match.group(1).split(",") if item.strip()
    ]
    return RemoteRefEvidence(
        int(count_match.group(1)),
        ref_sample,
        int(head_count_match.group(1)),
        int(tag_count_match.group(1)),
        ref_kinds,
    )


def origin_remote_is_missing(result: "PreflightResult") -> bool:
    origin_check = result.by_name.get("origin_matches_expected")
    if origin_check is not None and origin_check.status == "failed":
        detail = origin_check.detail.lower()
        if "no such remote" in detail or "not configured" in detail:
            return True

    origin_absent_check = result.by_name.get("origin_absent")
    return origin_absent_check is not None and origin_absent_check.status == "passed"


def utc_timestamp() -> str:
    """Return a compact UTC timestamp for generated preflight evidence."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def next_actions_for_result(
    result: "PreflightResult",
    *,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    expected_origin_url: str | None = None,
    expected_tag: str = DEFAULT_TAG,
    skip_remote: bool = False,
) -> list[str]:
    failed_checks = [check for check in result.checks if check.status == "failed"]
    failed = {check.name for check in failed_checks}
    actions: list[str] = []
    tracked_generated_fields = tracked_generated_artifact_fields_from_result(result)
    local_only_paths = tracked_generated_fields.get(
        "generated_local_only_tracked_paths"
    )
    local_by_default_paths = tracked_generated_fields.get(
        "generated_local_by_default_tracked_paths"
    )
    repository_target = parse_github_repository_target(repository_url)
    repository_targets_expected = (
        repository_target is not None
        and repository_target.full_name.lower() == expected_repository.lower()
    )
    if "worktree_clean" in failed:
        actions.append(
            (
                "Commit, stash, or intentionally rerun with --allow-dirty before "
                "publishing; the worktree_clean check must be clean for release."
            )
        )
    if "generated_artifacts_untracked" in failed:
        if isinstance(local_only_paths, list) and local_only_paths:
            actions.append(
                (
                    "Remove or untrack tracked local-only generated artifacts before "
                    f"publish: {', '.join(local_only_paths)}."
                )
            )
        if isinstance(local_by_default_paths, list) and local_by_default_paths:
            actions.append(
                (
                    "Decide whether tracked benchmark result evidence stays local or "
                    "is intentionally frozen with surrounding context before publish: "
                    f"{', '.join(local_by_default_paths)}."
                )
            )
        if not actions or actions[-1].startswith(
            "Commit, stash, or intentionally rerun with --allow-dirty"
        ):
            actions.append(
                (
                    "Remove or untrack tracked generated artifacts before publish; "
                    "keep benchmark result evidence only when it is intentionally "
                    "frozen with surrounding context."
                )
            )
    remote_decision = classify_remote_decision(result, skip_remote=skip_remote)
    publish_strategy = publish_strategy_for_result(result, skip_remote=skip_remote)
    publish_branch = repository_default_branch_from_result(result) or "main"
    if result.exit_code == 0 and publish_strategy == "push_default_branch":
        actions.append(
            (
                "Remote is empty and ready for direct publish; push the release "
                f"baseline to {publish_branch}, wait for remote CI, and tag only after the "
                "validated default branch is green."
            )
        )
    if result.exit_code == 0 and publish_strategy == "push_release_branch":
        actions.append(
            (
                "Remote bootstrap refs are present and the release PR path is ready; "
                "push codex/qa-z-bootstrap, open the release PR, and wait for remote "
                "CI before tagging."
            )
        )
    if remote_decision.remote_blocker == "repository_target_mismatch" and (
        "github_repository" in failed and not repository_targets_expected
    ):
        actions.append(
            (
                f"Set --repository-url to https://github.com/{expected_repository}.git, "
                "or update --expected-repository if a different public GitHub "
                "repository is intentional."
            )
        )
    elif remote_decision.remote_blocker in {
        "repository_missing",
        "repository_unavailable",
        "repository_not_public",
        "repository_archived",
        "remote_unreachable",
    }:
        actions.append(
            (
                f"Create or expose the public GitHub repository {expected_repository}, "
                f"then rerun remote preflight for {repository_url}."
            )
        )
    if remote_decision.remote_blocker in {
        "origin_mismatch",
        "origin_target_mismatch",
    }:
        actions.append(
            (
                "Set origin to the intended repository URL, then rerun preflight "
                "with --expected-origin-url."
            )
        )
    if remote_decision.remote_blocker == "origin_present":
        actions.append(
            (
                "Origin is already configured; rerun preflight with "
                "--expected-origin-url if that remote is intentional."
            )
        )
    if (
        remote_decision.remote_path == "skipped"
        and origin_state_from_result(result) == "missing"
        and "worktree_clean" not in failed
    ):
        actions.append(
            (
                "Configure origin and rerun remote preflight before public "
                "publish; skip-remote only defers the remote bootstrap step."
            )
        )
    if (
        remote_decision.remote_path == "skipped"
        and origin_state_from_result(result) == "configured"
        and "worktree_clean" not in failed
        and expected_origin_url is not None
    ):
        actions.append(
            (
                f"Run remote preflight against {expected_repository} before public "
                "publish; skip-remote only covers local readiness."
            )
        )
    if remote_decision.remote_blocker == "release_tag_exists":
        actions.append(
            (
                f"Remote release tag {expected_tag} already exists; inspect the "
                "existing tag before publishing a new alpha tag."
            )
        )
    elif remote_decision.remote_blocker == "existing_refs_present":
        actions.append(
            (
                "Remote already has refs; choose the release PR path with "
                "--allow-existing-refs or publish to an empty repository."
            )
        )
    return actions


def preflight_rerun_command(
    *,
    repository_url: str,
    expected_repository: str,
    expected_origin_url: str | None = None,
    skip_remote: bool = False,
    allow_existing_refs: bool = False,
    allow_dirty: bool = False,
) -> str:
    command = ["python", "scripts/alpha_release_preflight.py"]
    if skip_remote:
        command.append("--skip-remote")
    else:
        command.extend(["--repository-url", repository_url])
        if expected_repository != DEFAULT_REPOSITORY_FULL_NAME:
            command.extend(["--expected-repository", expected_repository])
        if allow_existing_refs:
            command.append("--allow-existing-refs")
    if expected_origin_url:
        if skip_remote and "--repository-url" not in command:
            command.extend(["--repository-url", repository_url])
        command.extend(["--expected-origin-url", expected_origin_url])
    if allow_dirty:
        command.append("--allow-dirty")
    command.append("--json")
    return " ".join(command)


def next_commands_for_result(
    result: "PreflightResult",
    *,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    expected_origin_url: str | None = None,
    expected_tag: str = DEFAULT_TAG,
    skip_remote: bool = False,
    allow_existing_refs: bool = False,
    allow_dirty: bool = False,
) -> list[str]:
    remote_decision = classify_remote_decision(result, skip_remote=skip_remote)
    publish_strategy = publish_strategy_for_result(result, skip_remote=skip_remote)
    publish_branch = repository_default_branch_from_result(result) or "main"
    commands: list[str] = []
    if result.exit_code == 0 and publish_strategy == "push_default_branch":
        commands.append(f"git push -u origin HEAD:{publish_branch}")
        return commands
    if result.exit_code == 0 and publish_strategy == "push_release_branch":
        commands.append(f"git push -u origin {DEFAULT_BRANCH}")
        return commands
    if remote_decision.remote_blocker == "origin_target_mismatch":
        intended_origin_url = repository_url
        origin_command = (
            f"git remote add origin {intended_origin_url}"
            if origin_remote_is_missing(result)
            else f"git remote set-url origin {intended_origin_url}"
        )
        commands.append(origin_command)
        commands.append(
            preflight_rerun_command(
                repository_url=repository_url,
                expected_repository=expected_repository,
                expected_origin_url=intended_origin_url,
                skip_remote=skip_remote,
                allow_existing_refs=allow_existing_refs,
                allow_dirty=allow_dirty,
            )
        )
    elif (
        remote_decision.remote_path == "skipped"
        and origin_state_from_result(result) == "missing"
        and result.by_name.get("worktree_clean", CheckResult("", "", "")).status
        != "failed"
    ):
        intended_origin_url = repository_url
        commands.append(f"git remote add origin {intended_origin_url}")
        commands.append(
            preflight_rerun_command(
                repository_url=repository_url,
                expected_repository=expected_repository,
                expected_origin_url=intended_origin_url,
                skip_remote=False,
                allow_existing_refs=allow_existing_refs,
                allow_dirty=allow_dirty,
            )
        )
    elif (
        remote_decision.remote_path == "skipped"
        and origin_state_from_result(result) == "configured"
        and result.by_name.get("worktree_clean", CheckResult("", "", "")).status
        != "failed"
    ):
        remote_origin_url = expected_origin_url or actual_origin_url_from_result(result)
        commands.append(
            preflight_rerun_command(
                repository_url=repository_url,
                expected_repository=expected_repository,
                expected_origin_url=remote_origin_url,
                skip_remote=False,
                allow_existing_refs=allow_existing_refs,
                allow_dirty=allow_dirty,
            )
        )
    elif remote_decision.remote_blocker == "origin_present":
        actual_origin_url = actual_origin_url_from_result(result)
        if actual_origin_url:
            commands.append(
                preflight_rerun_command(
                    repository_url=repository_url,
                    expected_repository=expected_repository,
                    expected_origin_url=actual_origin_url,
                    skip_remote=skip_remote,
                    allow_existing_refs=allow_existing_refs,
                    allow_dirty=allow_dirty,
                )
            )
    elif remote_decision.remote_blocker == "origin_mismatch" and expected_origin_url:
        origin_command = (
            f"git remote add origin {expected_origin_url}"
            if origin_remote_is_missing(result)
            else f"git remote set-url origin {expected_origin_url}"
        )
        commands.append(origin_command)
        commands.append(
            preflight_rerun_command(
                repository_url=repository_url,
                expected_repository=expected_repository,
                expected_origin_url=expected_origin_url,
                skip_remote=skip_remote,
                allow_existing_refs=allow_existing_refs,
                allow_dirty=allow_dirty,
            )
        )
    elif remote_decision.remote_blocker == "existing_refs_present":
        commands.append(f"git ls-remote --refs {repository_url}")
        commands.append(
            preflight_rerun_command(
                repository_url=repository_url,
                expected_repository=expected_repository,
                expected_origin_url=expected_origin_url,
                skip_remote=False,
                allow_existing_refs=True,
                allow_dirty=allow_dirty,
            )
        )
    elif remote_decision.remote_blocker == "release_tag_exists":
        commands.append(
            f"git ls-remote --refs {repository_url} refs/tags/{expected_tag}"
        )
    elif remote_decision.remote_blocker == "repository_target_mismatch":
        corrected_repository_url = f"https://github.com/{expected_repository}.git"
        commands.append(
            preflight_rerun_command(
                repository_url=corrected_repository_url,
                expected_repository=expected_repository,
                expected_origin_url=expected_origin_url,
                skip_remote=False,
                allow_existing_refs=allow_existing_refs,
                allow_dirty=allow_dirty,
            )
        )
    return commands


def yes_no(value: object) -> str:
    return "yes" if value is True else "no"


def result_payload(
    result: "PreflightResult",
    *,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    expected_origin_url: str | None = None,
    expected_branch: str = DEFAULT_BRANCH,
    expected_tag: str = DEFAULT_TAG,
    skip_remote: bool = False,
    allow_existing_refs: bool = False,
    allow_dirty: bool = False,
    prior_payload: Mapping[str, object] | None = None,
) -> dict[str, object]:
    failed_checks = [check.name for check in result.checks if check.status == "failed"]
    passed_count = sum(1 for check in result.checks if check.status == "passed")
    failed_count = len(failed_checks)
    skipped_count = sum(1 for check in result.checks if check.status == "skipped")
    generated_at = utc_timestamp()
    repository_target = parse_github_repository_target(repository_url)
    expected_origin_target = (
        parse_github_repository_target(expected_origin_url)
        if isinstance(expected_origin_url, str) and expected_origin_url
        else None
    )
    remote_decision = classify_remote_decision(result, skip_remote=skip_remote)
    remote_readiness = remote_readiness_for_result(result, skip_remote=skip_remote)
    release_path_state = release_path_state_for_result(result, skip_remote=skip_remote)
    publish_strategy = publish_strategy_for_result(result, skip_remote=skip_remote)
    carried_probe_snapshot = last_known_probe_snapshot(
        prior_payload,
        repository_target=repository_target,
        repository_url=repository_url,
    )
    next_actions = next_actions_for_result(
        result,
        repository_url=repository_url,
        expected_repository=expected_repository,
        expected_origin_url=expected_origin_url,
        expected_tag=expected_tag,
        skip_remote=skip_remote,
    )
    publish_checklist = publish_checklist_for_result(
        result,
        repository_url=repository_url,
        expected_repository=expected_repository,
        skip_remote=skip_remote,
        expected_tag=expected_tag,
        expected_branch=expected_branch,
        allow_dirty=allow_dirty,
    )
    github_repository_metadata = github_repository_metadata_from_result(result)
    repository_http_status = repository_http_status_from_result(result)
    payload = {
        "summary": result.summary,
        "exit_code": result.exit_code,
        "generated_at": generated_at,
        "check_count": len(result.checks),
        "passed_count": passed_count,
        "failed_count": failed_count,
        "skipped_count": skipped_count,
        "failed_checks": failed_checks,
        "repository_url": repository_url,
        "expected_repository": expected_repository,
        "expected_origin_url": expected_origin_url,
        "expected_branch": expected_branch,
        "expected_tag": expected_tag,
        "skip_remote": skip_remote,
        "allow_existing_refs": allow_existing_refs,
        "allow_dirty": allow_dirty,
        "checks": [
            {
                "name": check.name,
                "status": check.status,
                "detail": check.detail,
            }
            for check in result.checks
        ],
        "remote_path": remote_decision.remote_path,
    }
    payload.update(tracked_generated_artifact_fields_from_result(result))
    if isinstance(repository_http_status, int) and repository_http_status > 0:
        payload["repository_http_status"] = repository_http_status
    repository_probe_state = repository_probe_state_from_result(result)
    if repository_probe_state is None and skip_remote:
        repository_probe_state = "skipped"
    if isinstance(repository_probe_state, str) and repository_probe_state:
        payload["repository_probe_state"] = repository_probe_state
        if repository_probe_state == "probed":
            payload["repository_probe_generated_at"] = generated_at
        elif carried_probe_snapshot:
            payload["repository_probe_basis"] = "last_known"
            payload["repository_probe_generated_at"] = carried_probe_snapshot[
                "repository_probe_generated_at"
            ]
    for metadata_key in (
        "repository_visibility",
        "repository_archived",
        "repository_default_branch",
    ):
        metadata_value = github_repository_metadata.get(metadata_key)
        if isinstance(metadata_value, str) and metadata_value:
            payload[metadata_key] = metadata_value
        if isinstance(metadata_value, bool):
            payload[metadata_key] = metadata_value
    if "repository_http_status" not in payload:
        carried_http_status = carried_probe_snapshot.get("repository_http_status")
        if isinstance(carried_http_status, int) and carried_http_status > 0:
            payload["repository_http_status"] = carried_http_status
    for metadata_key in (
        "repository_visibility",
        "repository_archived",
        "repository_default_branch",
    ):
        if metadata_key in payload:
            continue
        metadata_value = carried_probe_snapshot.get(metadata_key)
        if isinstance(metadata_value, str) and metadata_value:
            payload[metadata_key] = metadata_value
        if isinstance(metadata_value, bool):
            payload[metadata_key] = metadata_value
    payload.update(
        probe_freshness_fields(
            generated_at=generated_at,
            probe_state=payload.get("repository_probe_state"),
            probe_basis=payload.get("repository_probe_basis"),
            probe_generated_at=payload.get("repository_probe_generated_at"),
        )
    )
    if release_path_state is not None:
        payload["release_path_state"] = release_path_state
    if remote_readiness is not None:
        payload["remote_readiness"] = remote_readiness
    if publish_strategy is not None:
        payload["publish_strategy"] = publish_strategy
    if publish_checklist:
        payload["publish_checklist"] = publish_checklist
    if next_actions:
        payload["next_actions"] = next_actions
    next_commands = next_commands_for_result(
        result,
        repository_url=repository_url,
        expected_repository=expected_repository,
        expected_origin_url=expected_origin_url,
        expected_tag=expected_tag,
        skip_remote=skip_remote,
        allow_existing_refs=allow_existing_refs,
        allow_dirty=allow_dirty,
    )
    if next_commands:
        payload["next_commands"] = next_commands
    origin_state = origin_state_from_result(result)
    if origin_state is not None:
        payload["origin_state"] = origin_state
    actual_origin_url = actual_origin_url_from_result(result)
    if actual_origin_url is not None:
        payload["actual_origin_url"] = actual_origin_url
        actual_origin_target = parse_github_repository_target(actual_origin_url)
        if actual_origin_target is not None:
            payload["actual_origin_target"] = actual_origin_target.full_name
    remote_ref_evidence = remote_ref_evidence_from_result(result)
    if remote_ref_evidence is not None:
        payload["remote_ref_count"] = remote_ref_evidence.ref_count
        payload["remote_ref_head_count"] = remote_ref_evidence.head_count
        payload["remote_ref_tag_count"] = remote_ref_evidence.tag_count
        payload["remote_ref_kinds"] = remote_ref_evidence.ref_kinds
        payload["remote_ref_sample"] = remote_ref_evidence.ref_sample
    if repository_target is not None:
        payload["repository_target"] = repository_target.full_name
    if expected_origin_target is not None:
        payload["expected_origin_target"] = expected_origin_target.full_name
    if remote_decision.remote_blocker is not None:
        payload["remote_blocker"] = remote_decision.remote_blocker
    return payload


def render_preflight_human(payload: dict[str, object]) -> str:
    lines: list[str] = []
    generated_at = payload.get("generated_at")
    if isinstance(generated_at, str) and generated_at:
        lines.append(f"Generated at: {generated_at}")

    repository_url = payload.get("repository_url")
    repository_target = payload.get("repository_target")
    target_parts: list[str] = []
    if isinstance(repository_target, str) and repository_target:
        target_parts.append(f"repository={repository_target}")
    if isinstance(repository_url, str) and repository_url:
        target_parts.append(f"url={repository_url}")
    repository_probe_state = payload.get("repository_probe_state")
    if isinstance(repository_probe_state, str) and repository_probe_state:
        target_parts.append(f"repo_probe={repository_probe_state}")
    repository_probe_basis = payload.get("repository_probe_basis")
    if isinstance(repository_probe_basis, str) and repository_probe_basis:
        target_parts.append(f"repo_probe_basis={repository_probe_basis}")
    repository_probe_generated_at = payload.get("repository_probe_generated_at")
    if isinstance(repository_probe_generated_at, str) and repository_probe_generated_at:
        target_parts.append(f"repo_probe_at={repository_probe_generated_at}")
    repository_probe_freshness = payload.get("repository_probe_freshness")
    if isinstance(repository_probe_freshness, str) and repository_probe_freshness:
        target_parts.append(f"repo_probe_freshness={repository_probe_freshness}")
    repository_probe_age_hours = payload.get("repository_probe_age_hours")
    if isinstance(repository_probe_age_hours, int) and repository_probe_age_hours >= 0:
        target_parts.append(f"repo_probe_age_hours={repository_probe_age_hours}")
    repository_http_status = payload.get("repository_http_status")
    if isinstance(repository_http_status, int) and repository_http_status > 0:
        target_parts.append(f"repo_http={repository_http_status}")
    repository_visibility = payload.get("repository_visibility")
    if isinstance(repository_visibility, str) and repository_visibility:
        target_parts.append(f"repo_visibility={repository_visibility}")
    repository_archived = payload.get("repository_archived")
    if isinstance(repository_archived, bool):
        target_parts.append(f"repo_archived={'yes' if repository_archived else 'no'}")
    repository_default_branch = payload.get("repository_default_branch")
    if isinstance(repository_default_branch, str) and repository_default_branch:
        target_parts.append(f"repo_default_branch={repository_default_branch}")
    if target_parts:
        lines.append(f"Target: {'; '.join(target_parts)}")

    expected_origin_url = payload.get("expected_origin_url")
    expected_origin_target = payload.get("expected_origin_target")
    actual_origin_url = payload.get("actual_origin_url")
    actual_origin_target = payload.get("actual_origin_target")
    origin_state = payload.get("origin_state")
    origin_parts: list[str] = []
    if isinstance(expected_origin_target, str) and expected_origin_target:
        origin_parts.append(f"expected={expected_origin_target}")
        origin_parts.append(f"url={expected_origin_url}")
    elif isinstance(expected_origin_url, str) and expected_origin_url:
        origin_parts.append(f"expected_url={expected_origin_url}")
    else:
        origin_parts.append("expected=(unset)")
    if isinstance(actual_origin_target, str) and actual_origin_target:
        origin_parts.append(f"actual_target={actual_origin_target}")
    if isinstance(actual_origin_url, str) and actual_origin_url:
        origin_parts.append(f"actual={actual_origin_url}")
    elif origin_state == "missing":
        origin_parts.append("actual=missing")
    elif origin_state == "configured":
        origin_parts.append("actual=configured")
    lines.append(f"Origin: {'; '.join(origin_parts)}")

    mode_parts = []
    expected_branch_value = payload.get("expected_branch")
    if isinstance(expected_branch_value, str) and expected_branch_value:
        mode_parts.append(f"branch={expected_branch_value}")
    expected_tag_value = payload.get("expected_tag")
    if isinstance(expected_tag_value, str) and expected_tag_value:
        mode_parts.append(f"tag={expected_tag_value}")
    mode_parts.extend(
        [
            f"skip_remote={yes_no(payload.get('skip_remote'))}",
            f"allow_existing_refs={yes_no(payload.get('allow_existing_refs'))}",
            f"allow_dirty={yes_no(payload.get('allow_dirty'))}",
        ]
    )
    lines.append(f"Mode: {'; '.join(mode_parts)}")
    decision_parts = []
    remote_path = payload.get("remote_path")
    if isinstance(remote_path, str) and remote_path:
        decision_parts.append(f"remote_path={remote_path}")
    release_path_state = release_path_state_from_payload(payload)
    if isinstance(release_path_state, str) and release_path_state:
        decision_parts.append(f"release_path_state={release_path_state}")
    remote_readiness = payload.get("remote_readiness")
    if isinstance(remote_readiness, str) and remote_readiness:
        decision_parts.append(f"remote_readiness={remote_readiness}")
    publish_strategy = payload.get("publish_strategy")
    if isinstance(publish_strategy, str) and publish_strategy:
        decision_parts.append(f"publish_strategy={publish_strategy}")
    remote_blocker = payload.get("remote_blocker")
    if isinstance(remote_blocker, str) and remote_blocker:
        decision_parts.append(f"remote_blocker={remote_blocker}")
    remote_ref_count = payload.get("remote_ref_count")
    if isinstance(remote_ref_count, int) and remote_ref_count > 0:
        decision_parts.append(f"remote_ref_count={remote_ref_count}")
    remote_ref_head_count = payload.get("remote_ref_head_count")
    if isinstance(remote_ref_head_count, int) and remote_ref_head_count >= 0:
        decision_parts.append(f"remote_ref_head_count={remote_ref_head_count}")
    remote_ref_tag_count = payload.get("remote_ref_tag_count")
    if isinstance(remote_ref_tag_count, int) and remote_ref_tag_count >= 0:
        decision_parts.append(f"remote_ref_tag_count={remote_ref_tag_count}")
    remote_ref_kinds = payload.get("remote_ref_kinds")
    if isinstance(remote_ref_kinds, list):
        ref_kinds = ",".join(
            item for item in remote_ref_kinds if isinstance(item, str) and item
        )
        if ref_kinds:
            decision_parts.append(f"remote_ref_kinds={ref_kinds}")
    if decision_parts:
        lines.append(f"Decision: {'; '.join(decision_parts)}")
    remote_ref_sample = payload.get("remote_ref_sample")
    if isinstance(remote_ref_sample, list) and remote_ref_sample:
        sample_text = ", ".join(
            item for item in remote_ref_sample if isinstance(item, str) and item
        )
        if sample_text:
            lines.append(f"Remote refs: {sample_text}")

    checks = payload.get("checks")
    if isinstance(checks, list):
        for item in checks:
            if not isinstance(item, dict):
                continue
            name = item.get("name")
            status = item.get("status")
            detail = item.get("detail")
            if not isinstance(name, str) or not isinstance(status, str):
                continue
            detail_text = detail if isinstance(detail, str) and detail else "no detail"
            lines.append(f"[{status.upper()}] {name}: {detail_text}")

    next_commands = payload.get("next_commands")
    if isinstance(next_commands, list) and next_commands:
        lines.append("Next commands:")
        for command in next_commands:
            if isinstance(command, str) and command:
                lines.append(f"- {command}")

    publish_checklist = payload.get("publish_checklist")
    if isinstance(publish_checklist, list) and publish_checklist:
        lines.append("Publish checklist:")
        for item in publish_checklist:
            if isinstance(item, str) and item:
                lines.append(f"- {item}")

    summary = payload.get("summary")
    if isinstance(summary, str) and summary:
        lines.append(summary)
    return "\n".join(lines)


def classify_remote_decision(
    result: "PreflightResult", *, skip_remote: bool
) -> RemoteDecision:
    by_name = result.by_name

    origin_target_check = by_name.get("origin_target_matches_repository")
    if origin_target_check is not None and origin_target_check.status == "failed":
        return RemoteDecision("blocked", "origin_target_mismatch")

    origin_check = by_name.get("origin_matches_expected")
    if origin_check is not None and origin_check.status == "failed":
        return RemoteDecision("blocked", "origin_mismatch")

    origin_absent_check = by_name.get("origin_absent")
    if origin_absent_check is not None and origin_absent_check.status == "failed":
        return RemoteDecision("blocked", "origin_present")

    if skip_remote:
        return RemoteDecision("skipped", None)

    github_check = by_name.get("github_repository")
    if github_check is not None and github_check.status == "failed":
        detail = github_check.detail.lower()
        if (
            _status_code_from_detail(github_check.detail) == 404
            or "not found" in detail
        ):
            return RemoteDecision("blocked", "repository_missing")
        if "expected " in detail or "github.com/" in detail:
            return RemoteDecision("blocked", "repository_target_mismatch")
        if "not public" in detail:
            return RemoteDecision("blocked", "repository_not_public")
        if "archived" in detail:
            return RemoteDecision("blocked", "repository_archived")
        return RemoteDecision("blocked", "repository_unavailable")

    remote_check = by_name.get("remote_reachable")
    if remote_check is not None and remote_check.status == "failed":
        detail = remote_check.detail.lower()
        if "repository not found" in detail:
            return RemoteDecision("blocked", "repository_missing")
        return RemoteDecision("blocked", "remote_unreachable")

    remote_empty = by_name.get("remote_empty")
    if remote_empty is not None:
        detail = remote_empty.detail.lower()
        if remote_empty.status == "passed":
            if "existing refs allowed for release pr path" in detail:
                return RemoteDecision("release_pr", None)
            if "reachable empty repository" in detail:
                return RemoteDecision("direct_publish", None)
        elif remote_empty.status == "failed":
            if "remote release tag already exists" in detail:
                return RemoteDecision("blocked", "release_tag_exists")
            if "remote already has refs" in detail:
                return RemoteDecision("blocked", "existing_refs_present")

    return RemoteDecision("blocked", None)
