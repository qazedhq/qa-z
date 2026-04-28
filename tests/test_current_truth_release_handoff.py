from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_release_plan_marks_completed_commit_split_truthfully() -> None:
    release_plan = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-18-github-repository-release.md"
    ).read_text(encoding="utf-8")

    assert "- [x] **Step 1: Confirm no generated runtime artifacts are staged**" in (
        release_plan
    )
    assert "- [x] **Step 2: Commit foundation first**" in release_plan
    assert "- [x] **Step 3: Commit benchmark coverage**" in release_plan
    assert "- [x] **Step 4: Commit planning and autonomy layers**" in release_plan
    assert (
        "- [x] **Step 5: Commit repair-session, publishing, and executor bridge**"
        in release_plan
    )
    assert (
        "- [x] **Step 6: Commit docs, examples, templates, and release reports last**"
        in release_plan
    )

    for commit in (
        "7d39e3e feat: add runner repair and verification foundations",
        "001e719 feat: expand benchmark coverage for typescript and deep policy cases",
        "a32e7fc feat: add self-inspection backlog and task selection workflow",
        "112b98e feat: add autonomy planning loops and loop artifacts",
        "ee4a4e1 feat: add repair session workflow and verification publishing",
        "a52d01e feat: add executor bridge packaging for external repair workflows",
        "0427add docs: add worktree triage and commit plan reports",
    ):
        assert commit in release_plan


def test_alpha_publish_handoff_pins_remote_blocker_and_next_commands() -> None:
    release_plan = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-18-github-repository-release.md"
    ).read_text(encoding="utf-8")
    release_notes = (ROOT / "docs" / "releases" / "v0.9.8-alpha.md").read_text(
        encoding="utf-8"
    )
    release_handoff = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-publish-handoff.md"
    ).read_text(encoding="utf-8")
    launch_plan = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-19-github-repository-launch.md"
    ).read_text(encoding="utf-8")

    assert "docs/releases/v0.9.8-alpha-publish-handoff.md" in release_plan
    assert "first public alpha release" in release_notes
    assert "configured `origin` remote" in release_handoff
    assert "qazedhq/qa-z" in release_handoff
    assert "public GitHub prerelease was created" in release_handoff
    assert "GitHub prerelease `QA-Z v0.9.8-alpha` is published" in (release_handoff)
    assert "https://github.com/qazedhq/qa-z/releases/tag/v0.9.8-alpha" in (
        release_handoff
    )
    assert "GitHub Actions run `25050794900`" in release_handoff
    assert "`1212 passed`" in release_handoff
    assert "`507` mypy source files" in release_handoff
    assert "`519 files" in release_handoff
    assert "`0` forbidden files" in release_handoff
    assert "No PyPI, TestPyPI, or package-registry publish was performed" in (
        release_handoff
    )
    assert "https://github.com/qazedhq/qa-z.git" in release_handoff
    assert "git remote add origin <repository-url>" in release_handoff
    assert "git ls-remote --refs <repository-url>" in release_handoff
    assert "GitHub API metadata reports a public `qazedhq/qa-z`" in release_handoff
    assert "--expected-repository <owner/repo>" in release_handoff
    assert "--expected-origin-url <repository-url>" in release_handoff
    assert "python scripts/alpha_release_gate.py --include-remote" in release_handoff
    assert "HTTPS, SSH, and schemeless" in (release_handoff)
    assert "github.com/owner/repo.git" in release_handoff
    assert "existing remote `v0.9.8-alpha` tag" in release_handoff
    assert "python scripts/alpha_release_preflight.py --skip-remote" in release_handoff
    assert "python scripts/alpha_release_gate.py --json" in release_handoff
    assert "one-shot local alpha release gate" in release_handoff
    assert (
        "python scripts/alpha_release_preflight.py --skip-remote --json"
        in release_handoff
    )
    assert (
        "python scripts/alpha_release_preflight.py --repository-url <repository-url>"
        in release_handoff
    )
    assert (
        "python scripts/alpha_release_preflight.py --repository-url <repository-url> --json"
        in release_handoff
    )
    assert (
        "python scripts/alpha_release_preflight.py --repository-url <repository-url> --expected-origin-url <repository-url>"
        in release_handoff
    )
    assert (
        "python scripts/alpha_release_preflight.py --repository-url <repository-url> --allow-existing-refs"
        in release_handoff
    )
    assert (
        "python scripts/alpha_release_preflight.py --repository-url <repository-url> --allow-existing-refs --json"
        in release_handoff
    )
    assert "machine-readable" in release_handoff
    assert "operator evidence" in release_handoff
    assert "returns the same exit code" in release_handoff
    assert "--allow-existing-refs" in launch_plan
    assert "release PR path" in launch_plan
    assert (
        "If `origin` is absent in a fresh clone, add it only after this command succeeds"
        in release_handoff
    )
    assert "git push -u origin HEAD:<repository_default_branch>" in release_handoff
    assert "git push -u origin codex/qa-z-bootstrap" in release_handoff
    assert "Release QA-Z v0.9.8-alpha" in release_handoff
    assert "docs/releases/v0.9.8-alpha-pr.md" in release_handoff
    assert "docs/releases/v0.9.8-alpha-github-release.md" in release_handoff
    assert "Annotated tag `v0.9.8-alpha` exists locally and remotely" in (
        release_handoff
    )
    assert "git tag -s v0.9.8-alpha -m" in release_handoff
    assert "git tag -v v0.9.8-alpha" in release_handoff
    assert "git tag -a v0.9.8-alpha -m" in release_handoff
    assert "title: `QA-Z v0.9.8-alpha`" in release_handoff
    assert "python -m qa_z benchmark --json" in release_handoff
    assert "python scripts/alpha_release_bundle_manifest.py --json" in release_handoff
    assert (
        "Package-build validation commit: "
        "`f009d14 chore: add release build validation tooling`"
    ) in release_handoff
    assert (
        "CI package-build gate commit: "
        "`b2cdc07 ci: verify package build before alpha release`"
    ) in release_handoff
    assert "Build package artifacts" in release_handoff
    assert "Smoke test built package artifacts" in release_handoff
    assert "artifact install smoke step passes inside the `test` job" in release_handoff
    assert (
        "git clone --branch codex/qa-z-bootstrap "
        "dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle"
    ) in release_handoff
    assert (
        "Generated artifact hashes are intentionally not pinned in this tracked handoff"
        in release_handoff
    )
    assert "Get-FileHash -Algorithm SHA256" in release_handoff
    assert "git bundle create" in release_handoff
    assert "git bundle verify" in release_handoff
    assert "git bundle list-heads" in release_handoff
    assert "git rev-parse HEAD" in release_handoff
    assert "GitHub prerelease `QA-Z v0.9.8-alpha` is published" in (release_handoff)
    assert "SHA256: `" not in release_handoff
    for artifact in (
        "dist/qa_z-0.9.8a0.tar.gz",
        "dist/qa_z-0.9.8a0-py3-none-any.whl",
        "dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle",
    ):
        assert artifact in release_handoff


def test_live_remote_blocker_recheck_is_captured_in_state_and_plan_docs() -> None:
    current_state = (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "reports" / "next-improvement-roadmap.md").read_text(
        encoding="utf-8"
    )
    blocker_plan = (
        ROOT
        / "docs"
        / "superpowers"
        / "plans"
        / "2026-04-24-remote-publish-path-blocker-recheck.md"
    ).read_text(encoding="utf-8")

    assert "GitHub Actions run `25050794900`" in current_state
    assert "remote `main` advanced to" in current_state
    assert "public GitHub prerelease now exists" in current_state
    assert "no PyPI, TestPyPI, or package-registry publish" in (current_state)

    assert "2026-04-28: Published `QA-Z v0.9.8-alpha`" in roadmap
    assert "GitHub Actions run `25050794900` succeeded" in roadmap
    assert "No PyPI, TestPyPI, or package-registry publish was performed" in (roadmap)

    assert "# QA-Z Remote Publish Path Blocker Recheck" in blocker_plan
    assert "- type: EXTERNAL + ACCESS" in blocker_plan
    assert "`remote_blocker=repository_missing`" in blocker_plan
    assert "installed GitHub accounts still show only `ggbu75769-dot`" in (blocker_plan)
    assert "visible GitHub org membership is empty" in blocker_plan
    assert "git ls-remote --refs https://github.com/qazedhq/qa-z.git" in blocker_plan
    assert "remote: Repository not found." in blocker_plan
