"""Tests for shipped GitHub workflow QA-Z gate shape."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def test_github_workflow_builds_package_artifacts_after_tests() -> None:
    """Release CI should prove package artifacts build and install-smoke."""
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    steps: list[dict[str, Any]] = workflow["jobs"]["test"]["steps"]
    runs = [step.get("run", "") for step in steps]

    install_position = runs.index("python -m pip install -e .[dev]")
    format_position = runs.index("python -m ruff format --check src tests scripts")
    lint_position = runs.index("python -m ruff check src tests scripts")
    mypy_position = runs.index("python -m mypy src tests")
    test_position = runs.index("python -m pytest")
    build_position = runs.index("python -m build --sdist --wheel")
    smoke_position = runs.index("python scripts/alpha_release_artifact_smoke.py --json")
    benchmark_position = runs.index(
        "python -m qa_z benchmark --results-dir benchmarks/results-ci --json"
    )

    assert (
        install_position
        < format_position
        < lint_position
        < mypy_position
        < test_position
        < build_position
        < smoke_position
        < benchmark_position
    )


def test_github_workflow_runs_benchmark_into_ignored_results_dir() -> None:
    """The release benchmark gate should not create tracked runtime evidence."""
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    steps: list[dict[str, Any]] = workflow["jobs"]["test"]["steps"]
    runs = [step.get("run", "") for step in steps]
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")

    assert "python -m qa_z benchmark --results-dir benchmarks/results-ci --json" in (
        runs
    )
    assert "benchmarks/results-*" in gitignore


def test_github_workflow_uploads_benchmark_report_artifacts() -> None:
    """Benchmark failures should leave concise CI evidence for operators."""
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )
    steps: list[dict[str, Any]] = workflow["jobs"]["test"]["steps"]

    artifact_step = next(
        step
        for step in steps
        if step.get("name") == "Upload benchmark report artifacts"
    )

    assert artifact_step.get("if") == "${{ always() }}"
    assert artifact_step.get("uses") == "actions/upload-artifact@v4"
    artifact_config = artifact_step.get("with", {})
    assert artifact_config.get("name") == "qa-z-benchmark-report"
    assert artifact_config.get("path", "").strip() == (
        "benchmarks/results-ci/summary.json\nbenchmarks/results-ci/report.md"
    )
    assert artifact_config.get("retention-days") == 7
    assert artifact_config.get("if-no-files-found") == "warn"


def test_codex_review_prep_uses_read_only_permissions() -> None:
    """Review prep only writes a job summary, so PR write permission is unnecessary."""
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "codex-review.yml").read_text(
            encoding="utf-8"
        )
    )
    permissions = workflow["jobs"]["review-prep"]["permissions"]

    assert permissions == {"contents": "read", "pull-requests": "read"}


def test_ci_jobs_use_explicit_least_privilege_permissions() -> None:
    """Every CI job should declare the workflow token scope it needs."""
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    )

    assert workflow["jobs"]["test"]["permissions"] == {"contents": "read"}
    assert workflow["jobs"]["qa-z"]["permissions"] == {
        "actions": "read",
        "contents": "read",
        "security-events": "write",
    }


@pytest.mark.parametrize(
    ("workflow_path", "runner_command", "run_dir"),
    [
        (".github/workflows/ci.yml", "python -m qa_z", ".qa-z/runs/ci"),
        ("templates/.github/workflows/vibeqa.yml", "qa-z", ".qa-z/runs/pr"),
    ],
)
def test_github_workflow_runs_deep_before_consumers_and_fails_last(
    workflow_path: str, runner_command: str, run_dir: str
) -> None:
    """The GitHub gate should preserve artifacts before applying the verdict."""
    workflow = yaml.safe_load((ROOT / workflow_path).read_text(encoding="utf-8"))
    jobs = workflow["jobs"]
    qa_job = next(job for job in jobs.values() if has_qa_z_gate(job))
    steps: list[dict[str, Any]] = qa_job["steps"]
    step_runs = [step.get("run", "") for step in steps]
    combined_runs = "\n".join(step_runs)
    workflow_text = (ROOT / workflow_path).read_text(encoding="utf-8")

    assert "deterministic CI gate" in workflow_text
    assert "preserves local artifacts before applying the fast/deep verdict" in (
        workflow_text
    )
    assert "does not call live executors" in workflow_text
    assert "does not create branches, commits, pushes, or bot comments" in workflow_text
    assert "does not ingest executor results" in workflow_text
    assert "does not perform autonomous repair" in workflow_text

    expected_commands = [
        f"{runner_command} fast",
        f"{runner_command} deep",
        f"{runner_command} review",
        f"{runner_command} repair-prompt",
        f"{runner_command} github-summary",
    ]
    command_positions = [combined_runs.index(command) for command in expected_commands]

    assert command_positions == sorted(command_positions)
    assert f"{run_dir}/fast-exit-code" in combined_runs
    assert f"{run_dir}/deep-exit-code" in combined_runs
    assert f"{run_dir}/deep/results.sarif" in workflow_text
    assert f"{runner_command} deep --selection smart --from-run {run_dir} --json" in (
        combined_runs
    )
    assert f"{runner_command} review --from-run {run_dir}" in combined_runs
    assert f"{runner_command} repair-prompt --from-run {run_dir}" in combined_runs
    assert f"{runner_command} github-summary --from-run {run_dir}" in combined_runs
    assert "fast_exit" in combined_runs
    assert "deep_exit" in combined_runs

    sarif_step = next(
        step
        for step in steps
        if step.get("uses") == "github/codeql-action/upload-sarif@v4"
    )
    assert sarif_step.get("if") == "${{ always() }}"
    assert sarif_step.get("with", {}).get("sarif_file") == (
        f"{run_dir}/deep/results.sarif"
    )
    assert "security-events" in qa_job.get("permissions", {})

    artifact_step = next(
        step for step in steps if step.get("uses") == "actions/upload-artifact@v4"
    )
    assert artifact_step.get("if") == "${{ always() }}"
    artifact_config = artifact_step.get("with", {})
    assert artifact_config.get("path").strip() == run_dir
    assert artifact_config.get("retention-days") == 7

    verdict_step = steps[-1]
    assert verdict_step.get("if") == "${{ always() }}"
    assert f"{run_dir}/fast-exit-code" in verdict_step["run"]
    assert f"{run_dir}/deep-exit-code" in verdict_step["run"]
    assert "exit 1" in verdict_step["run"]


def has_qa_z_gate(job: dict[str, Any]) -> bool:
    """Return true when a job contains the QA-Z fast gate."""
    return any(" fast" in step.get("run", "") for step in job.get("steps", []))
