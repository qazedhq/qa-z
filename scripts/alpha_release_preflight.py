"""Local preflight checks for publishing QA-Z v0.9.8-alpha."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable
from typing import NamedTuple
from typing import Sequence
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request
from urllib.request import urlopen


DEFAULT_BRANCH = "codex/qa-z-bootstrap"
DEFAULT_REPOSITORY_FULL_NAME = "qazedhq/qa-z"
DEFAULT_REPOSITORY_URL = "https://github.com/qazedhq/qa-z.git"
DEFAULT_TAG = "v0.9.8-alpha"

GENERATED_ARTIFACT_PATHS = (
    ".qa-z",
    "benchmarks/results",
    "dist",
    "build",
    "src/qa_z.egg-info",
)


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


def next_actions_for_result(
    result: PreflightResult,
    *,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    expected_tag: str = DEFAULT_TAG,
) -> list[str]:
    failed_checks = [check for check in result.checks if check.status == "failed"]
    failed = {check.name for check in failed_checks}
    actions: list[str] = []
    repository_target = parse_github_repository_target(repository_url)
    repository_targets_expected = (
        repository_target is not None
        and repository_target.full_name.lower() == expected_repository.lower()
    )
    if "github_repository" in failed and not repository_targets_expected:
        actions.append(
            (
                f"Set --repository-url to https://github.com/{expected_repository}.git, "
                "or update --expected-repository if a different public GitHub "
                "repository is intentional."
            )
        )
    elif {"github_repository", "remote_reachable"} & failed:
        actions.append(
            (
                f"Create or expose the public GitHub repository {expected_repository}, "
                f"then rerun remote preflight for {repository_url}."
            )
        )
    if {"origin_matches_expected", "origin_target_matches_repository"} & failed:
        actions.append(
            (
                "Set origin to the intended repository URL, then rerun preflight "
                "with --expected-origin-url."
            )
        )
    remote_empty = next(
        (check for check in failed_checks if check.name == "remote_empty"), None
    )
    if remote_empty is not None and "remote release tag already exists" in (
        remote_empty.detail
    ):
        actions.append(
            (
                f"Remote release tag {expected_tag} already exists; inspect the "
                "existing tag before publishing a new alpha tag."
            )
        )
    elif remote_empty is not None:
        actions.append(
            (
                "Remote already has refs; choose the release PR path with "
                "--allow-existing-refs or publish to an empty repository."
            )
        )
    return actions


def result_payload(
    result: PreflightResult,
    *,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    expected_origin_url: str | None = None,
    expected_branch: str = DEFAULT_BRANCH,
    expected_tag: str = DEFAULT_TAG,
    skip_remote: bool = False,
    allow_existing_refs: bool = False,
    allow_dirty: bool = False,
) -> dict[str, object]:
    failed_checks = [check.name for check in result.checks if check.status == "failed"]
    passed_count = sum(1 for check in result.checks if check.status == "passed")
    failed_count = len(failed_checks)
    skipped_count = sum(1 for check in result.checks if check.status == "skipped")
    return {
        "summary": result.summary,
        "exit_code": result.exit_code,
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
        **(
            {
                "next_actions": next_actions_for_result(
                    result,
                    repository_url=repository_url,
                    expected_repository=expected_repository,
                    expected_tag=expected_tag,
                )
            }
            if result.exit_code
            else {}
        ),
    }


Runner = Callable[[Sequence[str], Path], tuple[int, str, str]]
GitHubMetadataFetcher = Callable[[str], GitHubMetadataResult]


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


def parse_github_repository_target(
    repository_url: str,
) -> GitHubRepositoryTarget | None:
    url = repository_url.strip().rstrip("/")
    if url.startswith("git@github.com:"):
        path = url.removeprefix("git@github.com:")
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
    if metadata.status_code != 200:
        detail = (
            metadata.error or f"{target.api_url} returned HTTP {metadata.status_code}"
        )
        return CheckResult("github_repository", "failed", detail)

    full_name = str(metadata.data.get("full_name", ""))
    visibility = str(metadata.data.get("visibility", "")).lower()
    is_private = metadata.data.get("private")
    archived = metadata.data.get("archived")
    if full_name.lower() != target.full_name.lower():
        return CheckResult(
            "github_repository",
            "failed",
            f"expected {expected_repository}, got {full_name or 'unknown repository'}",
        )
    if is_private is True or visibility != "public":
        return CheckResult(
            "github_repository",
            "failed",
            f"{target.full_name} is not public",
        )
    if archived is True:
        return CheckResult(
            "github_repository",
            "failed",
            f"{target.full_name} is archived",
        )
    return CheckResult("github_repository", "passed", f"{target.full_name} is public")


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
        detail = tracked or stderr.strip() or "git ls-files failed"
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
                first_ref = refs.splitlines()[0]
                release_tag_ref = f"refs/tags/{expected_tag}"
                remote_tag_ref = next(
                    (
                        line
                        for line in refs.splitlines()
                        if line.split()[-1] == release_tag_ref
                    ),
                    "",
                )
                if remote_tag_ref:
                    checks.append(
                        CheckResult(
                            "remote_empty",
                            "failed",
                            f"remote release tag already exists: {remote_tag_ref}",
                        )
                    )
                elif allow_existing_refs:
                    checks.append(
                        CheckResult(
                            "remote_empty",
                            "passed",
                            (f"existing refs allowed for release PR path: {first_ref}"),
                        )
                    )
                else:
                    checks.append(
                        CheckResult(
                            "remote_empty",
                            "failed",
                            f"remote already has refs: {first_ref}",
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
    )
    payload_json = json.dumps(payload, indent=2)
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload_json}\n", encoding="utf-8")

    if args.json:
        print(payload_json)
    else:
        for check in result.checks:
            print(f"[{check.status.upper()}] {check.name}: {check.detail}")
        print(result.summary)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
