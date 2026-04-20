"""Rebuild and verify the QA-Z alpha release bundle manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable
from typing import NamedTuple
from typing import Sequence


DEFAULT_BRANCH = "codex/qa-z-bootstrap"
DEFAULT_BUNDLE = Path("dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle")
DEFAULT_ARTIFACTS = (
    Path("dist/qa_z-0.9.8a0.tar.gz"),
    Path("dist/qa_z-0.9.8a0-py3-none-any.whl"),
)


class CheckResult(NamedTuple):
    name: str
    status: str
    detail: str


class BundleManifestResult(NamedTuple):
    summary: str
    exit_code: int
    payload: dict[str, object]


Runner = Callable[[Sequence[str], Path], tuple[int, str, str]]


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


def actual_path(repo_root: Path, path: Path) -> Path:
    if path.is_absolute():
        return path
    return repo_root / path


def command_detail(
    step: str,
    exit_code: int,
    stdout: str,
    stderr: str,
) -> str:
    output = (stderr or stdout).strip()
    if output:
        return f"{step} failed with exit {exit_code}: {output}"
    return f"{step} failed with exit {exit_code}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def finish_payload(
    *,
    checks: Sequence[CheckResult],
    branch: str,
    head: str,
    branch_head: str,
    bundle_path: Path,
    bundle_heads: Sequence[str],
    artifacts: dict[str, dict[str, object]],
) -> BundleManifestResult:
    exit_code = 1 if any(check.status == "failed" for check in checks) else 0
    summary = (
        "release bundle manifest failed"
        if exit_code
        else "release bundle manifest passed"
    )
    payload: dict[str, object] = {
        "summary": summary,
        "exit_code": exit_code,
        "branch": branch,
        "head": head,
        "branch_head": branch_head,
        "bundle_path": str(bundle_path),
        "bundle_heads": list(bundle_heads),
        "checks": [
            {
                "name": check.name,
                "status": check.status,
                "detail": check.detail,
            }
            for check in checks
        ],
        "artifacts": artifacts,
    }
    return BundleManifestResult(summary=summary, exit_code=exit_code, payload=payload)


def run_bundle_manifest(
    repo_root: Path,
    *,
    branch: str = DEFAULT_BRANCH,
    bundle_path: Path = DEFAULT_BUNDLE,
    artifacts: Sequence[Path] = DEFAULT_ARTIFACTS,
    runner: Runner = subprocess_runner,
) -> BundleManifestResult:
    checks: list[CheckResult] = []
    artifact_payload: dict[str, dict[str, object]] = {}
    bundle_heads: list[str] = []

    exit_code, stdout, stderr = runner(("git", "rev-parse", "HEAD"), repo_root)
    head = stdout.strip()
    if exit_code or not head:
        checks.append(
            CheckResult(
                "head_resolves",
                "failed",
                command_detail("HEAD lookup", exit_code, stdout, stderr),
            )
        )
        return finish_payload(
            checks=checks,
            branch=branch,
            head=head,
            branch_head="",
            bundle_path=bundle_path,
            bundle_heads=bundle_heads,
            artifacts=artifact_payload,
        )
    checks.append(CheckResult("head_resolves", "passed", head))

    exit_code, stdout, stderr = runner(("git", "rev-parse", branch), repo_root)
    branch_head = stdout.strip()
    if exit_code or not branch_head:
        checks.append(
            CheckResult(
                "branch_resolves",
                "failed",
                command_detail("branch lookup", exit_code, stdout, stderr),
            )
        )
        return finish_payload(
            checks=checks,
            branch=branch,
            head=head,
            branch_head=branch_head,
            bundle_path=bundle_path,
            bundle_heads=bundle_heads,
            artifacts=artifact_payload,
        )

    if branch_head != head:
        checks.append(
            CheckResult(
                "branch_matches_head",
                "failed",
                f"{branch} resolves to {branch_head}, but HEAD is {head}",
            )
        )
        return finish_payload(
            checks=checks,
            branch=branch,
            head=head,
            branch_head=branch_head,
            bundle_path=bundle_path,
            bundle_heads=bundle_heads,
            artifacts=artifact_payload,
        )
    checks.append(CheckResult("branch_matches_head", "passed", head))

    missing_artifacts = [
        str(artifact)
        for artifact in artifacts
        if not actual_path(repo_root, artifact).exists()
    ]
    if missing_artifacts:
        checks.append(
            CheckResult(
                "release_artifacts_exist",
                "failed",
                f"missing artifacts: {', '.join(missing_artifacts)}",
            )
        )
        return finish_payload(
            checks=checks,
            branch=branch,
            head=head,
            branch_head=branch_head,
            bundle_path=bundle_path,
            bundle_heads=bundle_heads,
            artifacts=artifact_payload,
        )
    checks.append(
        CheckResult(
            "release_artifacts_exist",
            "passed",
            ", ".join(str(artifact) for artifact in artifacts),
        )
    )

    bundle_actual_path = actual_path(repo_root, bundle_path)
    bundle_actual_path.parent.mkdir(parents=True, exist_ok=True)
    if bundle_actual_path.exists():
        bundle_actual_path.unlink()

    exit_code, stdout, stderr = runner(
        ("git", "bundle", "create", str(bundle_path), branch), repo_root
    )
    if exit_code:
        checks.append(
            CheckResult(
                "bundle_create",
                "failed",
                command_detail("bundle create", exit_code, stdout, stderr),
            )
        )
        return finish_payload(
            checks=checks,
            branch=branch,
            head=head,
            branch_head=branch_head,
            bundle_path=bundle_path,
            bundle_heads=bundle_heads,
            artifacts=artifact_payload,
        )
    checks.append(CheckResult("bundle_create", "passed", str(bundle_path)))

    exit_code, stdout, stderr = runner(
        ("git", "bundle", "verify", str(bundle_path)), repo_root
    )
    if exit_code:
        checks.append(
            CheckResult(
                "bundle_verify",
                "failed",
                command_detail("bundle verify", exit_code, stdout, stderr),
            )
        )
        return finish_payload(
            checks=checks,
            branch=branch,
            head=head,
            branch_head=branch_head,
            bundle_path=bundle_path,
            bundle_heads=bundle_heads,
            artifacts=artifact_payload,
        )
    checks.append(CheckResult("bundle_verify", "passed", stdout.strip()))

    exit_code, stdout, stderr = runner(
        ("git", "bundle", "list-heads", str(bundle_path)), repo_root
    )
    if exit_code:
        checks.append(
            CheckResult(
                "bundle_list_heads",
                "failed",
                command_detail("bundle list-heads", exit_code, stdout, stderr),
            )
        )
        return finish_payload(
            checks=checks,
            branch=branch,
            head=head,
            branch_head=branch_head,
            bundle_path=bundle_path,
            bundle_heads=bundle_heads,
            artifacts=artifact_payload,
        )

    bundle_heads = [line.strip() for line in stdout.splitlines() if line.strip()]
    expected_bundle_head = f"{head} refs/heads/{branch}"
    if expected_bundle_head not in bundle_heads:
        checks.append(
            CheckResult(
                "bundle_head_matches_branch",
                "failed",
                f"expected {expected_bundle_head}; got {bundle_heads}",
            )
        )
        return finish_payload(
            checks=checks,
            branch=branch,
            head=head,
            branch_head=branch_head,
            bundle_path=bundle_path,
            bundle_heads=bundle_heads,
            artifacts=artifact_payload,
        )
    checks.append(CheckResult("bundle_head_matches_branch", "passed", head))

    for artifact in (*artifacts, bundle_path):
        artifact_actual_path = actual_path(repo_root, artifact)
        artifact_payload[str(artifact)] = {
            "path": str(artifact),
            "size_bytes": artifact_actual_path.stat().st_size,
            "sha256": sha256_file(artifact_actual_path),
        }
    checks.append(CheckResult("artifact_hashes", "passed", "sha256 recorded"))

    return finish_payload(
        checks=checks,
        branch=branch,
        head=head,
        branch_head=branch_head,
        bundle_path=bundle_path,
        bundle_heads=bundle_heads,
        artifacts=artifact_payload,
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild, verify, and hash the QA-Z alpha release bundle."
    )
    parser.add_argument(
        "--branch",
        default=DEFAULT_BRANCH,
        help=f"Branch ref to bundle. Defaults to {DEFAULT_BRANCH}.",
    )
    parser.add_argument(
        "--bundle",
        default=str(DEFAULT_BUNDLE),
        help=f"Bundle output path. Defaults to {DEFAULT_BUNDLE}.",
    )
    parser.add_argument(
        "--artifact",
        action="append",
        default=None,
        help=(
            "Release artifact to hash. May be passed multiple times. "
            "Defaults to the QA-Z alpha sdist and wheel."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable bundle manifest evidence as JSON.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    artifacts = (
        [Path(artifact) for artifact in args.artifact]
        if args.artifact
        else list(DEFAULT_ARTIFACTS)
    )
    result = run_bundle_manifest(
        Path.cwd(),
        branch=args.branch,
        bundle_path=Path(args.bundle),
        artifacts=artifacts,
    )
    if args.json:
        print(json.dumps(result.payload, indent=2))
    else:
        checks_payload = result.payload["checks"]
        assert isinstance(checks_payload, list)
        for check in checks_payload:
            assert isinstance(check, dict)
            status = str(check["status"]).upper()
            print(f"[{status}] {check['name']}: {check['detail']}")
        print(result.summary)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
