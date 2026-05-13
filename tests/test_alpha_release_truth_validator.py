"""Tests for alpha release truth-surface validation."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "alpha_release_truth_validator.py"
PROOF_HEAD = "9bbd1294d3b25fd45216b6cb14f2d97dd087351a"
POST_COMMIT_HEAD = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
ORIGIN_MAIN = "8f647619418b884afa3bef3d839326680bec70af"
PROOF_BRANCH = f"codex/alpha-rc-{PROOF_HEAD[:12]}-20260513"


def load_truth_validator_module():
    cached = sys.modules.get("alpha_release_truth_validator")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "alpha_release_truth_validator", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def valid_release_truth_texts(module):
    return module.ReleaseTruthTexts(
        worktree_packet=f"""
## Alpha Release-Candidate Decision Packet - 2026-05-12
- Proof timestamp: `2026-05-12T22:50Z`.
- Source HEAD at proof time: `{PROOF_HEAD}`.
- Branch at proof time: `main`.
- Remote `main` at proof time:
  `{ORIGIN_MAIN}`.
- Publish mode for this packet: `PROOF_ONLY`; approval flags
  `RELEASE_EXECUTION_APPROVED`, `PUSH_ALLOWED`, `TAG_ALLOWED`,
  `GITHUB_RELEASE_ALLOWED`, `PACKAGE_PUBLISH_ALLOWED`, and `DEPLOY_ALLOWED`
  were unset. No push, tag, GitHub release, package publish, deployment,
  credential use, destructive cleanup, or queue mutation was attempted.
- Local proof HEAD is 17 commits ahead of remote `main`.
Push/tag/release/package publish: not executed in PROOF_ONLY mode.
```bash
test "$(git rev-parse HEAD)" = "{PROOF_HEAD}"
git push -u origin {PROOF_HEAD}:refs/heads/{PROOF_BRANCH}
git ls-remote --heads origin {PROOF_BRANCH}
```
Expected proof branch output must resolve `{PROOF_HEAD}` to
`refs/heads/{PROOF_BRANCH}`.
Direct `main` update needs separate explicit approval.
Direct `main` update must use `git push origin {PROOF_HEAD}:main`, not a
moving `HEAD:main` refspec.
```bash
git tag -s <approved-alpha-tag> -m "QA-Z <approved-alpha-tag>"
git tag -v <approved-alpha-tag>
git push origin <approved-alpha-tag>
git ls-remote --tags origin <approved-alpha-tag>
```
Do not reuse `v0.9.8-alpha` or `v0.9.9-alpha`.
```bash
gh release create <approved-alpha-tag> --repo qazedhq/qa-z --title "QA-Z <approved-alpha-tag>" --notes-file <approved-release-notes>
```
- `python scripts\\check_public_raw_urls.py --repo qazedhq/qa-z --ref main --commit {PROOF_HEAD}`
  passed branch `main` URLs but failed exact-commit raw URLs with HTTP `404`.
Package publish dry-run packet:
- Package metadata version is `0.9.8a0` in `pyproject.toml`.
- `PACKAGE_PUBLISH_ALLOWED` unset.
```bash
python -m build --sdist --wheel
python scripts\\alpha_release_artifact_smoke.py --with-deps --json
python -m twine check dist/*
```
Registry publish remains blocked until approval.
Rollback and incident packet:
- Mistaken proof branch push: if approved by a release owner, delete only the
  proof branch with `git push origin --delete {PROOF_BRANCH}`.
- Mistaken remote tag: only after human approval, run
  `git push origin --delete <approved-alpha-tag>`.
- Package rollback/yank policy is registry-owned.
- Incident record must include actor, time, affected ref or artifact, command
  evidence, rollback command, validation rerun, and next approval owner.
- After any rollback, rerun:
```bash
python scripts\\alpha_release_gate.py --quick --allow-dirty --json
```
Deferred Marketing/X packet:
- Deferred paths are `marketing/x/**` and `tests/test_x_automation.py`.
- Do not stage Marketing/X source, tests, generated state, or queue files.
- No X credentials are required for this alpha RC.
Deferred Claude compatibility mirror packet:
- Deferred paths are `.claude/**`.
- `.claude/**` is a compatibility mirror. Codex-native source of truth remains
  `.codex/agents/*.toml`, `.agents/skills/*/SKILL.md`, and `docs/agent/*.md`.
- Do not stage, delete, or promote `.claude/**`.
Remote and publishing proof packet:
- local `{PROOF_HEAD}` is not yet remote-visible.
- QA-Z remote alpha readiness: `Partial`.
- QA-Z release-execution readiness: `Partial`.
- Production readiness: `No`. Production readiness is not claimed.
## Preflight
""",
        package_plan=f"""
## Alpha RC package dry-run packet - 2026-05-12
Package metadata version: `0.9.8a0`.
Current release proof HEAD: `{PROOF_HEAD}`.
No PyPI, TestPyPI, npm, GitHub Packages, or other package registry publish is approved.
`RELEASE_EXECUTION_APPROVED` and `PACKAGE_PUBLISH_ALLOWED` must both be set to
`true` by a human release owner before any upload command is run.

Safe local-only dry-run packet:

python -m build --sdist --wheel
python scripts\\alpha_release_artifact_smoke.py --with-deps --json
python -m twine check dist/*

Blocked upload packet:

python -m twine upload --repository testpypi dist/*
python -m twine upload dist/*
Rollback is registry-owned.
""",
        release_handoff="""
Current quality-mode no-remote rehearsal:
python scripts/alpha_release_preflight.py --skip-remote --expected-origin-url https://github.com/qazedhq/qa-z.git --expected-branch main --allow-dirty --skip-release-tag-check --json
The bare historical command is retained only as a legacy blocker check.
""",
    )


def test_validator_rejects_stale_local_head_in_release_packet() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = module.ReleaseTruthTexts(
        worktree_packet="""
## Alpha Release-Candidate Decision Packet - 2026-05-12
- Source HEAD at proof time: `a3e5303933fe9b1bef03e2e915ce224e0cc4e1c1`.
- Branch at proof time: `main`.
- Remote `main` at proof time:
  `8f647619418b884afa3bef3d839326680bec70af`.
- Local proof HEAD is 15 commits ahead of remote `main`.
Remote and publishing proof packet:
- local `1f35eeb7c420842aad78f2bb10b0545a15412cbd` is not yet remote-visible.
""",
        package_plan="",
        release_handoff="",
    )

    payload = module.validate_release_truth_texts(facts, texts)

    assert payload["status"] == "failed"
    assert "current_head_pinned" in payload["failed_checks"]
    assert "ahead_count_current" in payload["failed_checks"]
    assert "stale_local_sha_absent" in payload["failed_checks"]
    assert any(
        "Regenerate the alpha release decision packet for the current HEAD" in action
        for action in payload["next_actions"]
    )
    assert (
        "python scripts\\alpha_release_truth_validator.py --proof-head-from-packet --json"
        in payload["next_commands"]
    )


def test_validator_human_output_renders_recovery_guidance() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = module.ReleaseTruthTexts(
        worktree_packet=f"""
## Alpha Release-Candidate Decision Packet - 2026-05-12
- Source HEAD at proof time: `{POST_COMMIT_HEAD}`.
- Branch at proof time: `main`.
- Remote `main` at proof time:
  `{ORIGIN_MAIN}`.
- Local proof HEAD is 15 commits ahead of remote `main`.
""",
        package_plan="",
        release_handoff="",
    )

    output = module.render_human(module.validate_release_truth_texts(facts, texts))

    assert "next actions:" in output
    assert "Regenerate the alpha release decision packet for the current HEAD" in output
    assert "next commands:" in output
    assert (
        "python scripts\\alpha_release_truth_validator.py --proof-head-from-packet --json"
        in output
    )


def test_validator_rejects_missing_release_decision_packet_header() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = module.ReleaseTruthTexts(
        worktree_packet="""\
## Release Notes Without Current Decision Header
- Source HEAD at proof time: `9bbd1294d3b25fd45216b6cb14f2d97dd087351a`.
- Branch at proof time: `main`.
- Remote `main` at proof time:
  `8f647619418b884afa3bef3d839326680bec70af`.
- Local proof HEAD is 17 commits ahead of remote `main`.
Remote and publishing proof packet:
- local `9bbd1294d3b25fd45216b6cb14f2d97dd087351a` is not yet remote-visible.
""",
        package_plan="",
        release_handoff="",
    )

    payload = module.validate_release_truth_texts(facts, texts)

    assert payload["status"] == "failed"
    assert "release_packet_header_present" in payload["failed_checks"]


def test_validator_rejects_duplicate_release_decision_packet_sections() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    duplicated = module.ReleaseTruthTexts(
        worktree_packet=(
            texts.worktree_packet
            + """
## Alpha Release-Candidate Decision Packet - 2026-05-12
- Source HEAD at proof time: `a3e5303933fe9b1bef03e2e915ce224e0cc4e1c1`.
- Local proof HEAD is 15 commits ahead of remote `main`.
"""
        ),
        package_plan=texts.package_plan,
        release_handoff=texts.release_handoff,
    )

    payload = module.validate_release_truth_texts(facts, duplicated)

    assert payload["status"] == "failed"
    assert "release_packet_header_unique" in payload["failed_checks"]


def test_validator_rejects_duplicate_source_head_in_release_packet() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    duplicated = module.ReleaseTruthTexts(
        worktree_packet=texts.worktree_packet.replace(
            f"- Source HEAD at proof time: `{PROOF_HEAD}`.",
            (
                f"- Source HEAD at proof time: `{PROOF_HEAD}`.\n"
                f"- Source HEAD at proof time: `{PROOF_HEAD}`."
            ),
        ),
        package_plan=texts.package_plan,
        release_handoff=texts.release_handoff,
    )

    payload = module.validate_release_truth_texts(facts, duplicated)

    assert payload["status"] == "failed"
    assert "source_head_unique" in payload["failed_checks"]


def test_validator_accepts_current_release_execution_packet_contract() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)

    payload = module.validate_release_truth_texts(facts, texts)

    assert payload["status"] == "passed"
    assert payload["check_count"] >= 12
    assert payload["failed_checks"] == []


def test_validator_json_facts_include_proof_branch_readiness() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )

    payload = module.validate_release_truth_texts(
        facts, valid_release_truth_texts(module)
    )

    assert payload["status"] == "passed"
    assert payload["facts"]["proof_branch"] == PROOF_BRANCH
    assert (
        payload["facts"]["current_head_remote_proof"] == "local_only_not_remote_visible"
    )


def test_validator_accepts_singular_ahead_count_phrase() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=1,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    packet = texts.worktree_packet.replace(
        "- Local proof HEAD is 17 commits ahead of remote `main`.",
        "- Local proof HEAD is 1 commit ahead of remote `main`.",
    )

    payload = module.validate_release_truth_texts(
        facts,
        module.ReleaseTruthTexts(
            worktree_packet=packet,
            package_plan=texts.package_plan,
            release_handoff=texts.release_handoff,
        ),
    )

    assert payload["status"] == "passed"


def test_validator_accepts_remote_visible_current_head_packet() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=PROOF_HEAD,
        ahead_count=0,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    packet = (
        texts.worktree_packet.replace(
            f"  `{ORIGIN_MAIN}`.",
            f"  `{PROOF_HEAD}`.",
        )
        .replace(
            "- Local proof HEAD is 17 commits ahead of remote `main`.",
            "- Local proof HEAD is 0 commits ahead of remote `main`.",
        )
        .replace(
            "passed branch `main` URLs but failed exact-commit raw URLs with HTTP `404`.",
            "passed for branch and exact-commit raw URLs.",
        )
        .replace(
            f"- local `{PROOF_HEAD}` is not yet remote-visible.",
            f"- local `{PROOF_HEAD}` is remote-visible.",
        )
    )

    payload = module.validate_release_truth_texts(
        facts,
        module.ReleaseTruthTexts(
            worktree_packet=packet,
            package_plan=texts.package_plan,
            release_handoff=texts.release_handoff,
        ),
    )

    assert payload["status"] == "passed"
    assert payload["failed_checks"] == []
    assert payload["facts"]["current_head_remote_proof"] == "remote_visible"


def test_validator_explicit_proof_head_mode_survives_later_local_commits() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
        current_head=POST_COMMIT_HEAD,
        proof_head_mode="explicit",
    )

    payload = module.validate_release_truth_texts(
        facts, valid_release_truth_texts(module)
    )

    assert payload["status"] == "passed"
    assert payload["failed_checks"] == []
    assert payload["facts"]["head"] == PROOF_HEAD
    assert payload["facts"]["current_head"] == POST_COMMIT_HEAD
    assert payload["facts"]["proof_head_mode"] == "explicit"
    check_names = {check["name"] for check in payload["checks"]}
    assert "current_head_after_proof_recorded" in check_names


def test_validator_extracts_proof_head_from_packet_for_commit_safe_mode() -> None:
    module = load_truth_validator_module()

    proof_head = module.proof_head_from_texts(valid_release_truth_texts(module))

    assert proof_head == PROOF_HEAD


def test_truth_validator_cli_rejects_missing_source_head_for_packet_mode(
    monkeypatch,
) -> None:
    module = load_truth_validator_module()

    monkeypatch.setattr(
        module,
        "read_release_truth_texts",
        lambda _repo_root, **_kwargs: module.ReleaseTruthTexts(
            worktree_packet="""
## Alpha Release-Candidate Decision Packet - 2026-05-12
- Branch at proof time: `main`.
""",
            package_plan="",
            release_handoff="",
        ),
    )

    with pytest.raises(
        SystemExit,
        match="release packet does not contain a Source HEAD at proof time",
    ):
        module.main(["--proof-head-from-packet", "--json"])


def test_validator_rejects_head_based_proof_branch_push() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    packet = (
        texts.worktree_packet.replace(
            f'test "$(git rev-parse HEAD)" = "{PROOF_HEAD}"\n', ""
        )
        .replace(
            f"git push -u origin {PROOF_HEAD}:refs/heads/{PROOF_BRANCH}",
            f"git push -u origin HEAD:{PROOF_BRANCH}",
        )
        .replace(
            f"Expected proof branch output must resolve `{PROOF_HEAD}` to\n"
            f"`refs/heads/{PROOF_BRANCH}`.\n",
            "",
        )
        .replace(
            f"Direct `main` update must use `git push origin {PROOF_HEAD}:main`, not a\n"
            "moving `HEAD:main` refspec.\n",
            "",
        )
    )
    mutated = module.ReleaseTruthTexts(
        worktree_packet=packet,
        package_plan=texts.package_plan,
        release_handoff=texts.release_handoff,
    )

    payload = module.validate_release_truth_texts(facts, mutated)

    assert payload["status"] == "failed"
    assert "proof_branch_packet" in payload["failed_checks"]


def test_validator_rejects_placeholder_proof_branch_packet() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    packet = (
        texts.worktree_packet.replace(
            f'test "$(git rev-parse HEAD)" = "{PROOF_HEAD}"',
            'test "$(git rev-parse HEAD)" = "<approved-sha>"',
        )
        .replace(
            f"git push -u origin {PROOF_HEAD}:refs/heads/{PROOF_BRANCH}",
            "git push -u origin <approved-sha>:refs/heads/codex/alpha-rc-<approved-sha>-20260512",
        )
        .replace(
            f"git ls-remote --heads origin {PROOF_BRANCH}",
            "git ls-remote --heads origin codex/alpha-rc-<approved-sha>-20260512",
        )
        .replace(
            f"Expected proof branch output must resolve `{PROOF_HEAD}` to\n"
            f"`refs/heads/{PROOF_BRANCH}`.",
            "Expected proof branch output must resolve `<approved-sha>` to\n"
            "`refs/heads/codex/alpha-rc-<approved-sha>-20260512`.",
        )
        .replace(
            f"Direct `main` update must use `git push origin {PROOF_HEAD}:main`, not a",
            "Direct `main` update must use `git push origin <approved-sha>:main`, not a",
        )
    )
    mutated = module.ReleaseTruthTexts(
        worktree_packet=packet,
        package_plan=texts.package_plan,
        release_handoff=texts.release_handoff,
    )

    payload = module.validate_release_truth_texts(facts, mutated)

    assert payload["status"] == "failed"
    assert "proof_branch_packet" in payload["failed_checks"]


def test_validator_rejects_upload_command_inside_safe_dry_run_packet() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    package_plan = texts.package_plan.replace(
        "python -m twine check dist/*\n\nBlocked upload packet:",
        "python -m twine check dist/*\npython -m twine upload dist/*\n\nBlocked upload packet:",
    )
    mutated = module.ReleaseTruthTexts(
        worktree_packet=texts.worktree_packet,
        package_plan=package_plan,
        release_handoff=texts.release_handoff,
    )

    payload = module.validate_release_truth_texts(facts, mutated)

    assert payload["status"] == "failed"
    assert "package_dry_run_packet" in payload["failed_checks"]


def test_validator_rejects_stale_remote_main_and_ahead_count() -> None:
    module = load_truth_validator_module()
    moved_origin_main = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=moved_origin_main,
        ahead_count=18,
        package_version="0.9.8a0",
    )

    payload = module.validate_release_truth_texts(
        facts, valid_release_truth_texts(module)
    )

    assert payload["status"] == "failed"
    assert "origin_main_pinned" in payload["failed_checks"]
    assert "ahead_count_current" in payload["failed_checks"]
    assert "stale_local_sha_absent" in payload["failed_checks"]


def test_validator_rejects_missing_package_publish_approval_blocker() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    package_plan = texts.package_plan.replace(
        "No PyPI, TestPyPI, npm, GitHub Packages, or other package registry publish is approved.\n",
        "",
    )
    mutated = module.ReleaseTruthTexts(
        worktree_packet=texts.worktree_packet,
        package_plan=package_plan,
        release_handoff=texts.release_handoff,
    )

    payload = module.validate_release_truth_texts(facts, mutated)

    assert payload["status"] == "failed"
    assert "package_dry_run_packet" in payload["failed_checks"]


def test_validator_rejects_package_plan_without_current_proof_head() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    package_plan = texts.package_plan.replace(
        f"Current release proof HEAD: `{PROOF_HEAD}`.\n",
        "",
    )
    mutated = module.ReleaseTruthTexts(
        worktree_packet=texts.worktree_packet,
        package_plan=package_plan,
        release_handoff=texts.release_handoff,
    )

    payload = module.validate_release_truth_texts(facts, mutated)

    assert payload["status"] == "failed"
    assert "package_dry_run_packet" in payload["failed_checks"]


def test_validator_rejects_rollback_without_validation_rerun() -> None:
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    packet = texts.worktree_packet.replace(
        "python scripts\\alpha_release_gate.py --quick --allow-dirty --json\n",
        "",
    )
    mutated = module.ReleaseTruthTexts(
        worktree_packet=packet,
        package_plan=texts.package_plan,
        release_handoff=texts.release_handoff,
    )

    payload = module.validate_release_truth_texts(facts, mutated)

    assert payload["status"] == "failed"
    assert "rollback_incident_packet" in payload["failed_checks"]


def test_validator_rejects_marketing_deferred_packet_without_credential_boundary() -> (
    None
):
    module = load_truth_validator_module()
    facts = module.ReleaseTruthFacts(
        head=PROOF_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )
    texts = valid_release_truth_texts(module)
    packet = texts.worktree_packet.replace(
        "- No X credentials are required for this alpha RC.\n",
        "",
    )
    mutated = module.ReleaseTruthTexts(
        worktree_packet=packet,
        package_plan=texts.package_plan,
        release_handoff=texts.release_handoff,
    )

    payload = module.validate_release_truth_texts(facts, mutated)

    assert payload["status"] == "failed"
    assert "marketing_x_deferred" in payload["failed_checks"]


def test_collected_facts_record_packet_proof_head_mode(tmp_path: Path) -> None:
    module = load_truth_validator_module()

    facts = module.collect_release_truth_facts(
        tmp_path,
        proof_head=PROOF_HEAD,
        proof_head_mode="packet",
        current_head=POST_COMMIT_HEAD,
        branch="main",
        origin_main=ORIGIN_MAIN,
        ahead_count=17,
        package_version="0.9.8a0",
    )

    assert facts.head == PROOF_HEAD
    assert facts.current_head == POST_COMMIT_HEAD
    assert facts.proof_head_mode == "packet"


def test_collected_facts_count_ahead_from_packet_proof_head(
    monkeypatch, tmp_path: Path
) -> None:
    module = load_truth_validator_module()

    def fake_run_git(_repo_root, *args):
        if args == ("rev-parse", "HEAD"):
            return POST_COMMIT_HEAD
        if args == ("branch", "--show-current"):
            return "main"
        if args == ("rev-parse", "origin/main"):
            return ORIGIN_MAIN
        if args == (
            "rev-list",
            "--left-right",
            "--count",
            f"origin/main...{PROOF_HEAD}",
        ):
            return "0 17"
        raise AssertionError(f"unexpected git command: {args}")

    monkeypatch.setattr(module, "run_git", fake_run_git)
    monkeypatch.setattr(
        module, "package_version_from_pyproject", lambda _repo_root: "0.9.8a0"
    )

    facts = module.collect_release_truth_facts(
        tmp_path,
        proof_head=PROOF_HEAD,
        proof_head_mode="packet",
    )

    assert facts.head == PROOF_HEAD
    assert facts.current_head == POST_COMMIT_HEAD
    assert facts.ahead_count == 17
    assert facts.proof_head_mode == "packet"


def test_truth_validator_cli_writes_output_payload(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    module = load_truth_validator_module()
    output_path = tmp_path / "release-truth.json"

    monkeypatch.setattr(
        module,
        "read_release_truth_texts",
        lambda _repo_root, **_kwargs: valid_release_truth_texts(module),
    )
    monkeypatch.setattr(
        module,
        "collect_release_truth_facts",
        lambda _repo_root, **_kwargs: module.ReleaseTruthFacts(
            head=PROOF_HEAD,
            branch="main",
            origin_main=ORIGIN_MAIN,
            ahead_count=17,
            package_version="0.9.8a0",
        ),
    )

    exit_code = module.main(["--json", "--output", str(output_path)])

    captured = capsys.readouterr()
    stdout_payload = json.loads(captured.out)
    file_payload = json.loads(output_path.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert stdout_payload == file_payload
    assert file_payload["kind"] == "qa_z.alpha_release_truth_validator"
    assert file_payload["status"] == "passed"
    assert captured.err == ""


def test_truth_validator_cli_reports_output_write_failure(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    module = load_truth_validator_module()
    output_path = tmp_path / "release-truth.json"
    original_write_text = module.Path.write_text

    monkeypatch.setattr(
        module,
        "read_release_truth_texts",
        lambda _repo_root, **_kwargs: valid_release_truth_texts(module),
    )
    monkeypatch.setattr(
        module,
        "collect_release_truth_facts",
        lambda _repo_root, **_kwargs: module.ReleaseTruthFacts(
            head=PROOF_HEAD,
            branch="main",
            origin_main=ORIGIN_MAIN,
            ahead_count=17,
            package_version="0.9.8a0",
        ),
    )

    def fail_output_write(path, *args, **kwargs):
        if path == output_path:
            raise OSError("disk full")
        return original_write_text(path, *args, **kwargs)

    monkeypatch.setattr(module.Path, "write_text", fail_output_write)

    exit_code = module.main(["--json", "--output", str(output_path)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 2
    assert payload["status"] == "passed"
    assert (
        f"alpha release truth validator: could not write --output {output_path}: disk full"
        in captured.err
    )
