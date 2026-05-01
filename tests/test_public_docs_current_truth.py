from __future__ import annotations

from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


def read_readme() -> str:
    return (ROOT / "README.md").read_text(encoding="utf-8")


def read_docs_index() -> str:
    return (ROOT / "docs" / "README.md").read_text(encoding="utf-8")


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


def read_current_state() -> str:
    return (ROOT / "docs" / "reports" / "current-state-analysis.md").read_text(
        encoding="utf-8"
    )


def test_readme_local_setup_and_command_surface_match_current_cli() -> None:
    readme = read_readme()

    assert "python -m pip install semgrep" in readme
    assert "qa-z deep --from-run .qa-z/runs/baseline" in readme
    for command in (
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
        "[GitHub Action](github-action.md)",
        "[Use with Codex](use-with-codex.md)",
        "[Use with Claude Code](use-with-claude-code.md)",
        "[Use with Cursor](use-with-cursor.md)",
        "[Launch package](launch-package.md)",
        "[Launch posts](launch-posts.md)",
        "[Product direction](product/PRODUCT_DIRECTION.md)",
        "[V8 handoff](product/V8_HANDOFF.md)",
        "[Product decisions](product/PRODUCT_DECISIONS.md)",
        "[Benchmarking](benchmarking.md)",
    ):
        assert link in docs_index


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

    assert "GitHub Security Advisory" in security_policy
    assert "Do not include live secrets in public issues" in security_policy


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
