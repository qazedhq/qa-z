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
    assert artifact_step.get("uses") == "actions/upload-artifact@v6"
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


def test_public_raw_hygiene_workflow_checks_branch_and_commit_urls() -> None:
    """Public raw hygiene should verify GitHub raw bytes, not only local files."""
    workflow = yaml.safe_load(
        (ROOT / ".github" / "workflows" / "public-raw-hygiene.yml").read_text(
            encoding="utf-8"
        )
    )
    triggers = workflow.get("on", workflow.get(True, {}))
    job = workflow["jobs"]["public-raw-hygiene"]
    steps: list[dict[str, Any]] = job["steps"]
    runs = [step.get("run", "") for step in steps]
    combined_runs = "\n".join(runs)

    assert {"push", "pull_request", "workflow_dispatch"} <= set(triggers)
    assert workflow["permissions"] == {"contents": "read"}
    assert job["timeout-minutes"] == 10
    assert "python scripts/check_text_file_hygiene.py --source working-tree" in runs
    assert 'current_commit="$(git rev-parse HEAD)"' in combined_runs
    assert "github.event.pull_request.head.ref || github.ref_name" in str(workflow)
    assert "github.event.pull_request.head.sha || github.sha" in str(workflow)
    assert "python scripts/check_public_raw_urls.py" in combined_runs
    assert '--repo "${{ steps.raw-target.outputs.repo }}"' in combined_runs
    assert '--ref "${{ steps.raw-target.outputs.ref }}"' in combined_runs
    assert '--commit "${{ steps.raw-target.outputs.commit }}"' in combined_runs


def test_composite_action_preserves_artifacts_before_final_verdict() -> None:
    """The reusable action should publish evidence before applying the verdict."""
    action = yaml.safe_load(
        (ROOT / ".github" / "actions" / "qa-z" / "action.yml").read_text(
            encoding="utf-8"
        )
    )
    assert action["inputs"]["qa-z-install"]["default"] == (
        "git+https://github.com/qazedhq/qa-z.git@v0.9.9-alpha"
    )
    steps: list[dict[str, Any]] = action["runs"]["steps"]
    step_names = [step.get("name", "") for step in steps]
    expected_order = [
        "Validate QA-Z config",
        "Run fast checks",
        "Run deep checks",
        "Generate review and repair artifacts",
        "Publish QA-Z job summary",
        "Upload QA-Z SARIF to code scanning",
        "Upload QA-Z run artifacts",
        "Fail if QA-Z fast or deep failed",
    ]

    positions = [step_names.index(name) for name in expected_order]
    assert positions == sorted(positions)

    for name in expected_order[2:]:
        step = steps[step_names.index(name)]
        if name == "Upload QA-Z SARIF to code scanning":
            assert step.get("if") == "${{ always() && inputs.upload-sarif == 'true' }}"
        else:
            assert step.get("if") == "${{ always() }}"

    combined_runs = "\n".join(step.get("run", "") for step in steps)
    assert "qa-z doctor --json" in combined_runs
    assert "fast_exit=${PIPESTATUS[0]}" in combined_runs
    assert "deep_exit=${PIPESTATUS[0]}" in combined_runs
    assert "${{ inputs.run-dir }}/fast-exit-code" in combined_runs
    assert "${{ inputs.run-dir }}/deep-exit-code" in combined_runs

    sarif_step = steps[step_names.index("Upload QA-Z SARIF to code scanning")]
    assert sarif_step.get("uses") == "github/codeql-action/upload-sarif@v4"
    assert sarif_step.get("continue-on-error") is True
    assert sarif_step.get("with", {}).get("sarif_file") == (
        "${{ inputs.run-dir }}/deep/results.sarif"
    )

    artifact_step = steps[step_names.index("Upload QA-Z run artifacts")]
    assert artifact_step.get("uses") == "actions/upload-artifact@v6"
    assert artifact_step.get("with", {}).get("retention-days") == 7
    assert artifact_step.get("with", {}).get("if-no-files-found") == "warn"

    verdict_step = steps[step_names.index("Fail if QA-Z fast or deep failed")]
    assert "QA-Z checks failed: fast=$fast_exit deep=$deep_exit" in verdict_step["run"]
    assert "exit 1" in verdict_step["run"]


def test_guard_action_validates_inputs_before_running_guard() -> None:
    """The guard action should fail bad inputs with actionable diagnostics."""
    action = yaml.safe_load(
        (ROOT / ".github" / "actions" / "guard" / "action.yml").read_text(
            encoding="utf-8"
        )
    )
    steps: list[dict[str, Any]] = action["runs"]["steps"]
    step_names = [step.get("name", "") for step in steps]

    validation_position = step_names.index("Validate QA-Z action inputs")
    install_position = step_names.index("Install QA-Z")
    guard_position = step_names.index("Run QA-Z guard")
    assert validation_position < install_position < guard_position

    assert action["inputs"]["from-run"]["default"] == ""
    combined_runs = "\n".join(step.get("run", "") for step in steps)
    assert 'echo "run_dir=${run_dir}" >> "$GITHUB_OUTPUT"' in combined_runs
    assert "steps.runtime.outputs.run_dir" in str(action)
    assert "Invalid QA-Z action input: ${input_name}" in combined_runs
    assert 'fail_input "profile"' in combined_runs
    assert '"default, python, typescript, monorepo"' in combined_runs
    assert 'fail_input "deep"' in combined_runs
    assert '"auto, always, never"' in combined_runs
    assert 'fail_input "adapter"' in combined_runs
    assert '"codex, claude, cursor, aider, openhands, generic, human"' in combined_runs
    assert 'fail_input "fail-on-risk"' in combined_runs
    assert 'fail_input "upload-sarif"' in combined_runs
    assert 'fail_input "from-run"' in combined_runs
    assert "docs/github-action.md#troubleshooting-faq" in combined_runs
    assert "--from-run" in combined_runs


def test_qa_z_action_validates_inputs_and_keeps_sarif_opt_in() -> None:
    """The reusable action should not attempt SARIF upload by default."""
    action = yaml.safe_load(
        (ROOT / ".github" / "actions" / "qa-z" / "action.yml").read_text(
            encoding="utf-8"
        )
    )
    steps: list[dict[str, Any]] = action["runs"]["steps"]
    step_names = [step.get("name", "") for step in steps]

    assert action["inputs"]["upload-sarif"]["default"] == "false"
    assert step_names.index("Validate QA-Z action inputs") < step_names.index(
        "Install QA-Z and Semgrep"
    )

    combined_runs = "\n".join(step.get("run", "") for step in steps)
    assert "Invalid QA-Z action input: ${input_name}" in combined_runs
    assert 'fail_input "adapter"' in combined_runs
    assert '"legacy, codex, claude, cursor, aider, openhands, generic"' in combined_runs
    assert 'fail_input "run-dir"' in combined_runs
    assert 'fail_input "upload-sarif"' in combined_runs
    assert "docs/github-action.md#troubleshooting-faq" in combined_runs

    sarif_step = steps[step_names.index("Upload QA-Z SARIF to code scanning")]
    assert sarif_step.get("if") == "${{ always() && inputs.upload-sarif == 'true' }}"


def test_optional_pr_comment_template_validates_comment_flag() -> None:
    """The optional comment template should reject ambiguous comment flags."""
    workflow = yaml.safe_load(
        (
            ROOT / "templates" / ".github" / "workflows" / "qa-z-pr-comment.yml"
        ).read_text(encoding="utf-8")
    )
    steps: list[dict[str, Any]] = workflow["jobs"]["qa-z-comment"]["steps"]
    step_names = [step.get("name", "") for step in steps]

    assert "Validate optional PR comment flag" in step_names
    validation_step = steps[step_names.index("Validate optional PR comment flag")]
    assert "Invalid QA-Z comment flag: QA_Z_POST_PR_COMMENT" in validation_step["run"]
    assert "supported values: true, false" in validation_step["run"]
    assert (
        "docs/github-action.md#pr-comments-or-bot-comments-are-missing"
        in (validation_step["run"])
    )


def test_github_action_docs_explain_composite_action_operational_contract() -> None:
    """Docs should describe the action evidence and permission behavior."""
    docs = (ROOT / "docs" / "github-action.md").read_text(encoding="utf-8")
    normalized_docs = " ".join(docs.split())

    assert docs.index("## 1. Minimal PR Gate") < docs.index(
        "## 2. PR Summary / Artifacts"
    )
    assert docs.index("## 2. PR Summary / Artifacts") < docs.index(
        "## 3. SARIF Upload Opt-In"
    )
    assert docs.index("## 3. SARIF Upload Opt-In") < docs.index(
        "## 4. Troubleshooting FAQ"
    )
    assert "This is the 5-minute copy-paste path for pull requests." in docs
    assert "Start with `contents: read` and `actions: read`." in docs
    assert (
        "The composite action validates `qa-z doctor --json`, runs the guard verdict "
        "step, then preserves the summary, optional SARIF, and QA-Z run artifacts with "
        "`always()` cleanup steps."
    ) in normalized_docs
    assert "PR comments and bot comments are opt-in." in docs
    assert "Do not enable bot comments by default." in docs
    assert (
        "SARIF upload is disabled by default because code scanning permissions can be "
        "repository-specific."
    ) in normalized_docs
    assert "Add `security-events: write` only when SARIF upload is enabled." in docs
    assert 'upload-sarif: "true"' in docs


def test_github_action_docs_troubleshooting_faq_preserves_safe_defaults() -> None:
    """Troubleshooting should not expand the default workflow boundary."""
    docs = (ROOT / "docs" / "github-action.md").read_text(encoding="utf-8")
    faq = docs.split("## 4. Troubleshooting FAQ", 1)[1]

    for heading in (
        "### Minimal workflow fails because permissions are too small or wrong",
        "### SARIF upload fails",
        "### PR comments or bot comments are missing",
        "### Where do I find the verdict, repair prompt, Job Summary, and artifacts?",
        "### Semgrep or deep checks differ between local and CI",
        "### The profile or adapter does not match my repository",
        "### Why is the PyPI-style pipx install command not shown as live?",
    ):
        assert heading in faq

    for text in (
        "permissions:\n  contents: read\n  actions: read",
        "Do not add\n`contents: write`, `pull-requests: write`, or broad default write scopes",
        "SARIF upload is optional.",
        'add `security-events: write` to the\nsame job and set `upload-sarif: "true"`',
        "QA-Z does not post pull request\ncomments by default",
        "the minimal workflow should not request\n`pull-requests: write`",
        "The uploaded\nartifact is named `qa-z-runs`",
        ".qa-z/runs/latest/guard/verdict.json",
        ".qa-z/runs/latest/repair/<adapter>.md",
        "Compare the Job Summary with the artifact files under\n`.qa-z/runs/latest/deep/`",
        "an existing `qa-z.yaml` remains the source of truth",
        "TestPyPI/PyPI publishing has not happened yet",
        "package-registry `pipx` or `uv tool` install commands are live",
        "Keep\nGitHub source installs until a separate release-owner publish path is approved\nand executed.",
    ):
        assert text in faq

    assert "pipx install qa-z is live" not in faq
    assert "PyPI package available" not in faq


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/public-raw-hygiene.yml",
        ".github/workflows/codex-review.yml",
        ".github/workflows/scorecard.yml",
        "templates/.github/workflows/vibeqa.yml",
        "templates/.github/workflows/qa-z-pr-comment.yml",
    ],
)
def test_github_workflow_jobs_have_explicit_timeouts(workflow_path: str) -> None:
    """CI jobs should fail boundedly instead of waiting on the platform default."""
    workflow = yaml.safe_load((ROOT / workflow_path).read_text(encoding="utf-8"))

    assert all(
        isinstance(job.get("timeout-minutes"), int)
        and 1 <= job["timeout-minutes"] <= 60
        for job in workflow["jobs"].values()
    )


@pytest.mark.parametrize(
    "workflow_path",
    [
        ".github/workflows/ci.yml",
        ".github/workflows/public-raw-hygiene.yml",
        ".github/workflows/codex-review.yml",
        ".github/workflows/scorecard.yml",
        "templates/.github/workflows/vibeqa.yml",
        "templates/.github/workflows/qa-z-pr-comment.yml",
    ],
)
def test_github_workflow_checkout_steps_do_not_persist_credentials(
    workflow_path: str,
) -> None:
    """Checkout tokens should not remain in git config after source checkout."""
    workflow = yaml.safe_load((ROOT / workflow_path).read_text(encoding="utf-8"))
    checkout_steps = [
        step
        for job in workflow["jobs"].values()
        for step in job.get("steps", [])
        if step.get("uses") == "actions/checkout@v6"
    ]

    assert checkout_steps
    assert all(
        step.get("with", {}).get("persist-credentials") is False
        for step in checkout_steps
    )


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
        f"{runner_command} doctor --json",
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
    assert f"{runner_command} doctor --json" in combined_runs
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
        step for step in steps if step.get("uses") == "actions/upload-artifact@v6"
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


def test_github_actions_use_node24_compatible_action_majors() -> None:
    """Repo-owned workflows should avoid known Node.js 20 runtime action majors."""
    checked_paths = [
        ".github/workflows/ci.yml",
        ".github/workflows/public-raw-hygiene.yml",
        ".github/workflows/codex-review.yml",
        ".github/workflows/scorecard.yml",
        ".github/workflows/qa-z-example.yml.example",
        ".github/actions/guard/action.yml",
        ".github/actions/qa-z/action.yml",
        "templates/.github/workflows/vibeqa.yml",
        "templates/.github/workflows/qa-z-pr-comment.yml",
    ]
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8") for path in checked_paths
    )

    for stale_action in (
        "actions/checkout@v4",
        "actions/setup-python@v5",
        "actions/setup-node@v4",
        "actions/upload-artifact@v4",
    ):
        assert stale_action not in combined

    for current_action in (
        "actions/checkout@v6",
        "actions/setup-python@v6",
        "actions/setup-node@v6",
        "actions/upload-artifact@v6",
    ):
        assert current_action in combined
