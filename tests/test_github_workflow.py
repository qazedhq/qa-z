"""Tests for shipped GitHub workflow QA-Z gate shape."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


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
    assert "fast_exit" in combined_runs
    assert "deep_exit" in combined_runs

    sarif_step = next(
        step
        for step in steps
        if step.get("uses") == "github/codeql-action/upload-sarif@v3"
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

    verdict_step = steps[-1]
    assert verdict_step.get("if") == "${{ always() }}"
    assert f"{run_dir}/fast-exit-code" in verdict_step["run"]
    assert f"{run_dir}/deep-exit-code" in verdict_step["run"]
    assert "exit 1" in verdict_step["run"]


def has_qa_z_gate(job: dict[str, Any]) -> bool:
    """Return true when a job contains the QA-Z fast gate."""
    return any(" fast" in step.get("run", "") for step in job.get("steps", []))
