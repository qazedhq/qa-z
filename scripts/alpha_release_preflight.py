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
        if parsed.netloc.lower() != "github.com":
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
) -> CheckResult:
    target = parse_github_repository_target(repository_url)
    if target is None:
        return CheckResult(
            "github_repository",
            "skipped",
            "repository URL is not a github.com URL",
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
            f"expected {target.full_name}, got {full_name or 'unknown repository'}",
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
    expected_branch: str = DEFAULT_BRANCH,
    expected_tag: str = DEFAULT_TAG,
    skip_remote: bool = False,
    allow_dirty: bool = False,
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
    if exit_code != 0:
        checks.append(
            CheckResult("origin_absent", "passed", "origin is not configured")
        )
    else:
        detail = stdout.strip() or stderr.strip() or "origin exists"
        checks.append(CheckResult("origin_absent", "failed", detail))

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

    if skip_remote:
        checks.append(
            CheckResult("github_repository", "skipped", "remote check skipped")
        )
        checks.append(
            CheckResult("remote_reachable", "skipped", "remote check skipped")
        )
        checks.append(CheckResult("remote_empty", "skipped", "remote check skipped"))
    else:
        checks.append(check_github_repository(repository_url, github_metadata_fetcher))
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
                checks.append(
                    CheckResult(
                        "remote_empty",
                        "failed",
                        f"remote already has refs: {refs.splitlines()[0]}",
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
        help="Skip git ls-remote. Use only before the GitHub repository exists.",
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help="Allow local changes while developing the preflight itself.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = run_preflight(
        Path.cwd(),
        repository_url=args.repository_url,
        expected_branch=args.expected_branch,
        expected_tag=args.expected_tag,
        skip_remote=args.skip_remote,
        allow_dirty=args.allow_dirty,
    )
    for check in result.checks:
        print(f"[{check.status.upper()}] {check.name}: {check.detail}")
    print(result.summary)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
