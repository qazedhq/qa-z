"""Validate QA-Z alpha release truth surfaces against local facts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from qa_z.subprocess_env import build_tool_subprocess_env


DEFAULT_WORKTREE_PACKET = Path("docs/reports/worktree-commit-plan.md")
DEFAULT_PACKAGE_PLAN = Path("docs/package-publish-plan.md")
DEFAULT_RELEASE_HANDOFF = Path("docs/releases/v0.9.8-alpha-publish-handoff.md")
RELEASE_PACKET_HEADER = "## Alpha Release-Candidate Decision Packet - 2026-05-12"
SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")
SOURCE_HEAD_RE = re.compile(r"Source HEAD at proof time:\s*`(?P<head>[0-9a-f]{40})`")
VERSION_RE = re.compile(r'^version\s*=\s*"(?P<version>[^"]+)"', re.MULTILINE)


@dataclass(frozen=True)
class ReleaseTruthFacts:
    head: str
    branch: str
    origin_main: str
    ahead_count: int
    package_version: str
    current_head: str | None = None
    proof_head_mode: str = "current"


@dataclass(frozen=True)
class ReleaseTruthTexts:
    worktree_packet: str
    package_plan: str
    release_handoff: str


@dataclass(frozen=True)
class TruthCheck:
    name: str
    passed: bool
    detail: str


def run_git(repo_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ("git", *args),
        cwd=repo_root,
        env=build_tool_subprocess_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout).strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return completed.stdout.strip()


def package_version_from_pyproject(repo_root: Path) -> str:
    pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8")
    match = VERSION_RE.search(pyproject)
    if match is None:
        raise RuntimeError("pyproject.toml does not contain a version field")
    return match.group("version")


def collect_release_truth_facts(
    repo_root: Path,
    *,
    head: str | None = None,
    proof_head: str | None = None,
    proof_head_mode: str | None = None,
    current_head: str | None = None,
    branch: str | None = None,
    origin_main: str | None = None,
    ahead_count: int | None = None,
    package_version: str | None = None,
) -> ReleaseTruthFacts:
    resolved_current_head = current_head or run_git(repo_root, "rev-parse", "HEAD")
    resolved_head = proof_head or head or resolved_current_head
    resolved_proof_head_mode = (
        proof_head_mode or "explicit"
        if proof_head
        else "override"
        if head
        else "current"
    )
    resolved_branch = branch or run_git(repo_root, "branch", "--show-current")
    resolved_origin_main = origin_main or run_git(repo_root, "rev-parse", "origin/main")
    if ahead_count is None:
        ahead_ref = resolved_head if proof_head or head else "HEAD"
        counts = run_git(
            repo_root,
            "rev-list",
            "--left-right",
            "--count",
            f"origin/main...{ahead_ref}",
        )
        parts = counts.split()
        if len(parts) != 2:
            raise RuntimeError(f"unexpected ahead/behind output: {counts}")
        ahead_count = int(parts[1])
    resolved_package_version = package_version or package_version_from_pyproject(
        repo_root
    )
    return ReleaseTruthFacts(
        head=resolved_head,
        branch=resolved_branch,
        origin_main=resolved_origin_main,
        ahead_count=ahead_count,
        package_version=resolved_package_version,
        current_head=resolved_current_head,
        proof_head_mode=resolved_proof_head_mode,
    )


def read_release_truth_texts(
    repo_root: Path,
    *,
    worktree_packet_path: Path = DEFAULT_WORKTREE_PACKET,
    package_plan_path: Path = DEFAULT_PACKAGE_PLAN,
    release_handoff_path: Path = DEFAULT_RELEASE_HANDOFF,
) -> ReleaseTruthTexts:
    return ReleaseTruthTexts(
        worktree_packet=(repo_root / worktree_packet_path).read_text(encoding="utf-8"),
        package_plan=(repo_root / package_plan_path).read_text(encoding="utf-8"),
        release_handoff=(repo_root / release_handoff_path).read_text(encoding="utf-8"),
    )


def section_from_header(text: str, header: str) -> str | None:
    start = text.find(header)
    if start < 0:
        return None
    next_start = text.find("\n## ", start + len(header))
    if next_start < 0:
        return text[start:]
    return text[start:next_start]


def proof_head_from_texts(texts: ReleaseTruthTexts) -> str | None:
    packet = section_from_header(texts.worktree_packet, RELEASE_PACKET_HEADER)
    if packet is None:
        return None
    match = SOURCE_HEAD_RE.search(packet)
    if match is None:
        return None
    return match.group("head")


def text_between_markers(
    text: str, start_marker: str, end_marker: str | None = None
) -> str | None:
    start = text.find(start_marker)
    if start < 0:
        return None
    content_start = start + len(start_marker)
    if end_marker is None:
        return text[content_start:]
    end = text.find(end_marker, content_start)
    if end < 0:
        return None
    return text[content_start:end]


def has_all(text: str, values: Sequence[str]) -> bool:
    return all(value in text for value in values)


def check(name: str, passed: bool, detail: str) -> TruthCheck:
    return TruthCheck(name=name, passed=passed, detail=detail)


def recovery_guidance_for_failed_checks(
    failed_checks: Sequence[str],
) -> dict[str, list[str]]:
    failed = set(failed_checks)
    next_actions: list[str] = []
    next_commands: list[str] = []

    stale_packet_checks = {
        "current_head_pinned",
        "ahead_count_current",
        "stale_local_sha_absent",
        "current_head_remote_not_visible",
    }
    if failed & stale_packet_checks:
        next_actions.extend(
            [
                "Regenerate the alpha release decision packet for the current HEAD before treating default validator output as release proof.",
                "If reviewing the historical proof packet instead of current HEAD, rerun the validator with --proof-head-from-packet.",
            ]
        )
        next_commands.append(
            "python scripts\\alpha_release_truth_validator.py --proof-head-from-packet --json"
        )

    if {
        "release_packet_header_present",
        "release_packet_header_unique",
    } & failed:
        next_actions.append(
            "Keep exactly one current alpha release decision packet section before validating proof-head or release-command claims."
        )

    if failed and not next_actions:
        next_actions.append(
            "Inspect failed_checks and update the release truth packet, package plan, or handoff before claiming alpha release readiness."
        )

    return {"next_actions": next_actions, "next_commands": next_commands}


def validate_release_truth_texts(
    facts: ReleaseTruthFacts, texts: ReleaseTruthTexts
) -> dict[str, object]:
    packet = section_from_header(texts.worktree_packet, RELEASE_PACKET_HEADER)
    packet_header_present = packet is not None
    packet_header_count = texts.worktree_packet.count(RELEASE_PACKET_HEADER)
    if packet is None:
        packet = ""
    package_plan = texts.package_plan
    handoff = texts.release_handoff
    safe_package_dry_run = text_between_markers(
        package_plan, "Safe local-only dry-run packet:", "Blocked upload packet:"
    )
    blocked_package_upload = text_between_markers(
        package_plan, "Blocked upload packet:"
    )
    stale_shas = sorted(set(SHA_RE.findall(packet)) - {facts.head, facts.origin_main})

    checks = [
        check(
            "release_packet_header_present",
            packet_header_present,
            "release packet must contain the current alpha decision packet header",
        ),
        check(
            "release_packet_header_unique",
            packet_header_count == 1,
            f"release packet must contain exactly one current alpha decision packet header; found {packet_header_count}",
        ),
        check(
            "current_head_pinned",
            has_all(packet, ["Source HEAD at proof time", f"`{facts.head}`"]),
            "release packet must pin the current local HEAD",
        ),
        check(
            "current_head_after_proof_recorded",
            facts.proof_head_mode in {"current", "override"}
            or bool(facts.current_head),
            "proof-head mode must report the current local HEAD separately",
        ),
        check(
            "branch_pinned",
            f"Branch at proof time: `{facts.branch}`" in packet,
            "release packet must pin the active branch",
        ),
        check(
            "origin_main_pinned",
            facts.origin_main in packet and "Remote `main`" in packet,
            "release packet must pin origin/main separately from local HEAD",
        ),
        check(
            "ahead_count_current",
            f"{facts.ahead_count} commits ahead of remote `main`" in packet,
            "release packet must use the current ahead count",
        ),
        check(
            "stale_local_sha_absent",
            not stale_shas,
            "release packet must not carry stale local proof SHAs: "
            + ",".join(stale_shas),
        ),
        check(
            "approval_flags_block_mutation",
            has_all(
                packet,
                [
                    "`RELEASE_EXECUTION_APPROVED`, `PUSH_ALLOWED`, `TAG_ALLOWED`",
                    "`GITHUB_RELEASE_ALLOWED`, `PACKAGE_PUBLISH_ALLOWED`, and `DEPLOY_ALLOWED`",
                    "were unset. No push, tag, GitHub release, package publish, deployment",
                ],
            ),
            "approval flags must explicitly block unapproved release mutation",
        ),
        check(
            "proof_only_no_publish_claim",
            "Push/tag/release/package publish: not executed in PROOF_ONLY mode."
            in packet,
            "packet must say proof-only did not execute publish actions",
        ),
        check(
            "current_head_remote_not_visible",
            has_all(
                packet,
                [
                    f"--commit {facts.head}",
                    "failed exact-commit raw URLs with HTTP `404`",
                    f"local `{facts.head}` is not yet remote-visible",
                ],
            ),
            "remote proof must distinguish branch proof from current-HEAD proof",
        ),
        check(
            "proof_branch_packet",
            (
                has_all(
                    packet,
                    [
                        'test "$(git rev-parse HEAD)" = "<approved-sha>"',
                        "git push -u origin <approved-sha>:refs/heads/codex/alpha-rc-<approved-sha>-20260512",
                        "git ls-remote --heads origin codex/alpha-rc-<approved-sha>-20260512",
                        "Expected proof branch output must resolve `<approved-sha>`",
                        "`refs/heads/codex/alpha-rc-<approved-sha>-20260512`",
                        "Direct `main` update needs separate explicit approval",
                        "Direct `main` update must use `git push origin <approved-sha>:main`",
                    ],
                )
                and "git push -u origin HEAD:codex/alpha-rc-<approved-sha>-20260512"
                not in packet
                and "git push origin HEAD:main" not in packet
            ),
            "proof branch packet must use an explicit approved SHA and post-push equality proof",
        ),
        check(
            "tag_release_packet",
            has_all(
                packet,
                [
                    "git tag -s <approved-alpha-tag>",
                    "git tag -v <approved-alpha-tag>",
                    "git push origin <approved-alpha-tag>",
                    "gh release create <approved-alpha-tag>",
                    "Do not reuse `v0.9.8-alpha`",
                    "`v0.9.9-alpha`",
                ],
            ),
            "tag and GitHub release packet must be approval-gated and non-reuse",
        ),
        check(
            "package_dry_run_packet",
            (
                safe_package_dry_run is not None
                and blocked_package_upload is not None
                and has_all(
                    packet + "\n" + package_plan,
                    [
                        f"Package metadata version: `{facts.package_version}`",
                        f"Package metadata version is `{facts.package_version}`",
                        "No PyPI, TestPyPI, npm, GitHub Packages, or other package registry publish is approved.",
                        "Rollback is registry-owned",
                    ],
                )
                and has_all(
                    safe_package_dry_run,
                    [
                        "python -m build --sdist --wheel",
                        "python scripts\\alpha_release_artifact_smoke.py --with-deps --json",
                        "python -m twine check dist/*",
                    ],
                )
                and "twine upload" not in safe_package_dry_run
                and has_all(
                    blocked_package_upload,
                    [
                        "python -m twine upload --repository testpypi dist/*",
                        "python -m twine upload dist/*",
                    ],
                )
            ),
            "package dry-run packet must keep upload commands out of the safe dry-run section",
        ),
        check(
            "rollback_incident_packet",
            (
                has_all(
                    packet,
                    [
                        "git push origin --delete codex/alpha-rc-<approved-sha>-20260512",
                        "Package rollback/yank policy is registry-owned",
                        "Incident record must include actor, time, affected ref or artifact",
                        "After any rollback, rerun:",
                        "python scripts\\alpha_release_gate.py --quick --allow-dirty --json",
                    ],
                )
                and (
                    "git push origin --delete <approved-alpha-tag>" in packet
                    or "git push origin :refs/tags/<approved-alpha-tag>" in packet
                )
            ),
            "rollback packet must include ref cleanup, incident, and validation rerun",
        ),
        check(
            "marketing_x_deferred",
            has_all(
                packet,
                [
                    "Deferred Marketing/X packet:",
                    "Deferred paths are `marketing/x/**` and `tests/test_x_automation.py`",
                    "Do not stage Marketing/X source",
                    "No X credentials are required for this alpha RC",
                ],
            ),
            "Marketing/X must stay deferred and credential-free",
        ),
        check(
            "claude_mirror_deferred",
            has_all(
                packet,
                [
                    "Deferred Claude compatibility mirror packet:",
                    "Deferred paths are `.claude/**`",
                    ".claude/**` is a compatibility mirror",
                    "Codex-native source of truth remains",
                    "Do not stage, delete, or promote `.claude/**`",
                ],
            ),
            "Claude mirror must stay deferred behind Codex-native truth",
        ),
        check(
            "preflight_contract_current",
            has_all(
                handoff,
                [
                    "Current quality-mode no-remote rehearsal:",
                    "python scripts/alpha_release_preflight.py --skip-remote --expected-origin-url https://github.com/qazedhq/qa-z.git --expected-branch main --allow-dirty --skip-release-tag-check --json",
                    "The bare historical command is retained only as a legacy blocker check",
                ],
            ),
            "release handoff must separate current preflight from legacy blocker command",
        ),
        check(
            "readiness_not_overclaimed",
            has_all(
                packet,
                [
                    "QA-Z remote alpha readiness: `Partial`",
                    "QA-Z release-execution readiness: `Partial`",
                    "Production readiness: `No`",
                    "Production readiness is not claimed",
                ],
            ),
            "readiness labels must stay partial/no until approval and proof exist",
        ),
    ]

    failed = [truth_check.name for truth_check in checks if not truth_check.passed]
    recovery_guidance = recovery_guidance_for_failed_checks(failed)
    return {
        "kind": "qa_z.alpha_release_truth_validator",
        "schema_version": 1,
        "status": "failed" if failed else "passed",
        "check_count": len(checks),
        "passed_count": len(checks) - len(failed),
        "failed_count": len(failed),
        "failed_checks": failed,
        "checks": [
            {
                "name": truth_check.name,
                "status": "passed" if truth_check.passed else "failed",
                "detail": truth_check.detail,
            }
            for truth_check in checks
        ],
        "next_actions": recovery_guidance["next_actions"],
        "next_commands": recovery_guidance["next_commands"],
        "facts": {
            "head": facts.head,
            "current_head": facts.current_head or facts.head,
            "proof_head_mode": facts.proof_head_mode,
            "branch": facts.branch,
            "origin_main": facts.origin_main,
            "ahead_count": facts.ahead_count,
            "package_version": facts.package_version,
        },
    }


def render_human(payload: dict[str, object]) -> str:
    lines = [
        f"alpha release truth validator: {payload['status']}",
        f"checks: {payload['passed_count']}/{payload['check_count']} passed",
    ]
    failed_checks = payload.get("failed_checks")
    if isinstance(failed_checks, list) and failed_checks:
        lines.append("failed checks:")
        lines.extend(f"- {name}" for name in failed_checks)
    next_actions = payload.get("next_actions")
    if isinstance(next_actions, list) and next_actions:
        lines.append("next actions:")
        lines.extend(f"- {action}" for action in next_actions)
    next_commands = payload.get("next_commands")
    if isinstance(next_commands, list) and next_commands:
        lines.append("next commands:")
        lines.extend(f"- {command}" for command in next_commands)
    return "\n".join(lines) + "\n"


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate alpha release packet truth against local git facts."
    )
    parser.add_argument("--worktree-packet", type=Path, default=DEFAULT_WORKTREE_PACKET)
    parser.add_argument("--package-plan", type=Path, default=DEFAULT_PACKAGE_PLAN)
    parser.add_argument("--release-handoff", type=Path, default=DEFAULT_RELEASE_HANDOFF)
    parser.add_argument("--head", default=None)
    parser.add_argument("--proof-head", default=None)
    parser.add_argument("--proof-head-from-packet", action="store_true")
    parser.add_argument("--branch", default=None)
    parser.add_argument("--origin-main", default=None)
    parser.add_argument("--ahead-count", type=int, default=None)
    parser.add_argument("--package-version", default=None)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.head and args.proof_head:
        raise SystemExit("--head and --proof-head cannot be combined")
    if args.proof_head and args.proof_head_from_packet:
        raise SystemExit("--proof-head and --proof-head-from-packet cannot be combined")
    repo_root = Path.cwd()
    texts = read_release_truth_texts(
        repo_root,
        worktree_packet_path=args.worktree_packet,
        package_plan_path=args.package_plan,
        release_handoff_path=args.release_handoff,
    )
    proof_head = args.proof_head
    if args.proof_head_from_packet:
        proof_head = proof_head_from_texts(texts)
        if proof_head is None:
            raise SystemExit(
                "release packet does not contain a Source HEAD at proof time"
            )
        proof_head_mode = "packet"
    else:
        proof_head_mode = None
    facts = collect_release_truth_facts(
        repo_root,
        head=args.head,
        proof_head=proof_head,
        proof_head_mode=proof_head_mode,
        branch=args.branch,
        origin_main=args.origin_main,
        ahead_count=args.ahead_count,
        package_version=args.package_version,
    )
    payload = validate_release_truth_texts(facts, texts)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(render_human(payload), end="")
    return 1 if payload["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
