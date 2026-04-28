"""Local preflight checks for publishing QA-Z v0.9.8-alpha."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable
from typing import NamedTuple
from typing import Sequence
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

from qa_z.subprocess_env import build_tool_subprocess_env


DEFAULT_BRANCH = "codex/qa-z-bootstrap"
DEFAULT_REPOSITORY_FULL_NAME = "qazedhq/qa-z"
DEFAULT_REPOSITORY_URL = "https://github.com/qazedhq/qa-z.git"
DEFAULT_TAG = "v0.9.8-alpha"

GENERATED_ARTIFACT_PATHS = (
    ".qa-z",
    ".mypy_cache",
    ".mypy_cache_safe",
    ".ruff_cache",
    ".ruff_cache_safe",
    "%TEMP%",
    "benchmarks/results",
    "benchmarks/results-*",
    "benchmarks/minlock-*",
    "dist",
    "build",
    "tmp_*",
    "src/qa_z.egg-info",
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
            f"Unable to load worktree commit plan support module: {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class CheckResult(NamedTuple):
    name: str
    status: str
    detail: str


class GitHubRepositoryTarget(NamedTuple):
    full_name: str
    api_url: str


class GitHubMetadataResult(NamedTuple):
    status_code: int
    data: dict[str, object]
    error: str


class RemoteDecision(NamedTuple):
    remote_path: str
    remote_blocker: str | None


class RemoteRefEvidence(NamedTuple):
    ref_count: int
    ref_sample: list[str]
    head_count: int
    tag_count: int
    ref_kinds: list[str]


class PreflightResult:
    def __init__(self, checks: Sequence[CheckResult]) -> None:
        self.checks = list(checks)

    @property
    def exit_code(self) -> int:
        return 1 if any(check.status == "failed" for check in self.checks) else 0

    @property
    def summary(self) -> str:
        if self.exit_code:
            return "release preflight failed"
        return "release preflight passed"

    @property
    def by_name(self) -> dict[str, CheckResult]:
        return {check.name: check for check in self.checks}


Runner = Callable[[Sequence[str], Path], tuple[int, str, str]]
GitHubMetadataFetcher = Callable[[str], GitHubMetadataResult]


def _load_alpha_release_preflight_evidence_module():
    module_path = Path(__file__).with_name("alpha_release_preflight_evidence.py")
    cached = sys.modules.get("alpha_release_preflight_evidence")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == module_path.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "alpha_release_preflight_evidence", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load alpha release preflight evidence module: {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_ALPHA_RELEASE_PREFLIGHT_EVIDENCE = _load_alpha_release_preflight_evidence_module()
_detail_field = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE._detail_field
github_repository_metadata_from_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.github_repository_metadata_from_result
)
repository_default_branch_from_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.repository_default_branch_from_result
)
repository_probe_state_from_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.repository_probe_state_from_result
)
existing_preflight_payload = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.existing_preflight_payload
)
parse_utc_timestamp = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.parse_utc_timestamp
parse_github_repository_target = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.parse_github_repository_target
)
repository_urls_match = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.repository_urls_match
repository_identity_matches_payload = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.repository_identity_matches_payload
)
last_known_probe_snapshot = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.last_known_probe_snapshot
probe_freshness_fields = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.probe_freshness_fields
publish_strategy_for_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.publish_strategy_for_result
)
publish_checklist_for_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.publish_checklist_for_result
)
release_path_state_for_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.release_path_state_for_result
)
release_path_state_from_payload = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.release_path_state_from_payload
)
_status_code_from_detail = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE._status_code_from_detail
repository_http_status_from_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.repository_http_status_from_result
)
remote_readiness_for_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.remote_readiness_for_result
)
origin_state_from_result = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.origin_state_from_result
actual_origin_url_from_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.actual_origin_url_from_result
)
remote_ref_names = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.remote_ref_names
remote_ref_kind_summary = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.remote_ref_kind_summary
format_remote_ref_detail = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.format_remote_ref_detail
remote_ref_evidence_from_result = (
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.remote_ref_evidence_from_result
)
origin_remote_is_missing = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.origin_remote_is_missing
utc_timestamp = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.utc_timestamp
next_actions_for_result = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.next_actions_for_result
preflight_rerun_command = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.preflight_rerun_command
next_commands_for_result = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.next_commands_for_result
yes_no = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.yes_no

_WORKTREE_COMMIT_PLAN_SUPPORT = _load_worktree_commit_plan_support_module()
generated_artifact_bucket = _WORKTREE_COMMIT_PLAN_SUPPORT.generated_artifact_bucket
is_local_only_generated_artifact = (
    _WORKTREE_COMMIT_PLAN_SUPPORT.is_local_only_generated_artifact
)
is_local_by_default_generated_artifact = (
    _WORKTREE_COMMIT_PLAN_SUPPORT.is_local_by_default_generated_artifact
)


def unique_strings(values: Sequence[str]) -> list[str]:
    strings: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value and value not in seen:
            strings.append(value)
            seen.add(value)
    return strings


def tracked_generated_artifact_fields(tracked_output: str) -> dict[str, object]:
    tracked_paths = unique_strings(
        [
            generated_artifact_bucket(line.strip())
            for line in tracked_output.splitlines()
            if line.strip()
        ]
    )
    local_only_paths = [
        path for path in tracked_paths if is_local_only_generated_artifact(path)
    ]
    local_by_default_paths = [
        path for path in tracked_paths if is_local_by_default_generated_artifact(path)
    ]
    return {
        "tracked_generated_artifact_count": len(tracked_paths),
        "tracked_generated_artifact_paths": tracked_paths,
        "generated_local_only_tracked_count": len(local_only_paths),
        "generated_local_only_tracked_paths": local_only_paths,
        "generated_local_by_default_tracked_count": len(local_by_default_paths),
        "generated_local_by_default_tracked_paths": local_by_default_paths,
    }


def tracked_generated_artifact_detail(tracked_output: str) -> str:
    fields = tracked_generated_artifact_fields(tracked_output)
    parts = [
        f"tracked_generated_artifact_count={fields['tracked_generated_artifact_count']}",
    ]
    tracked_paths = fields["tracked_generated_artifact_paths"]
    if tracked_paths:
        parts.append(
            "tracked_generated_artifact_paths=" + ",".join(tracked_paths)  # type: ignore[arg-type]
        )
    parts.append(
        "generated_local_only_tracked_count="
        f"{fields['generated_local_only_tracked_count']}"
    )
    local_only_paths = fields["generated_local_only_tracked_paths"]
    if local_only_paths:
        parts.append(
            "generated_local_only_tracked_paths=" + ",".join(local_only_paths)  # type: ignore[arg-type]
        )
    parts.append(
        "generated_local_by_default_tracked_count="
        f"{fields['generated_local_by_default_tracked_count']}"
    )
    local_by_default_paths = fields["generated_local_by_default_tracked_paths"]
    if local_by_default_paths:
        parts.append(
            "generated_local_by_default_tracked_paths="
            + ",".join(local_by_default_paths)  # type: ignore[arg-type]
        )
    return "; ".join(parts)


def _sync_preflight_evidence_module():
    _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.utc_timestamp = utc_timestamp
    return _ALPHA_RELEASE_PREFLIGHT_EVIDENCE


def _result_payload(*args, **kwargs):
    """Render a preflight payload after synchronizing timestamp helpers."""
    return _sync_preflight_evidence_module().result_payload(*args, **kwargs)


result_payload = _result_payload
render_preflight_human = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.render_preflight_human
classify_remote_decision = _ALPHA_RELEASE_PREFLIGHT_EVIDENCE.classify_remote_decision


def subprocess_runner(command: Sequence[str], cwd: Path) -> tuple[int, str, str]:
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
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def check_git(
    name: str,
    command: Sequence[str],
    repo_root: Path,
    runner: Runner,
) -> tuple[int, str, str]:
    try:
        return runner(command, repo_root)
    except FileNotFoundError as exc:
        return 127, "", str(exc)


def fetch_github_metadata(api_url: str) -> GitHubMetadataResult:
    request = Request(
        api_url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "qa-z-release-preflight",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
            if not isinstance(data, dict):
                return GitHubMetadataResult(response.status, {}, "unexpected API body")
            return GitHubMetadataResult(response.status, data, "")
    except HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace").strip()
        return GitHubMetadataResult(exc.code, {}, body or str(exc))
    except (OSError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        return GitHubMetadataResult(0, {}, str(exc))


def check_github_repository(
    repository_url: str,
    github_metadata_fetcher: GitHubMetadataFetcher,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
) -> CheckResult:
    target = parse_github_repository_target(repository_url)
    if target is None:
        return CheckResult(
            "github_repository",
            "failed",
            f"repository URL must point to github.com/{expected_repository}",
        )

    if target.full_name.lower() != expected_repository.lower():
        return CheckResult(
            "github_repository",
            "failed",
            f"expected {expected_repository}, got {target.full_name}",
        )

    metadata = github_metadata_fetcher(target.api_url)
    metadata_parts = [f"status_code={metadata.status_code}"]
    visibility = str(metadata.data.get("visibility", "")).lower()
    if visibility:
        metadata_parts.append(f"visibility={visibility}")
    archived = metadata.data.get("archived")
    if isinstance(archived, bool):
        metadata_parts.append(f"archived={'yes' if archived else 'no'}")
    default_branch = str(metadata.data.get("default_branch", "")).strip()
    if default_branch:
        metadata_parts.append(f"default_branch={default_branch}")
    if metadata.status_code != 200:
        detail = (
            metadata.error or f"{target.api_url} returned HTTP {metadata.status_code}"
        )
        detail = "; ".join([*metadata_parts, detail])
        return CheckResult("github_repository", "failed", detail)

    full_name = str(metadata.data.get("full_name", ""))
    is_private = metadata.data.get("private")
    if full_name.lower() != target.full_name.lower():
        return CheckResult(
            "github_repository",
            "failed",
            "; ".join(
                [
                    *metadata_parts,
                    f"expected {expected_repository}, got {full_name or 'unknown repository'}",
                ]
            ),
        )
    if is_private is True or visibility != "public":
        return CheckResult(
            "github_repository",
            "failed",
            "; ".join([*metadata_parts, f"{target.full_name} is not public"]),
        )
    if archived is True:
        return CheckResult(
            "github_repository",
            "failed",
            "; ".join([*metadata_parts, f"{target.full_name} is archived"]),
        )
    return CheckResult(
        "github_repository",
        "passed",
        "; ".join([*metadata_parts, f"{target.full_name} is public"]),
    )


def run_preflight(
    repo_root: Path,
    *,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_origin_url: str | None = None,
    expected_branch: str = DEFAULT_BRANCH,
    expected_tag: str = DEFAULT_TAG,
    skip_remote: bool = False,
    allow_existing_refs: bool = False,
    allow_dirty: bool = False,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    runner: Runner = subprocess_runner,
    github_metadata_fetcher: GitHubMetadataFetcher = fetch_github_metadata,
) -> PreflightResult:
    checks: list[CheckResult] = []

    exit_code, stdout, stderr = check_git(
        "current_branch", ("git", "branch", "--show-current"), repo_root, runner
    )
    branch = stdout.strip()
    if exit_code == 0 and branch == expected_branch:
        checks.append(CheckResult("current_branch", "passed", branch))
    else:
        detail = stderr.strip() or branch or f"expected {expected_branch}"
        checks.append(CheckResult("current_branch", "failed", detail))

    exit_code, stdout, stderr = check_git(
        "worktree_clean", ("git", "status", "--short"), repo_root, runner
    )
    status = stdout.strip()
    if exit_code == 0 and not status:
        checks.append(CheckResult("worktree_clean", "passed", "no tracked changes"))
    elif exit_code == 0 and allow_dirty:
        checks.append(CheckResult("worktree_clean", "passed", "dirty worktree allowed"))
    else:
        detail = status or stderr.strip() or "git status failed"
        checks.append(CheckResult("worktree_clean", "failed", detail))

    exit_code, stdout, stderr = check_git(
        "origin_absent", ("git", "remote", "get-url", "origin"), repo_root, runner
    )
    origin_url = stdout.strip()
    if exit_code != 0 and expected_origin_url is None:
        checks.append(
            CheckResult("origin_absent", "passed", "origin is not configured")
        )
    elif exit_code != 0:
        detail = stderr.strip() or "origin is not configured"
        checks.append(
            CheckResult(
                "origin_matches_expected",
                "failed",
                f"expected origin {expected_origin_url}, got {detail}",
            )
        )
    elif expected_origin_url is None:
        detail = origin_url or stderr.strip() or "origin exists"
        checks.append(CheckResult("origin_absent", "failed", detail))
    elif repository_urls_match(origin_url, expected_origin_url):
        checks.append(CheckResult("origin_matches_expected", "passed", origin_url))
    else:
        detail = f"expected origin {expected_origin_url}, got {origin_url}"
        checks.append(CheckResult("origin_matches_expected", "failed", detail))

    exit_code, stdout, stderr = check_git(
        "release_tag_absent",
        ("git", "tag", "--list", expected_tag),
        repo_root,
        runner,
    )
    tag_output = stdout.strip()
    if exit_code == 0 and not tag_output:
        checks.append(CheckResult("release_tag_absent", "passed", expected_tag))
    else:
        detail = tag_output or stderr.strip() or f"{expected_tag} lookup failed"
        checks.append(CheckResult("release_tag_absent", "failed", detail))

    exit_code, stdout, stderr = check_git(
        "generated_artifacts_untracked",
        ("git", "ls-files", *GENERATED_ARTIFACT_PATHS),
        repo_root,
        runner,
    )
    tracked = stdout.strip()
    if exit_code == 0 and not tracked:
        checks.append(
            CheckResult(
                "generated_artifacts_untracked",
                "passed",
                "no generated release artifacts are tracked",
            )
        )
    else:
        detail = tracked_generated_artifact_detail(tracked)
        if not tracked.strip():
            detail = stderr.strip() or "git ls-files failed"
        checks.append(CheckResult("generated_artifacts_untracked", "failed", detail))

    exit_code, stdout, stderr = check_git(
        "head_resolves", ("git", "rev-parse", "HEAD"), repo_root, runner
    )
    head = stdout.strip()
    if exit_code == 0 and head:
        checks.append(CheckResult("head_resolves", "passed", head))
    else:
        detail = stderr.strip() or "HEAD did not resolve"
        checks.append(CheckResult("head_resolves", "failed", detail))

    if expected_origin_url is not None:
        repository_target = parse_github_repository_target(repository_url)
        origin_target = parse_github_repository_target(expected_origin_url)
        if repository_target is None or origin_target is None:
            checks.append(
                CheckResult(
                    "origin_target_matches_repository",
                    "failed",
                    "expected origin URL and repository URL must both target GitHub",
                )
            )
        elif repository_target.full_name.lower() == origin_target.full_name.lower():
            checks.append(
                CheckResult(
                    "origin_target_matches_repository",
                    "passed",
                    repository_target.full_name,
                )
            )
        else:
            checks.append(
                CheckResult(
                    "origin_target_matches_repository",
                    "failed",
                    (
                        f"expected origin target {origin_target.full_name} does not "
                        f"match repository target {repository_target.full_name}"
                    ),
                )
            )

    if skip_remote:
        checks.append(
            CheckResult("github_repository", "skipped", "remote check skipped")
        )
        checks.append(
            CheckResult("remote_reachable", "skipped", "remote check skipped")
        )
        checks.append(CheckResult("remote_empty", "skipped", "remote check skipped"))
    else:
        checks.append(
            check_github_repository(
                repository_url,
                github_metadata_fetcher,
                expected_repository=expected_repository,
            )
        )
        exit_code, stdout, stderr = check_git(
            "remote_reachable",
            ("git", "ls-remote", "--refs", repository_url),
            repo_root,
            runner,
        )
        refs = stdout.strip()
        if exit_code == 0:
            checks.append(CheckResult("remote_reachable", "passed", repository_url))
            if refs:
                ref_names = remote_ref_names(refs)
                release_tag_ref = f"refs/tags/{expected_tag}"
                remote_tag_ref = next(
                    (ref_name for ref_name in ref_names if ref_name == release_tag_ref),
                    "",
                )
                if remote_tag_ref:
                    ref_sample = [
                        remote_tag_ref,
                        *[name for name in ref_names if name != remote_tag_ref],
                    ]
                    checks.append(
                        CheckResult(
                            "remote_empty",
                            "failed",
                            format_remote_ref_detail(
                                "remote release tag already exists",
                                ref_sample,
                            ),
                        )
                    )
                elif allow_existing_refs:
                    checks.append(
                        CheckResult(
                            "remote_empty",
                            "passed",
                            format_remote_ref_detail(
                                "existing refs allowed for release PR path",
                                ref_names,
                            ),
                        )
                    )
                else:
                    checks.append(
                        CheckResult(
                            "remote_empty",
                            "failed",
                            format_remote_ref_detail(
                                "remote already has refs", ref_names
                            ),
                        )
                    )
            else:
                checks.append(
                    CheckResult(
                        "remote_empty",
                        "passed",
                        "reachable empty repository",
                    )
                )
        else:
            detail = (
                stderr.strip() or stdout.strip() or f"{repository_url} not reachable"
            )
            checks.append(CheckResult("remote_reachable", "failed", detail))

    return PreflightResult(checks)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check local and remote prerequisites before publishing QA-Z alpha."
    )
    parser.add_argument(
        "--repository-url",
        default=DEFAULT_REPOSITORY_URL,
        help=f"Git repository URL to test. Defaults to {DEFAULT_REPOSITORY_URL}.",
    )
    parser.add_argument(
        "--expected-repository",
        default=DEFAULT_REPOSITORY_FULL_NAME,
        help=(
            "Expected GitHub owner/repository full name. "
            f"Defaults to {DEFAULT_REPOSITORY_FULL_NAME}."
        ),
    )
    parser.add_argument(
        "--expected-origin-url",
        default=None,
        help=(
            "Require a configured origin remote matching this URL. "
            "Omit before the GitHub repository exists."
        ),
    )
    parser.add_argument(
        "--expected-branch",
        default=DEFAULT_BRANCH,
        help=f"Expected local branch. Defaults to {DEFAULT_BRANCH}.",
    )
    parser.add_argument(
        "--expected-tag",
        default=DEFAULT_TAG,
        help=f"Release tag that must not exist yet. Defaults to {DEFAULT_TAG}.",
    )
    parser.add_argument(
        "--skip-remote",
        action="store_true",
        help=(
            "Skip GitHub metadata and git ls-remote checks. "
            "Use only before the GitHub repository exists."
        ),
    )
    parser.add_argument(
        "--allow-existing-refs",
        action="store_true",
        help=(
            "Allow a reachable public repository that already has refs. "
            "Use only for the existing-default-branch release PR path."
        ),
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow local changes while developing the preflight itself.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable preflight evidence as JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path where the JSON evidence payload should be written.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    prior_payload = existing_preflight_payload(args.output)
    result = run_preflight(
        Path.cwd(),
        repository_url=args.repository_url,
        expected_origin_url=args.expected_origin_url,
        expected_branch=args.expected_branch,
        expected_tag=args.expected_tag,
        skip_remote=args.skip_remote,
        allow_existing_refs=args.allow_existing_refs,
        allow_dirty=args.allow_dirty,
        expected_repository=args.expected_repository,
    )
    payload = result_payload(
        result,
        repository_url=args.repository_url,
        expected_repository=args.expected_repository,
        expected_origin_url=args.expected_origin_url,
        expected_branch=args.expected_branch,
        expected_tag=args.expected_tag,
        skip_remote=args.skip_remote,
        allow_existing_refs=args.allow_existing_refs,
        allow_dirty=args.allow_dirty,
        prior_payload=prior_payload,
    )
    payload_json = json.dumps(payload, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload_json}\n", encoding="utf-8")

    if args.json:
        print(payload_json)
    else:
        print(render_preflight_human(payload))
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
