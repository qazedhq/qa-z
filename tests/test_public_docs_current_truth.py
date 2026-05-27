from __future__ import annotations

import subprocess
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
TESTPYPI_UPLOAD_PROOF_PATH = (
    "docs/reports/v0.10.0-beta-testpypi-rehearsal-upload-proof.md"
)
PYPI_READINESS_PATH = "docs/reports/v0.10.0-beta-pypi-readiness.md"
PRODUCTION_GO_NO_GO_PATH = "docs/reports/v0.18-production-pypi-go-no-go.md"
PYPI_RELEASE_NOTES_DRAFT_PATH = "docs/releases/v0.10.0-beta-release-notes-draft.md"


def read_readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def read_docs_index() -> str:
    return (ROOT / "docs" / "README.md").read_text(encoding="utf-8")


def read_quickstart() -> str:
    return (ROOT / "docs" / "quickstart.md").read_text(encoding="utf-8")


def read_benchmarking_docs() -> str:
    return (ROOT / "docs" / "benchmarking.md").read_text(encoding="utf-8")


def read_security_policy() -> str:
    return (ROOT / "SECURITY.md").read_text(encoding="utf-8")


def read_good_first_issues() -> str:
    return (ROOT / "docs" / "issues" / "good-first-issues.md").read_text(
        encoding="utf-8"
    )


def read_semgrep_docs() -> str:
    return (ROOT / "docs" / "use-with-semgrep.md").read_text(encoding="utf-8")


def read_testpypi_upload_proof() -> str:
    return (ROOT / TESTPYPI_UPLOAD_PROOF_PATH).read_text(encoding="utf-8")


def read_pypi_readiness() -> str:
    return (ROOT / PYPI_READINESS_PATH).read_text(encoding="utf-8")


def read_current_state() -> str:
    return (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )


def git_tracked_paths(*paths: str) -> set[str]:
    completed = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "--", *paths],
        check=True,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return set(completed.stdout.splitlines())


def test_readme_local_setup_and_command_surface_match_current_cli() -> None:
    readme = read_readme()

    assert "Make AI coding safe to merge." in readme
    assert "deterministic merge evidence" in readme
    assert "Run the auth-bug demo from the GitHub source install" in readme
    assert "pipx install git+https://github.com/qazedhq/qa-z.git" in readme
    assert "Verdict: do_not_merge" in readme
    assert "Reason: auth/owner-check risk detected" in readme
    assert "Next: use the generated repair prompt, then run qa-z verify" in readme
    assert "After the CLI demo, the next step is a copy-paste PR gate" in readme
    assert (
        "minimal PR gate, PR summary/artifacts, SARIF upload opt-in, and "
        "troubleshooting FAQ"
    ) in readme
    assert "`security-events: write` only when SARIF upload is explicitly enabled" in (
        readme
    )
    assert "bot comments stay opt-in" in readme
    assert "python -m pip install semgrep" in readme
    assert "qa-z deep --from-run .qa-z/runs/baseline" in readme
    assert "qa-z scorecard" in readme
    assert "verdict `improved`" in readme
    assert "no regressions" in readme
    for forbidden in (
        "pipx install qa-z",
        "uv tool install qa-z",
        "PyPI package available",
        "Install from PyPI",
    ):
        assert forbidden not in readme
    for command in (
        "`qa-z self-inspect`",
        "`qa-z select-next`",
        "`qa-z backlog`",
        "`qa-z autonomy`",
        "`qa-z executor-bridge`",
        "`qa-z executor-result`",
    ):
        assert command in readme


def test_root_config_referenced_adapter_instruction_files_exist() -> None:
    root_config = yaml.safe_load((ROOT / "qa-z.yaml").read_text(encoding="utf-8"))

    for adapter in root_config["adapters"].values():
        if adapter.get("enabled") is False:
            continue
        instructions_file = adapter.get("instructions_file")
        assert instructions_file
        assert (ROOT / instructions_file).is_file()


def test_readme_links_product_direction_docs() -> None:
    readme = read_readme()

    for link in (
        "[Product direction](docs/product/PRODUCT_DIRECTION.md)",
        "[V8 handoff](docs/product/V8_HANDOFF.md)",
        "[Product decisions](docs/product/PRODUCT_DECISIONS.md)",
        "[Benchmarking](docs/benchmarking.md)",
    ):
        assert link in readme


def test_pyproject_metadata_uses_public_launch_positioning() -> None:
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'description = "Deterministic QA gates for AI coding agents."' in pyproject
    for keyword in (
        "ai",
        "code-review",
        "devsecops",
        "qa",
        "testing",
        "ci",
        "ai-agents",
        "coding-agents",
        "codex",
        "claude",
        "cursor",
        "semgrep",
        "sarif",
        "static-analysis",
        "quality-assurance",
    ):
        assert f'"{keyword}"' in pyproject


def test_docs_index_links_production_readiness_docs() -> None:
    docs_index = read_docs_index()

    for link in (
        "[Quickstart](quickstart.md)",
        "[Comparison](comparison.md)",
        "[Agent adapters](agent-adapters.md)",
        "[GitHub Action](github-action.md)",
        "[Evidence summary](evidence-summary.md)",
        "[Repair -> verify workflow](repair-verify-workflow.md)",
        "[Scorecards](../docs/scorecard.md)",
        "[Use with Codex](use-with-codex.md)",
        "[Use with Claude Code](use-with-claude-code.md)",
        "[Use with Cursor](use-with-cursor.md)",
        "[Launch kit](launch/launch-kit.md)",
        "[Launch package](launch-package.md)",
        "[Launch posts](launch-posts.md)",
        "[Product direction](product/PRODUCT_DIRECTION.md)",
        "[V8 handoff](product/V8_HANDOFF.md)",
        "[Product decisions](product/PRODUCT_DECISIONS.md)",
        "[Benchmarking](benchmarking.md)",
    ):
        assert link in docs_index


def test_quickstart_states_repair_verification_success_signal() -> None:
    quickstart = read_quickstart()

    assert "qa-z verify --from-run .qa-z/runs/baseline" in quickstart
    assert "qa-z verify --from-run latest --config qa-z.demo.yaml" in quickstart
    assert "qa-z summary --from-run latest" in quickstart
    assert "verdict `improved`" in quickstart
    assert "no regressions" in quickstart


def test_evidence_summary_docs_pin_local_first_read_boundary() -> None:
    docs = (ROOT / "docs" / "evidence-summary.md").read_text(encoding="utf-8")

    for phrase in (
        "qa-z summary --from-run latest",
        "qa-z summary --from-run latest --json",
        "qa-z summary --from-run latest --markdown",
        "qa-z verify --from-run latest",
        "status",
        "verdict",
        "top_findings",
        "repair_prompt",
        "verify_report",
        "next_actions",
        "warnings",
        "live PyPI package",
    ):
        assert phrase in docs
    for forbidden in (
        "pipx install qa-z",
        "uv tool install qa-z",
        "PyPI package available",
        "Install from PyPI",
    ):
        assert forbidden not in docs


def test_public_docs_point_to_latest_github_prerelease_without_package_publish() -> (
    None
):
    readme = read_readme()
    quickstart = read_quickstart()
    package_plan = (ROOT / "docs" / "package-publish-plan.md").read_text(
        encoding="utf-8"
    )
    roadmap = (ROOT / "docs" / "roadmap.md").read_text(encoding="utf-8")
    launch_checklist = (ROOT / "docs" / "launch-checklist.md").read_text(
        encoding="utf-8"
    )
    launch_package = (ROOT / "docs" / "launch-package.md").read_text(encoding="utf-8")
    product_direction = (ROOT / "docs" / "product" / "PRODUCT_DIRECTION.md").read_text(
        encoding="utf-8"
    )
    v8_handoff = (ROOT / "docs" / "product" / "V8_HANDOFF.md").read_text(
        encoding="utf-8"
    )
    action = yaml.safe_load(
        (ROOT / ".github" / "actions" / "qa-z" / "action.yml").read_text(
            encoding="utf-8"
        )
    )
    release_notes = (ROOT / "docs" / "releases" / "v0.9.9-alpha.md").read_text(
        encoding="utf-8"
    )

    assert "https://github.com/qazedhq/qa-z/releases/tag/v0.9.9-alpha" in readme
    assert "https://github.com/qazedhq/qa-z/releases/tag/v0.9.8-alpha" not in readme
    for text in (quickstart, package_plan):
        assert "git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha" in text
    assert "No GitHub Release has been created yet" not in release_notes
    assert "No tag has been pushed yet" not in release_notes
    assert "This should be created" not in release_notes
    assert "GitHub prerelease created for `v0.9.9-alpha`." in release_notes
    assert "Annotated `v0.9.9-alpha` tag pushed and targeting" in release_notes
    assert "This release is a GitHub prerelease only." in release_notes
    assert "Package publish: none" in release_notes
    assert (
        "`qa-z guard`."
        in roadmap.split("## v0.9.9-alpha", 1)[1].split("## v0.10.0-beta", 1)[0]
    )
    assert "Package-publish readiness." in roadmap.split("## v0.10.0-beta", 1)[1]
    assert "GitHub prerelease: present for `v0.9.9-alpha`" in launch_checklist
    assert "v0.9.9-alpha post-release maintenance." in launch_checklist
    assert "GitHub prerelease exists for `v0.9.9-alpha`" in launch_package
    assert "source package metadata is `0.10.0b0`" in product_direction
    assert "Historical TestPyPI proof remains `qa-z==0.9.8a0`" in product_direction
    assert "Latest GitHub prerelease: `v0.9.9-alpha`" in product_direction
    assert "source package metadata `0.10.0b0`" in v8_handoff
    assert "historical TestPyPI proof at `qa-z==0.9.8a0`" in v8_handoff
    assert "latest GitHub prerelease `v0.9.9-alpha`" in v8_handoff
    assert action["inputs"]["qa-z-install"]["default"] == (
        "git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha"
    )


def test_testpypi_upload_proof_documents_registry_and_security_boundary() -> None:
    proof_path = ROOT / TESTPYPI_UPLOAD_PROOF_PATH
    assert proof_path.exists()

    proof = read_testpypi_upload_proof()
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    for section in (
        "## Purpose",
        "## Upload Result",
        "## TestPyPI URL",
        "## Uploaded Artifacts",
        "## Install Smoke Result",
        "## Registry Boundary",
        "## Explicit Non-actions",
        "## Security Boundary",
        "## Remaining Blockers Before PyPI",
        "## Recommended Next Step",
    ):
        assert section in proof

    for required in (
        "TestPyPI upload completed.",
        "https://test.pypi.org/project/qa-z/0.9.8a0/",
        "`registry_upload_executed=true` for TestPyPI only.",
        "PyPI upload did not occur.",
        "Production PyPI remains out of scope.",
        "No tag, GitHub Release, deploy, or version bump occurred.",
        "Credential values are not included.",
        "QAZ_TOKEN.txt must not be committed.",
        "dist artifacts are generated evidence only and must not be committed.",
        "`pipx install qa-z` is still not a live PyPI install claim.",
        "TestPyPI install uses TestPyPI index, not production PyPI.",
    ):
        assert required in proof

    for artifact in (
        "dist/qa_z-0.9.8a0.tar.gz",
        "dist/qa_z-0.9.8a0-py3-none-any.whl",
    ):
        assert artifact in proof

    assert "QAZ_TOKEN.txt" in gitignore
    assert (
        git_tracked_paths(
            "QAZ_TOKEN.txt",
            "dist/qa_z-0.9.8a0.tar.gz",
            "dist/qa_z-0.9.8a0-py3-none-any.whl",
        )
        == set()
    )


def test_package_publish_plan_documents_testpypi_upload_proof() -> None:
    package_plan = (ROOT / "docs" / "package-publish-plan.md").read_text(
        encoding="utf-8"
    )
    release_handoff = (
        ROOT / "docs" / "releases" / "v0.9.8-alpha-publish-handoff.md"
    ).read_text(encoding="utf-8")

    heading = "## TestPyPI Publish Rehearsal Checklist - Local Only"
    assert heading in package_plan
    rehearsal = package_plan.split(heading, 1)[1].split("Blocked upload packet:", 1)[0]
    blocked_upload = package_plan.split("Blocked upload packet:", 1)[1].split(
        "## v0.10.0-beta", 1
    )[0]

    for command in (
        "python -m build --sdist --wheel",
        "python scripts\\alpha_release_artifact_smoke.py --with-deps --json",
        "python scripts\\package_smoke_rehearsal.py --json --allow-missing-tools",
    ):
        assert command in rehearsal

    assert "twine upload" not in rehearsal
    assert "uv publish" not in rehearsal
    assert "`registry_upload_executed=false`" in rehearsal
    assert "discovers exactly one `dist/*.whl`" in rehearsal
    assert "`PASS` means the local command passed" in rehearsal
    assert "`FAIL` means an available local command failed" in rehearsal
    assert "`NOT RUN` means the tool" in rehearsal
    assert "It does not install global tools." in rehearsal
    assert TESTPYPI_UPLOAD_PROOF_PATH in package_plan
    assert "TestPyPI package URL: https://test.pypi.org/project/qa-z/0.9.8a0/" in (
        package_plan
    )
    assert "`registry_upload_executed=true` for TestPyPI only." in package_plan
    assert "PyPI upload did not occur." in package_plan
    assert "No TestPyPI package URL exists yet." not in package_plan
    assert "No package registry publish has happened yet." not in package_plan
    assert (
        "GitHub prerelease credentials do not authorize TestPyPI or PyPI upload."
        in package_plan
    )
    assert (
        "TestPyPI and PyPI credentials are registry-owned release credentials."
        in package_plan
    )
    assert "python -m twine upload --repository testpypi dist/*" in blocked_upload
    assert "python -m twine upload dist/*" in blocked_upload
    assert (
        "TestPyPI rehearsal stays local-only; registry upload remains blocked."
        in release_handoff
    )


def test_related_release_docs_link_testpypi_upload_proof() -> None:
    for doc_path in (
        "docs/releases/v0.9.8-alpha-publish-handoff.md",
        "docs/reports/v0.10.0-beta-testpypi-rehearsal-go-no-go.md",
        "docs/reports/v0.10.0-beta-testpypi-rehearsal-execution-packet.md",
        "docs/reports/v0.10.0-beta-testpypi-rehearsal-approval.md",
        "docs/reports/v0.10.0-beta-release-execution-checklist.md",
    ):
        doc = (ROOT / doc_path).read_text(encoding="utf-8")
        text = " ".join(doc.split())

        assert TESTPYPI_UPLOAD_PROOF_PATH in doc
        assert "TestPyPI" in doc
        assert "PyPI upload did not occur" in text
        assert "v0.10.0-beta" in doc


def test_pypi_conversion_readiness_pack_keeps_public_truth_blocked() -> None:
    readme = read_readme()
    package_plan = (ROOT / "docs/package-publish-plan.md").read_text(encoding="utf-8")
    readiness = read_pypi_readiness()
    go_no_go = (ROOT / PRODUCTION_GO_NO_GO_PATH).read_text(encoding="utf-8")
    release_notes = (ROOT / PYPI_RELEASE_NOTES_DRAFT_PATH).read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    combined = "\n".join([package_plan, readiness, release_notes, go_no_go])
    combined_text = " ".join(combined.split())

    assert (ROOT / PYPI_READINESS_PATH).exists()
    assert (ROOT / PRODUCTION_GO_NO_GO_PATH).exists()
    assert (ROOT / PYPI_RELEASE_NOTES_DRAFT_PATH).exists()
    assert 'version = "0.10.0b0"' in pyproject
    assert "pipx install qa-z" not in readme
    assert "uv tool install qa-z" not in readme
    assert PRODUCTION_GO_NO_GO_PATH in package_plan
    assert "Decision: `NO_GO_MISSING_APPROVAL`" in go_no_go
    assert "Secondary decision: `NO_GO_MISSING_CREDENTIALS`" in go_no_go
    assert "`production_pypi_upload_executed=false`" in go_no_go
    assert "README transition status: unchanged." in go_no_go
    assert "https://test.pypi.org/project/qa-z/0.9.8a0/" in readiness
    assert (
        "`registry_upload_executed=true` applies to TestPyPI `0.9.8a0` only."
        in readiness
    )
    assert "Current source metadata: `qa-z` / `0.10.0b0`." in readiness
    assert "Historical TestPyPI proof remains `qa-z==0.9.8a0`." in readiness
    assert "Owner-approved package metadata version: `0.10.0b0`." in readiness
    assert "Production PyPI has not been published." in readiness
    assert "Production PyPI is not published." in release_notes
    assert "Draft only - not a GitHub Release." in release_notes

    for false_claim in (
        "Production PyPI publish completed",
        "PyPI upload completed",
        "PyPI install is live",
        "live PyPI install is available",
        "v0.10.0-beta is released",
        "published to PyPI",
        "production_pypi_upload_executed=true",
    ):
        assert false_claim not in combined_text


def test_launch_package_points_to_complete_good_first_issue_seed_set() -> None:
    launch_package = (ROOT / "docs" / "launch-package.md").read_text(encoding="utf-8")
    issue_seeds = (ROOT / "docs" / "issues" / "good-first-issues.md").read_text(
        encoding="utf-8"
    )

    assert "docs/issues/good-first-issues.md" in launch_package
    assert "20 detailed good-first-issue seeds" in launch_package
    assert issue_seeds.count("## Issue ") >= 20


def test_benchmarking_docs_include_ci_safe_results_dir() -> None:
    benchmarking_docs = read_benchmarking_docs()

    assert (
        "python -m qa_z benchmark --results-dir benchmarks/results-ci --json"
        in benchmarking_docs
    )
    assert "benchmarks/results-*" in benchmarking_docs


def test_security_policy_names_private_disclosure_path() -> None:
    security_policy = read_security_policy()
    support = (ROOT / "SUPPORT.md").read_text(encoding="utf-8")

    assert "GitHub Security Advisory" in security_policy
    assert "Do not include live secrets in public issues" in security_policy
    assert "[SUPPORT.md](SUPPORT.md)" in security_policy
    assert "Release, package, tag, or deploy approvals" in support
    assert "QA-Z does not edit target repositories" in support


def test_readme_contributing_section_links_community_health_files() -> None:
    readme = read_readme()
    contributing = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")

    readme_contributing = readme.split("## Contributing", 1)[1].split("## License", 1)[
        0
    ]
    for link in (
        "[CONTRIBUTING.md](CONTRIBUTING.md)",
        "[SUPPORT.md](SUPPORT.md)",
        "[SECURITY.md](SECURITY.md)",
        "[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)",
    ):
        assert link in readme_contributing
    assert "[SUPPORT.md](SUPPORT.md)" in contributing
    assert "[SECURITY.md](SECURITY.md)" in contributing


def test_current_state_snapshot_includes_doctor_onboarding_validation() -> None:
    current_state = read_current_state()

    assert "config and onboarding validation with `doctor`" in current_state


def test_public_docs_match_current_sarif_upload_action_version() -> None:
    docs = "\n".join(
        [
            (ROOT / "docs" / "artifact-schema-v1.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "mvp-issues.md").read_text(encoding="utf-8"),
        ]
    )

    assert "github/codeql-action/upload-sarif@v4" in docs
    assert "github/codeql-action/upload-sarif@v3" not in docs


def test_good_first_issue_validation_commands_use_repo_local_run_dirs() -> None:
    issues = read_good_first_issues()

    assert "%TEMP%" not in issues
    for run_dir in (
        ".qa-z/runs/qa-z-fastapi-agent-bug",
        ".qa-z/runs/qa-z-auth-deep",
        ".qa-z/runs/qa-z-ts-agent-bug",
        ".qa-z/runs/qa-z-fastapi-agent-deep",
    ):
        assert run_dir in issues


def test_semgrep_docs_pin_deep_gate_to_explicit_baseline_run() -> None:
    semgrep_docs = read_semgrep_docs()

    for command in (
        "qa-z fast --output-dir .qa-z/runs/baseline",
        "qa-z deep --from-run .qa-z/runs/baseline",
        "qa-z review --from-run .qa-z/runs/baseline",
        "qa-z repair-prompt --from-run .qa-z/runs/baseline --adapter codex",
    ):
        assert command in semgrep_docs
    assert "qa-z deep --from-run latest" not in semgrep_docs
