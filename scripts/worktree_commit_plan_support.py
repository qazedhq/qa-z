"""Support helpers for worktree commit plan analysis and rendering."""

from __future__ import annotations

import fnmatch
from datetime import datetime
from datetime import timezone
from pathlib import Path
from typing import Callable
from typing import NamedTuple
from typing import Sequence


def utc_timestamp() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


class BatchRule(NamedTuple):
    id: str
    title: str
    message: str
    patterns: tuple[str, ...]
    validation_commands: tuple[str, ...]


Runner = Callable[[Sequence[str], Path], tuple[int, str, str]]

OWNER_OVERRIDES = (
    (
        "planning_runtime_foundation",
        (
            "pyproject.toml",
            "mypy.ini",
            "src/qa_z/subprocess_env.py",
        ),
    ),
    (
        "self_inspection_backlog",
        (
            "src/qa_z/commands/planning.py",
            "src/qa_z/commands/planning_*.py",
            "tests/test_planning_commands.py",
        ),
    ),
    (
        "repair_session_publish",
        (
            "src/qa_z/commands/execution_repair.py",
            "src/qa_z/commands/review_github.py",
            "src/qa_z/commands/review_packet.py",
            "src/qa_z/commands/reviewing.py",
            "src/qa_z/commands/session_repair.py",
            "src/qa_z/commands/session_verify.py",
            "src/qa_z/commands/sessioning.py",
            "tests/test_verify_cli_error_contracts.py",
            "tests/test_session_commands.py",
        ),
    ),
    (
        "deep_runner_foundation",
        (
            "src/qa_z/commands/execution_runs.py",
            "src/qa_z/reporters/sarif.py",
            "src/qa_z/runners/selection_deep.py",
            "tests/test_sarif_cli.py",
        ),
    ),
    (
        "runner_contract_spine",
        (
            "src/qa_z/runners/selection.py",
            "src/qa_z/runners/selection_common.py",
            "src/qa_z/runners/selection_typescript.py",
        ),
    ),
    (
        "autonomy_loop_planner",
        ("src/qa_z/commands/runtime_autonomy.py",),
    ),
    (
        "benchmark_coverage",
        ("src/qa_z/commands/runtime_benchmark.py",),
    ),
    (
        "executor_return_path",
        (
            "src/qa_z/commands/runtime_bridge.py",
            "src/qa_z/commands/runtime_executor_result.py",
            "src/qa_z/commands/runtime_executor_result_stdout.py",
        ),
    ),
    (
        "alpha_release_closure",
        (
            "tests/test_release_script_environment.py",
            "tests/test_github_workflow.py",
        ),
    ),
    (
        "planning_runtime_foundation",
        ("tests/test_fast_gate_environment.py",),
    ),
    (
        "executor_return_path",
        ("benchmarks/fixtures/*executor*/**",),
    ),
    (
        "executor_return_path",
        ("benchmarks/fixtures/executor_result_partial_mixed_verify_candidate/**",),
    ),
    (
        "autonomy_loop_planner",
        ("src/qa_z/autonomy_selection.py",),
    ),
    (
        "repair_session_publish",
        ("src/qa_z/commands/review_github_context.py",),
    ),
    (
        "benchmark_coverage",
        ("tests/benchmark_test_support.py",),
    ),
    (
        "executor_return_path",
        (
            "tests/executor_result_test_support.py",
            "tests/test_runtime_executor_result_architecture.py",
        ),
    ),
    (
        "self_inspection_backlog",
        (
            "src/qa_z/benchmark_discovery.py",
            "src/qa_z/benchmark_signals.py",
            "src/qa_z/execution_discovery.py",
            "src/qa_z/executor_history_signals.py",
            "src/qa_z/executor_signals.py",
            "src/qa_z/report_signals.py",
            "tests/test_artifact_consistency_discovery.py",
            "tests/test_repair_signal_inputs.py",
            "tests/test_worktree_discovery_architecture.py",
            "tests/test_worktree_discovery_candidates.py",
        ),
    ),
)

BATCH_RULES = (
    BatchRule(
        id="alpha_release_closure",
        title="Alpha release closure",
        message="Keep deterministic alpha release gate and preflight changes together.",
        patterns=(
            "scripts/alpha_release_gate.py",
            "scripts/alpha_release_gate_*.py",
            "scripts/alpha_release_artifact_smoke.py",
            "scripts/alpha_release_artifact_smoke_*.py",
            "scripts/alpha_release_bundle_manifest.py",
            "scripts/alpha_release_bundle_manifest_*.py",
            "scripts/alpha_release_preflight.py",
            "scripts/alpha_release_preflight_*.py",
            "scripts/alpha_release_truth_validator.py",
            "scripts/package_smoke_rehearsal.py",
            "scripts/package_smoke_rehearsal_*.py",
            "scripts/check_public_raw_urls.py",
            "scripts/check_text_file_hygiene.py",
            ".github/workflows/*.yml",
            ".github/workflows/*.yml.example",
            ".github/actions/guard/**",
            ".github/actions/qa-z/**",
            "tests/test_alpha_release_artifact_smoke*.py",
            "tests/test_alpha_release_bundle_manifest*.py",
            "tests/alpha_release_artifact_smoke*_support.py",
            "tests/alpha_release_bundle_manifest*_support.py",
            "tests/test_alpha_release_gate*.py",
            "tests/alpha_release_gate*_support.py",
            "tests/test_alpha_release_preflight*.py",
            "tests/alpha_release_preflight*_support.py",
            "tests/test_alpha_release_truth_validator.py",
            "tests/test_package_smoke_rehearsal*.py",
            "tests/test_public_raw_urls.py",
            "tests/test_text_file_hygiene.py",
            "docs/package-publish-plan.md",
            "docs/reports/worktree-commit-plan.md",
            "docs/releases/**",
        ),
        validation_commands=(
            "python -m pytest tests/test_alpha_release_gate.py tests/test_alpha_release_gate_environment.py tests/test_alpha_release_preflight.py tests/test_alpha_release_artifact_smoke.py tests/test_package_smoke_rehearsal.py tests/test_alpha_release_bundle_manifest.py tests/test_alpha_release_truth_validator.py tests/test_release_script_environment.py tests/test_github_workflow.py tests/test_text_file_hygiene.py tests/test_public_raw_urls.py -q",
            "python scripts/alpha_release_gate.py --quick --allow-dirty --json",
            "python scripts/alpha_release_truth_validator.py --proof-head-from-packet --json --output .qa-z/tmp/alpha-release-truth-validator.json",
            "python scripts/alpha_release_gate.py --allow-dirty --json",
        ),
    ),
    BatchRule(
        id="current_truth_release_surface",
        title="Current-truth and release surfaces",
        message="Keep release-facing docs and current-truth guards aligned with the shipped surface.",
        patterns=(
            "CONTRIBUTING.md",
            "CODE_OF_CONDUCT.md",
            "SUPPORT.md",
            "SECURITY.md",
            ".github/ISSUE_TEMPLATE/**",
            ".github/PULL_REQUEST_TEMPLATE.md",
            ".github/pull_request_template.md",
            "tests/test_current_truth*.py",
            "tests/test_*current_truth*.py",
            "tests/test_beta_readiness_docs.py",
            "tests/test_beta_release_decision_docs.py",
            "tests/test_beta_version_policy_docs.py",
            "tests/test_examples.py",
            "tests/test_launch_growth_package.py",
            "docs/reports/v0.10.0-beta-readiness.md",
            "docs/reports/v0.10.0-beta-release-decision.md",
            "docs/reports/v0.10.0-beta-version-policy.md",
            "docs/product/**",
            "docs/roadmap.md",
            "docs/superpowers/plans/*github*release*.md",
            "docs/superpowers/plans/*github*launch*.md",
            "docs/launch/**",
            "docs/issues/**",
            "docs/generated-vs-frozen-evidence-policy.md",
        ),
        validation_commands=(
            "python -m pytest tests/test_current_truth.py tests/test_current_truth_architecture.py tests/test_current_truth_executor_bridge.py tests/test_current_truth_release_continuity.py tests/test_current_truth_release_handoff.py tests/test_current_truth_release_surfaces.py tests/test_current_truth_worktree_commit_plan.py tests/test_public_docs_current_truth.py tests/test_beta_readiness_docs.py tests/test_beta_release_decision_docs.py tests/test_beta_version_policy_docs.py tests/test_examples.py -q",
            "python -m qa_z --help",
        ),
    ),
    BatchRule(
        id="commit_plan_support",
        title="Commit-plan support",
        message="Keep worktree commit-plan runtime, helper seams, and tests in one reversible slice.",
        patterns=(
            "scripts/worktree_commit_plan.py",
            "scripts/worktree_commit_plan_*.py",
            "tests/test_worktree_commit_plan*.py",
            "tests/worktree_commit_plan*_support.py",
        ),
        validation_commands=(
            "python -m pytest tests/test_worktree_commit_plan.py tests/test_worktree_commit_plan_public_docs.py tests/test_worktree_commit_plan_validation_commands.py tests/test_current_truth.py -q",
            "python scripts/worktree_commit_plan.py --json --output .qa-z/tmp/worktree-commit-plan.json",
            "python scripts/worktree_commit_plan.py --summary-only --json --fail-on-generated --fail-on-cross-cutting --output .qa-z/tmp/worktree-commit-plan.json",
        ),
    ),
    BatchRule(
        id="planning_runtime_foundation",
        title="Planning and runtime foundation",
        message=(
            "Keep CLI, planning/runtime seams, and local evidence helpers together."
        ),
        patterns=(
            "src/qa_z/cli.py",
            "src/qa_z/artifacts.py",
            "src/qa_z/config.py",
            "src/qa_z/config_validation.py",
            "src/qa_z/commands",
            "src/qa_z/commands/**",
            "src/qa_z/execution_*.py",
            "src/qa_z/git_runtime.py",
            "src/qa_z/guard",
            "src/qa_z/guard/**",
            "src/qa_z/improvement_state.py",
            "src/qa_z/live_repository*.py",
            "src/qa_z/loop_history_candidates.py",
            "src/qa_z/operator_commands.py",
            "src/qa_z/report_*.py",
            "tests/__init__.py",
            "tests/ast_test_support.py",
            "tests/conftest.py",
            "tests/test_bootstrap_commands.py",
            "tests/test_cli_config_error_contracts.py",
            "tests/test_command_registry_architecture.py",
            "tests/test_config_validation.py",
            "tests/test_contract_planner.py",
            "tests/test_contract_resolution.py",
            "tests/test_coverage_gap_discovery.py",
            "tests/test_demo_json_failure_contracts.py",
            "tests/test_demo_guard_action_package.py",
            "tests/test_execution*.py",
            "tests/test_git_runtime*.py",
            "tests/test_guard_cli.py",
            "tests/test_live_repository*.py",
            "tests/test_loop_health*.py",
            "tests/test_operator_commands.py",
            "tests/test_planning_commands.py",
            "tests/test_report*.py",
            "tests/test_runtime_commands.py",
            "tests/test_init_options.py",
            "tests/test_selection_context*.py",
            "tests/test_session_commands.py",
            "tests/test_skill_install_cli.py",
            "tests/test_surface_discovery*.py",
            "tests/test_task_selection*.py",
            "src/qa_z/planner/contracts.py",
            "src/qa_z/templates/**",
            "qa/contracts/**",
            "qa-z.yaml",
        ),
        validation_commands=(
            "python -m pytest tests/test_coverage_gap_discovery.py tests/test_execution_discovery_architecture.py tests/test_execution_executor_candidates_architecture.py tests/test_execution_followup_candidates_architecture.py tests/test_fast_gate_environment.py tests/test_git_runtime_signal_inputs.py tests/test_live_repository_architecture.py tests/test_loop_health_architecture.py tests/test_loop_health_signal_inputs.py tests/test_report_freshness.py tests/test_report_freshness_architecture.py tests/test_report_signal_architecture.py tests/test_report_signal_inputs.py tests/test_selection_context_architecture.py tests/test_surface_discovery_architecture.py tests/test_task_selection_architecture.py tests/test_task_selection_evidence_architecture.py -q",
            "python -m pytest tests/test_execution_runs_error_contracts.py tests/test_guard_cli.py tests/test_operator_commands.py -q",
            "python -m qa_z self-inspect --json",
        ),
    ),
    BatchRule(
        id="deep_runner_foundation",
        title="Deep runner foundation",
        message=(
            "Keep deep/semgrep runtime seams and their direct architecture coverage together."
        ),
        patterns=(
            "src/qa_z/runners/deep.py",
            "src/qa_z/runners/deep_policy.py",
            "src/qa_z/runners/deep_runtime.py",
            "src/qa_z/runners/selection_deep.py",
            "src/qa_z/runners/semgrep.py",
            "tests/test_deep_context_architecture.py",
            "tests/test_deep_context_helper_architecture.py",
            "tests/test_deep_run_resolution.py",
            "tests/test_deep_runner_architecture.py",
            "tests/test_deep_selection.py",
            "tests/test_semgrep_normalization.py",
        ),
        validation_commands=(
            "python -m pytest tests/test_deep_run_resolution.py tests/test_semgrep_normalization.py tests/test_deep_runner_architecture.py -q",
            "python -m qa_z deep --help",
        ),
    ),
    BatchRule(
        id="runner_contract_spine",
        title="Runner contract spine",
        message=(
            "Keep shared runner models and their direct contract checks together."
        ),
        patterns=(
            "src/qa_z/runners/models.py",
            "src/qa_z/runners/checks.py",
            "src/qa_z/runners/fast.py",
            "src/qa_z/runners/python.py",
            "src/qa_z/runners/selection.py",
            "src/qa_z/runners/selection_common.py",
            "src/qa_z/runners/selection_typescript.py",
            "src/qa_z/runners/subprocess.py",
            "src/qa_z/runners/typescript.py",
            "tests/test_fast_config.py",
            "tests/test_fast_selection.py",
            "tests/test_runner_models*.py",
            "tests/test_subprocess_runner.py",
        ),
        validation_commands=(
            "python -m pytest tests/test_runner_models_contract.py tests/test_runner_models_architecture.py tests/test_fast_selection.py tests/test_subprocess_runner.py -q",
            "python -m qa_z fast --help",
        ),
    ),
    BatchRule(
        id="benchmark_coverage",
        title="Benchmark coverage",
        message="Keep benchmark runtime, fixtures, and regression evidence together.",
        patterns=(
            "src/qa_z/benchmark.py",
            "src/qa_z/benchmark_*.py",
            "tests/test_benchmark*.py",
            "benchmarks/**",
            "docs/benchmarking.md",
        ),
        validation_commands=(
            "python -m pytest tests/test_benchmark.py -q",
            "python -m qa_z benchmark --json",
        ),
    ),
    BatchRule(
        id="self_inspection_backlog",
        title="Self-inspection backlog",
        message="Keep self-inspection, selection, and backlog scoring changes together.",
        patterns=(
            "src/qa_z/self_improvement.py",
            "src/qa_z/self_improvement_*.py",
            "src/qa_z/backlog*.py",
            "src/qa_z/*discovery*.py",
            "src/qa_z/*selection*.py",
            "src/qa_z/*signals.py",
            "scripts/runtime_artifact_cleanup.py",
            "scripts/runtime_artifact_cleanup_*.py",
            "tests/test_self_improvement*.py",
            "tests/self_improvement*_support.py",
            "tests/test_runtime_artifact_cleanup*.py",
            "tests/runtime_artifact_cleanup*_support.py",
            "tests/test_cli.py",
        ),
        validation_commands=(
            "python -m pytest tests/test_self_improvement.py "
            "tests/test_self_improvement_inspection.py "
            "tests/test_self_improvement_selection_output.py "
            "tests/test_repair_signal_inputs.py "
            "tests/test_artifact_consistency_discovery.py tests/test_cli.py -q",
            "python -m qa_z self-inspect --json",
        ),
    ),
    BatchRule(
        id="autonomy_loop_planner",
        title="Autonomy loop planner",
        message="Keep autonomy loop orchestration and status surfaces together.",
        patterns=(
            "src/qa_z/autonomy.py",
            "src/qa_z/autonomy_*.py",
            "tests/test_autonomy*.py",
        ),
        validation_commands=(
            "python -m pytest tests/test_autonomy.py "
            "tests/test_autonomy_action_cleanup.py "
            "tests/test_autonomy_action_context.py tests/test_cli.py -q",
            "python -m qa_z autonomy status --json",
        ),
    ),
    BatchRule(
        id="repair_session_publish",
        title="Verification and publish path",
        message=(
            "Keep verification, repair-session, reporting, and publish surfaces aligned."
        ),
        patterns=(
            "src/qa_z/repair_session.py",
            "src/qa_z/repair_session_*.py",
            "src/qa_z/verification.py",
            "src/qa_z/verification_*.py",
            "src/qa_z/reporters/*.py",
            "src/qa_z/reporters/verification_publish.py",
            "src/qa_z/reporters/github_summary.py",
            "src/qa_z/operator_action_render.py",
            "src/qa_z/commands/review_github_context.py",
            "tests/test_repair_session*.py",
            "tests/test_verification*.py",
            "tests/test_github_summary*.py",
            "tests/test_repair_prompt*.py",
            "tests/test_review_packet*.py",
            "tests/test_verify_cli_error_contracts.py",
            "tests/test_run_summary*.py",
            "tests/test_sarif*.py",
            "tests/test_review_commands.py",
            "tests/test_review_*.py",
            "tests/verification*_support.py",
            "tests/repair_prompt*_support.py",
            "tests/github_summary*_support.py",
        ),
        validation_commands=(
            "python -m pytest tests/test_verification.py tests/test_verify_cli_error_contracts.py tests/test_repair_prompt.py tests/test_repair_prompt_error_contracts.py tests/test_review_commands.py tests/test_repair_session.py tests/test_github_summary_render.py tests/test_github_summary_session.py -q",
            "python -m qa_z verify --help",
        ),
    ),
    BatchRule(
        id="executor_return_path",
        title="Executor return path",
        message="Keep bridge, executor-result, ingest, and executor fixtures aligned.",
        patterns=(
            "src/qa_z/executor*.py",
            "src/qa_z/**/executor*.py",
            "tests/test_executor*.py",
            "benchmarks/fixtures/*executor*/**",
            "benchmarks/fixtures/**/external-result.json",
        ),
        validation_commands=(
            "python -m pytest tests/test_executor_bridge.py tests/test_executor_result.py tests/test_executor_ingest_outcome.py tests/test_executor_result_dry_run.py -q",
            "python -m qa_z executor-result dry-run --session .qa-z/sessions/latest --json",
        ),
    ),
)

GENERATED_LOCAL_ONLY_PATTERNS = (
    ".qa-z",
    ".qa-z/**",
    "benchmarks/results/work",
    "benchmarks/results/work/**",
    "build",
    "build/**",
    "dist",
    "dist/**",
    "src/qa_z.egg-info",
    "src/qa_z.egg-info/**",
    "__pycache__",
    "__pycache__/**",
    "*/__pycache__",
    "*/__pycache__/**",
    "**/__pycache__",
    "**/__pycache__/**",
    ".pytest_cache",
    ".pytest_cache/**",
    ".mypy_cache",
    ".mypy_cache/**",
    ".mypy_cache_safe",
    ".mypy_cache_safe/**",
    ".ruff_cache",
    ".ruff_cache/**",
    ".ruff_cache_safe",
    ".ruff_cache_safe/**",
    "%TEMP%",
    "%TEMP%/**",
    "tmp_*",
    "tmp_*/**",
    "benchmarks/minlock-*",
    "benchmarks/minlock-*/**",
    "marketing/x/.state",
    "marketing/x/.state/**",
    "marketing/x/logs",
    "marketing/x/logs/**",
    "marketing/x/*.local.json",
)

GENERATED_LOCAL_BY_DEFAULT_PATTERNS = (
    "benchmarks/results",
    "benchmarks/results/**",
    "benchmarks/results-*",
    "benchmarks/results-*/**",
)

GENERATED_PATTERNS = (
    *GENERATED_LOCAL_ONLY_PATTERNS,
    *GENERATED_LOCAL_BY_DEFAULT_PATTERNS,
)

FROZEN_FIXTURE_EXCEPTIONS = (
    "benchmarks/fixtures/**/repo/.qa-z",
    "benchmarks/fixtures/**/repo/.qa-z/**",
)

CROSS_CUTTING_PATTERNS = (
    "README.md",
    "docs/artifact-schema-v1.md",
    "docs/mvp-issues.md",
    "src/qa_z/cli.py",
    "src/qa_z/commands/command_registration.py",
    "src/qa_z/commands/command_registry.py",
    "src/qa_z/commands/execution.py",
    "src/qa_z/commands/runtime.py",
    "tests/test_artifact_schema.py",
    "tests/test_command_registry_architecture.py",
    "tests/test_current_truth.py",
    "tests/test_execution_commands.py",
    "tests/test_runtime_commands.py",
)

REPORT_PATTERNS = ("docs/reports/**",)
RELEASE_OWNED_REPORT_PATTERNS = (
    "docs/reports/worktree-commit-plan.md",
    "docs/reports/v0.10.0-beta-readiness.md",
    "docs/reports/v0.10.0-beta-release-decision.md",
    "docs/reports/v0.10.0-beta-version-policy.md",
)

CROSS_CUTTING_GROUP_RULES = (
    (
        "public_docs_contract",
        "Public docs and schema contract",
        ("README.md", "docs/artifact-schema-v1.md", "docs/mvp-issues.md"),
    ),
    (
        "command_router_spine",
        "CLI command router spine",
        (
            "src/qa_z/cli.py",
            "src/qa_z/commands/command_registration.py",
            "src/qa_z/commands/command_registry.py",
            "src/qa_z/commands/execution.py",
            "src/qa_z/commands/runtime.py",
        ),
    ),
    (
        "current_truth_guards",
        "Current-truth guards",
        ("tests/test_current_truth.py",),
    ),
    (
        "command_surface_tests",
        "Command surface tests",
        (
            "tests/test_artifact_schema.py",
            "tests/test_command_registry_architecture.py",
            "tests/test_execution_commands.py",
            "tests/test_runtime_commands.py",
        ),
    ),
    ("status_reports", "Status reports", REPORT_PATTERNS),
)

SOURCE_PATTERNS = (
    ".github/actions/**",
    ".github/workflows/**",
    "src/**",
    "scripts/**",
    "tests/**",
    "benchmarks/**",
    "qa-z.yaml",
    "pyproject.toml",
    "mypy.ini",
)

PRODUCT_DECISION_GROUP_RULES = (
    (
        "codex_operating_model",
        "Codex-native operating model",
        "operating-model-owned",
        (
            "Stage only after approving the operating-model surface as "
            "alpha-release support, separate from runtime QA-Z changes."
        ),
        (
            ".agents/**",
            ".codex/**",
            ".github/copilot-instructions.md",
            ".github/instructions/**",
            "docs/agent/**",
        ),
    ),
    (
        "claude_compatibility_mirror",
        "Claude compatibility mirror",
        "compatibility mirror",
        (
            "Stage only if the Codex-native operating-model assets are approved "
            "and the mirror must stay synchronized."
        ),
        (".claude/**",),
    ),
    (
        "marketing_x_surface",
        "Marketing/X network automation",
        "marketing/product-owned",
        (
            "Keep out of QA-Z alpha release unless a product owner approves "
            "the credential-gated marketing/network surface."
        ),
        ("marketing/x/**",),
    ),
    (
        "operating_model_validator",
        "Operating-model validator",
        "operating-model-owned",
        (
            "Stage with the operating-model support batch after format and "
            "validator checks pass."
        ),
        ("scripts/validate-agent-operating-model.py",),
    ),
    (
        "marketing_x_tests",
        "Marketing/X automation tests",
        "marketing/product-owned",
        "Stage with marketing/X only if that product surface is approved.",
        ("tests/test_x_automation.py",),
    ),
)

PRODUCT_DECISION_PATTERNS = tuple(
    pattern
    for _, _, _, _, patterns in PRODUCT_DECISION_GROUP_RULES
    for pattern in patterns
)

APPROVED_ALPHA_SUPPORT_GROUP_IDS = frozenset(
    ("codex_operating_model", "operating_model_validator")
)
DEFERRED_ALPHA_SCOPE_GROUP_IDS = frozenset(
    (
        "claude_compatibility_mirror",
        "marketing_x_surface",
        "marketing_x_tests",
    )
)
APPROVED_ALPHA_SUPPORT_SCOPE = "approved_alpha_support_scope"
DEFERRED_OUT_OF_ALPHA_SCOPE = "deferred_out_of_alpha_scope"
UNRESOLVED_PRODUCT_DECISION_SCOPE = "unresolved_product_decision"


def release_scope_for_product_group(group_id: str) -> str:
    if group_id in APPROVED_ALPHA_SUPPORT_GROUP_IDS:
        return APPROVED_ALPHA_SUPPORT_SCOPE
    if group_id in DEFERRED_ALPHA_SCOPE_GROUP_IDS:
        return DEFERRED_OUT_OF_ALPHA_SCOPE
    return UNRESOLVED_PRODUCT_DECISION_SCOPE


def normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/")


def unquote_status_path(path: str) -> str:
    stripped = path.strip()
    if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
        stripped = stripped[1:-1]
    return stripped.replace('\\"', '"')


def matches_any(path: str, patterns: Sequence[str]) -> bool:
    normalized = normalize_path(path)
    return any(fnmatch.fnmatchcase(normalized, pattern) for pattern in patterns)


def parse_status_line(line: str) -> str | None:
    if not line.strip():
        return None
    path = line[3:] if len(line) > 3 else ""
    if " -> " in path:
        path = path.rsplit(" -> ", 1)[1]
    path = unquote_status_path(path)
    path = normalize_path(path)
    if not path:
        return None
    return path


def status_paths(status_lines: Sequence[str]) -> list[str]:
    paths: list[str] = []
    for line in status_lines:
        path = parse_status_line(line)
        if path is not None:
            paths.append(path)
    return paths


def generated_artifact_bucket(path: str) -> str:
    normalized = normalize_path(path).rstrip("/")
    first_segment = normalized.split("/", 1)[0]
    if first_segment.startswith("tmp_"):
        return first_segment if "/" not in normalized else f"{first_segment}/"
    if normalized.startswith("benchmarks/minlock-"):
        parts = normalized.split("/")
        return normalized if len(parts) == 2 else f"{parts[0]}/{parts[1]}/"
    for prefix in (
        ".qa-z",
        "benchmarks/results/work",
        "build",
        "dist",
        "src/qa_z.egg-info",
        ".pytest_cache",
        ".mypy_cache",
        ".mypy_cache_safe",
        ".ruff_cache",
        ".ruff_cache_safe",
        "%TEMP%",
        "benchmarks/results",
        "marketing/x/.state",
        "marketing/x/logs",
    ):
        if normalized == prefix or normalized.startswith(f"{prefix}/"):
            return f"{prefix}/"

    if normalized.startswith("benchmarks/results-"):
        parts = normalized.split("/")
        if len(parts) >= 2:
            return f"benchmarks/{parts[1]}/"

    parts = normalized.split("/")
    for index, part in enumerate(parts):
        if part == "__pycache__":
            return "/".join(parts[: index + 1]).rstrip("/") + "/"

    return path


def is_generated_artifact(path: str) -> bool:
    if matches_any(path, FROZEN_FIXTURE_EXCEPTIONS):
        return False
    return matches_any(path, GENERATED_PATTERNS)


def is_local_only_generated_artifact(path: str) -> bool:
    return matches_any(path, GENERATED_LOCAL_ONLY_PATTERNS)


def is_local_by_default_generated_artifact(path: str) -> bool:
    return matches_any(path, GENERATED_LOCAL_BY_DEFAULT_PATTERNS) and not matches_any(
        path, GENERATED_LOCAL_ONLY_PATTERNS
    )


def is_source_like(path: str) -> bool:
    return matches_any(path, SOURCE_PATTERNS)


def owner_override_for_path(path: str) -> str | None:
    for batch_id, patterns in OWNER_OVERRIDES:
        if matches_any(path, patterns):
            return batch_id
    return None


def build_staging_plan(
    *,
    include_paths: Sequence[str],
    candidate_patch_add_paths: Sequence[str],
    exclude_paths: Sequence[str],
    validation_commands: Sequence[str],
) -> dict[str, object]:
    include_path_list = list(include_paths)
    patch_add_path_list = list(candidate_patch_add_paths)
    return {
        "include_paths": include_path_list,
        "candidate_patch_add_paths": patch_add_path_list,
        "exclude_path_count": len(exclude_paths),
        "git_add_command": ["git", "add", "--", *include_path_list]
        if include_path_list
        else [],
        "git_add_patch_command": ["git", "add", "--patch", "--", *patch_add_path_list]
        if patch_add_path_list
        else [],
        "validation_commands": list(validation_commands),
    }


def shared_patch_add_paths(
    *,
    cross_cutting_paths: Sequence[str],
    report_paths: Sequence[str],
) -> list[str]:
    return unique_strings([*cross_cutting_paths, *report_paths])


def cross_cutting_group_rollup(paths: Sequence[str]) -> list[dict[str, object]]:
    """Group shared patch-add paths into operator-sized review surfaces."""
    grouped: list[dict[str, object]] = []
    used: set[str] = set()
    normalized_paths = unique_strings(paths)
    for group_id, title, patterns in CROSS_CUTTING_GROUP_RULES:
        group_paths = [
            path
            for path in normalized_paths
            if path not in used and matches_any(path, patterns)
        ]
        if not group_paths:
            continue
        used.update(group_paths)
        grouped.append(
            {
                "id": group_id,
                "title": title,
                "path_count": len(group_paths),
                "paths": group_paths,
                "patch_command": ["git", "add", "--patch", "--", *group_paths],
            }
        )
    remaining_paths = [path for path in normalized_paths if path not in used]
    if remaining_paths:
        grouped.append(
            {
                "id": "unclassified_cross_cutting",
                "title": "Unclassified cross-cutting paths",
                "path_count": len(remaining_paths),
                "paths": remaining_paths,
                "patch_command": ["git", "add", "--patch", "--", *remaining_paths],
            }
        )
    return grouped


def product_decision_group_rollup(paths: Sequence[str]) -> list[dict[str, object]]:
    """Group product-decision paths into ownership surfaces."""
    grouped: list[dict[str, object]] = []
    used: set[str] = set()
    normalized_paths = unique_strings(paths)
    for (
        group_id,
        title,
        ownership,
        next_action,
        patterns,
    ) in PRODUCT_DECISION_GROUP_RULES:
        group_paths = [
            path
            for path in normalized_paths
            if path not in used and matches_any(path, patterns)
        ]
        if not group_paths:
            continue
        used.update(group_paths)
        grouped.append(
            {
                "id": group_id,
                "title": title,
                "ownership": ownership,
                "release_scope": release_scope_for_product_group(group_id),
                "path_count": len(group_paths),
                "paths": group_paths,
                "next_action": next_action,
            }
        )
    remaining_paths = [path for path in normalized_paths if path not in used]
    if remaining_paths:
        grouped.append(
            {
                "id": "unclassified_product_decision",
                "title": "Unclassified product-decision paths",
                "ownership": "requires human/product decision",
                "release_scope": UNRESOLVED_PRODUCT_DECISION_SCOPE,
                "path_count": len(remaining_paths),
                "paths": remaining_paths,
                "next_action": (
                    "Assign ownership before staging; these paths matched the "
                    "product-decision bucket without a narrower group."
                ),
            }
        )
    return grouped


def paths_for_release_scope(
    groups: Sequence[dict[str, object]], release_scope: str
) -> list[str]:
    paths: list[str] = []
    for group in groups:
        if group.get("release_scope") != release_scope:
            continue
        group_paths = group.get("paths")
        if isinstance(group_paths, list):
            paths.extend(path for path in group_paths if isinstance(path, str))
    return unique_strings(paths)


def groups_for_release_scope(
    groups: Sequence[dict[str, object]], release_scope: str
) -> list[dict[str, object]]:
    return [group for group in groups if group.get("release_scope") == release_scope]


def render_command_part(part: object) -> str:
    text = str(part)
    shell_sensitive_characters = set('"&;|<>()')
    if (
        not text
        or any(character.isspace() for character in text)
        or any(character in shell_sensitive_characters for character in text)
    ):
        return '"' + text.replace('"', '\\"') + '"'
    return text


def render_command(parts: Sequence[object]) -> str:
    return " ".join(render_command_part(part) for part in parts)


def next_actions(
    *,
    generated_local_only_paths: Sequence[str],
    generated_local_by_default_paths: Sequence[str],
    unassigned_source_paths: Sequence[str],
    product_decision_paths: Sequence[str],
    approved_alpha_support_paths: Sequence[str],
    deferred_alpha_scope_paths: Sequence[str],
    cross_cutting_paths: Sequence[str],
    report_paths: Sequence[str],
    multi_batch_paths: Sequence[dict[str, object]],
) -> list[str]:
    actions: list[str] = []
    if generated_local_only_paths:
        actions.append(
            (
                "Keep local-only generated runtime artifacts out of staging and "
                "cleanup review unless a fixture/doc task explicitly freezes them."
            )
        )
    if generated_local_by_default_paths:
        actions.append(
            (
                "Decide whether local-by-default benchmark evidence stays local or "
                "is intentionally frozen with command/date context before staging "
                "those generated paths."
            )
        )
    if unassigned_source_paths:
        actions.append(
            (
                "Add unassigned source paths to an existing commit batch rule or "
                "split a new explicit batch before release staging."
            )
        )
    if product_decision_paths:
        actions.append(
            (
                "Resolve remaining product decision paths before staging; these "
                "paths still lack an alpha release-scope decision."
            )
        )
    if approved_alpha_support_paths:
        actions.append(
            (
                "Stage approved alpha support paths only with the operating-model "
                "support batch after validator and format proof."
            )
        )
    if deferred_alpha_scope_paths:
        actions.append(
            (
                "Keep deferred out-of-alpha paths out of QA-Z alpha staging unless "
                "a separate product/network or compatibility release decision "
                "approves them."
            )
        )
    if multi_batch_paths:
        actions.append(
            (
                "Resolve multi-batch paths with an explicit owner or patch-add "
                "strategy before staging those files."
            )
        )
    if cross_cutting_paths or report_paths:
        actions.append(
            (
                "Patch-add cross-cutting docs, report files, or current-truth tests "
                "with the feature batch they describe instead of staging them wholesale; "
                "use cross_cutting_groups[].patch_command_text for scoped commands."
            )
        )
    return actions


def analyze_paths(
    paths: Sequence[str],
    *,
    fail_on_generated: bool = False,
    fail_on_cross_cutting: bool = False,
) -> dict[str, object]:
    normalized_paths = unique_strings([normalize_path(path) for path in paths])
    generated_source_paths = [
        path for path in normalized_paths if is_generated_artifact(path)
    ]
    generated_paths = unique_strings(
        [generated_artifact_bucket(path) for path in generated_source_paths]
    )
    generated_local_only_paths = [
        path for path in generated_paths if is_local_only_generated_artifact(path)
    ]
    generated_local_by_default_paths = [
        path for path in generated_paths if is_local_by_default_generated_artifact(path)
    ]
    source_paths = [
        path for path in normalized_paths if not is_generated_artifact(path)
    ]
    release_scope_decision_paths = [
        path for path in source_paths if matches_any(path, PRODUCT_DECISION_PATTERNS)
    ]
    release_scope_decision_groups = product_decision_group_rollup(
        release_scope_decision_paths
    )
    approved_alpha_support_groups = groups_for_release_scope(
        release_scope_decision_groups, APPROVED_ALPHA_SUPPORT_SCOPE
    )
    deferred_alpha_scope_groups = groups_for_release_scope(
        release_scope_decision_groups, DEFERRED_OUT_OF_ALPHA_SCOPE
    )
    product_decision_groups = groups_for_release_scope(
        release_scope_decision_groups, UNRESOLVED_PRODUCT_DECISION_SCOPE
    )
    approved_alpha_support_paths = paths_for_release_scope(
        release_scope_decision_groups, APPROVED_ALPHA_SUPPORT_SCOPE
    )
    deferred_alpha_scope_paths = paths_for_release_scope(
        release_scope_decision_groups, DEFERRED_OUT_OF_ALPHA_SCOPE
    )
    product_decision_paths = paths_for_release_scope(
        release_scope_decision_groups, UNRESOLVED_PRODUCT_DECISION_SCOPE
    )
    cross_cutting_paths = [
        path
        for path in source_paths
        if path not in release_scope_decision_paths
        and matches_any(path, CROSS_CUTTING_PATTERNS)
    ]
    report_paths = [
        path
        for path in source_paths
        if path not in release_scope_decision_paths
        and matches_any(path, REPORT_PATTERNS)
        and not matches_any(path, RELEASE_OWNED_REPORT_PATTERNS)
    ]
    patch_add_paths = shared_patch_add_paths(
        cross_cutting_paths=cross_cutting_paths,
        report_paths=report_paths,
    )
    cross_cutting_groups = cross_cutting_group_rollup(patch_add_paths)

    rule_matches_by_path: dict[str, list[str]] = {}
    for path in source_paths:
        if (
            path in release_scope_decision_paths
            or path in cross_cutting_paths
            or path in report_paths
        ):
            continue
        owner_override = owner_override_for_path(path)
        if owner_override is not None:
            rule_matches_by_path[path] = [owner_override]
        else:
            rule_matches_by_path[path] = [
                rule.id for rule in BATCH_RULES if matches_any(path, rule.patterns)
            ]
    multi_batch_paths: list[dict[str, object]] = [
        {"path": path, "batches": matches}
        for path, matches in rule_matches_by_path.items()
        if len(matches) > 1
    ]
    multi_batch_path_set = {
        item["path"] for item in multi_batch_paths if isinstance(item["path"], str)
    }
    assigned_paths: set[str] = set()
    batches: list[dict[str, object]] = []
    for rule in BATCH_RULES:
        changed_paths = [
            path
            for path in source_paths
            if rule_matches_by_path.get(path) == [rule.id]
            and path not in cross_cutting_paths
            and path not in report_paths
        ]
        assigned_paths.update(changed_paths)
        batches.append(
            {
                "id": rule.id,
                "title": rule.title,
                "message": rule.message,
                "validation_commands": list(rule.validation_commands),
                "changed_count": len(changed_paths),
                "changed_paths": changed_paths,
                "staging_plan": build_staging_plan(
                    include_paths=changed_paths,
                    candidate_patch_add_paths=(),
                    exclude_paths=generated_paths,
                    validation_commands=rule.validation_commands,
                ),
            }
        )

    unassigned_source_paths = [
        path
        for path in source_paths
        if path not in assigned_paths
        and path not in release_scope_decision_paths
        and path not in cross_cutting_paths
        and path not in report_paths
        and path not in multi_batch_path_set
        and is_source_like(path)
    ]
    attention_reasons: list[str] = []
    if unassigned_source_paths:
        attention_reasons.append("unassigned_source_paths")
    if product_decision_paths:
        attention_reasons.append("product_decision_paths_present")
    if multi_batch_paths:
        attention_reasons.append("multi_batch_paths")
    if fail_on_generated and generated_paths:
        attention_reasons.append("generated_artifacts_present")
    if fail_on_cross_cutting and patch_add_paths:
        attention_reasons.append("cross_cutting_paths_present")
    status = "attention_required" if attention_reasons else "ready"
    actions = next_actions(
        generated_local_only_paths=generated_local_only_paths,
        generated_local_by_default_paths=generated_local_by_default_paths,
        unassigned_source_paths=unassigned_source_paths,
        product_decision_paths=product_decision_paths,
        approved_alpha_support_paths=approved_alpha_support_paths,
        deferred_alpha_scope_paths=deferred_alpha_scope_paths,
        cross_cutting_paths=cross_cutting_paths,
        report_paths=report_paths,
        multi_batch_paths=multi_batch_paths,
    )
    changed_batch_count = 0
    for batch in batches:
        changed_count = batch.get("changed_count")
        if isinstance(changed_count, int) and changed_count > 0:
            changed_batch_count += 1
    generated_artifact_dir_count = sum(
        1 for path in generated_paths if path.endswith("/")
    )
    summary = {
        "batch_count": len(batches),
        "changed_batch_count": changed_batch_count,
        "unchanged_batch_count": len(batches) - changed_batch_count,
        "changed_path_count": len(normalized_paths),
        "generated_artifact_count": len(generated_paths),
        "generated_artifact_file_count": len(generated_paths)
        - generated_artifact_dir_count,
        "generated_artifact_dir_count": generated_artifact_dir_count,
        "generated_local_only_count": len(generated_local_only_paths),
        "generated_local_by_default_count": len(generated_local_by_default_paths),
        "cross_cutting_count": len(cross_cutting_paths),
        "cross_cutting_group_count": len(cross_cutting_groups),
        "report_path_count": len(report_paths),
        "shared_patch_add_count": len(patch_add_paths),
        "multi_batch_path_count": len(multi_batch_paths),
        "unassigned_source_path_count": len(unassigned_source_paths),
        "product_decision_path_count": len(product_decision_paths),
        "product_decision_group_count": len(product_decision_groups),
        "release_scope_decision_path_count": len(release_scope_decision_paths),
        "release_scope_decision_group_count": len(release_scope_decision_groups),
        "approved_alpha_support_path_count": len(approved_alpha_support_paths),
        "approved_alpha_support_group_count": len(approved_alpha_support_groups),
        "deferred_alpha_scope_path_count": len(deferred_alpha_scope_paths),
        "deferred_alpha_scope_group_count": len(deferred_alpha_scope_groups),
        "attention_reason_count": len(attention_reasons),
    }
    return {
        "kind": "qa_z.worktree_commit_plan",
        "schema_version": 1,
        "generated_at": utc_timestamp(),
        "status": status,
        "strict_mode": {
            "fail_on_generated": fail_on_generated,
            "fail_on_cross_cutting": fail_on_cross_cutting,
        },
        "attention_reasons": attention_reasons,
        "summary": summary,
        "changed_path_count": len(normalized_paths),
        "batches": batches,
        "generated_artifact_paths": generated_paths,
        "generated_local_only_paths": generated_local_only_paths,
        "generated_local_by_default_paths": generated_local_by_default_paths,
        "cross_cutting_paths": cross_cutting_paths,
        "report_paths": report_paths,
        "shared_patch_add_paths": patch_add_paths,
        "cross_cutting_groups": cross_cutting_groups,
        "multi_batch_paths": multi_batch_paths,
        "unassigned_source_paths": unassigned_source_paths,
        "product_decision_paths": product_decision_paths,
        "product_decision_groups": product_decision_groups,
        "release_scope_decision_paths": release_scope_decision_paths,
        "release_scope_decision_groups": release_scope_decision_groups,
        "approved_alpha_support_paths": approved_alpha_support_paths,
        "approved_alpha_support_groups": approved_alpha_support_groups,
        "deferred_alpha_scope_paths": deferred_alpha_scope_paths,
        "deferred_alpha_scope_groups": deferred_alpha_scope_groups,
        "next_actions": actions,
    }


def analyze_status_lines(
    status_lines: Sequence[str],
    *,
    fail_on_generated: bool = False,
    fail_on_cross_cutting: bool = False,
) -> dict[str, object]:
    return analyze_paths(
        status_paths(status_lines),
        fail_on_generated=fail_on_generated,
        fail_on_cross_cutting=fail_on_cross_cutting,
    )


def filter_payload_for_batch(
    payload: dict[str, object],
    batch_id: str,
) -> dict[str, object]:
    batches = payload.get("batches")
    if not isinstance(batches, list):
        raise ValueError("payload does not contain batches")
    selected = [
        batch
        for batch in batches
        if isinstance(batch, dict) and batch.get("id") == batch_id
    ]
    if not selected:
        known_batches = [
            str(batch.get("id"))
            for batch in batches
            if isinstance(batch, dict) and batch.get("id")
        ]
        raise ValueError(
            f"unknown batch {batch_id}; known batches: {', '.join(known_batches)}"
        )
    filtered = dict(payload)
    global_status = payload.get("status")
    global_attention_reasons = payload.get("attention_reasons")
    selected_batch = dict(selected[0])
    cross_cutting_paths = payload.get("cross_cutting_paths")
    report_paths = payload.get("report_paths")
    patch_add_candidates = [
        path
        for path in shared_patch_add_paths(
            cross_cutting_paths=(
                [path for path in cross_cutting_paths if isinstance(path, str)]
                if isinstance(cross_cutting_paths, list)
                else []
            ),
            report_paths=(
                [path for path in report_paths if isinstance(path, str)]
                if isinstance(report_paths, list)
                else []
            ),
        )
    ]
    staging_plan = selected_batch.get("staging_plan")
    if isinstance(staging_plan, dict):
        updated_staging_plan = dict(staging_plan)
        updated_staging_plan["candidate_patch_add_paths"] = patch_add_candidates
        updated_staging_plan["git_add_patch_command"] = (
            [
                "git",
                "add",
                "--patch",
                "--",
                *patch_add_candidates,
            ]
            if patch_add_candidates
            else []
        )
        selected_batch["staging_plan"] = updated_staging_plan
    filtered["selected_batch"] = batch_id
    filtered["batches"] = [selected_batch]
    validation_commands = selected_batch.get("validation_commands")
    selected_is_empty = selected_batch.get("changed_count") == 0
    selected_status = "attention_required" if selected_is_empty else "ready"
    selected_staging_plan = selected_batch.get("staging_plan")
    include_path_count = 0
    patch_add_candidate_count = 0
    generated_exclude_count = 0
    if isinstance(selected_staging_plan, dict):
        include_paths = selected_staging_plan.get("include_paths")
        if isinstance(include_paths, list):
            include_path_count = len(include_paths)
        patch_add_paths = selected_staging_plan.get("candidate_patch_add_paths")
        if isinstance(patch_add_paths, list):
            patch_add_candidate_count = len(patch_add_paths)
        exclude_count = selected_staging_plan.get("exclude_path_count")
        if isinstance(exclude_count, int):
            generated_exclude_count = exclude_count
    global_reasons = (
        [reason for reason in global_attention_reasons if isinstance(reason, str)]
        if isinstance(global_attention_reasons, list)
        else []
    )
    selected_attention_reasons = list(global_reasons)
    if selected_is_empty:
        selected_attention_reasons.append("selected_batch_empty")
    filtered_status = (
        "attention_required" if selected_attention_reasons else selected_status
    )
    filtered["global_status"] = global_status
    filtered["global_attention_reasons"] = global_reasons
    filtered["global_attention_reason_count"] = len(global_reasons)
    filtered["status"] = filtered_status
    filtered["attention_reasons"] = selected_attention_reasons
    if selected_is_empty:
        next_action_items = filtered.get("next_actions")
        actions = (
            [action for action in next_action_items if isinstance(action, str)]
            if isinstance(next_action_items, list)
            else []
        )
        actions.append(
            "Select a batch with changed paths or rerun without --batch to inspect changed_batches."
        )
        filtered["next_actions"] = unique_strings(actions)
    filtered["selected_batch_summary"] = {
        "id": batch_id,
        "changed_count": selected_batch.get("changed_count", 0),
        "include_path_count": include_path_count,
        "patch_add_candidate_count": patch_add_candidate_count,
        "generated_exclude_count": generated_exclude_count,
        "status": selected_status,
        "validation_command_count": len(validation_commands)
        if isinstance(validation_commands, list)
        else 0,
        "attention_reason_count": len(selected_attention_reasons),
    }
    return filtered


def compact_payload(payload: dict[str, object]) -> dict[str, object]:
    """Return a compact JSON-safe summary for loop and handoff artifacts."""
    attention_reasons = payload.get("attention_reasons")
    next_action_items = payload.get("next_actions")
    compact: dict[str, object] = {
        "kind": payload.get("kind"),
        "schema_version": payload.get("schema_version"),
        "generated_at": payload.get("generated_at"),
        "status": payload.get("status"),
        "strict_mode": payload.get("strict_mode"),
        "summary": payload.get("summary"),
        "attention_reasons": attention_reasons
        if isinstance(attention_reasons, list)
        else [],
        "next_actions": next_action_items
        if isinstance(next_action_items, list)
        else [],
    }
    for key in (
        "repository",
        "selected_batch",
        "selected_batch_summary",
        "global_status",
        "global_attention_reasons",
        "global_attention_reason_count",
    ):
        if key in payload:
            compact[key] = payload[key]
    for key in (
        "generated_artifact_paths",
        "generated_local_only_paths",
        "generated_local_by_default_paths",
        "cross_cutting_paths",
        "report_paths",
        "shared_patch_add_paths",
        "multi_batch_paths",
        "unassigned_source_paths",
        "product_decision_paths",
        "release_scope_decision_paths",
        "approved_alpha_support_paths",
        "deferred_alpha_scope_paths",
    ):
        value = payload.get(key)
        if isinstance(value, list):
            compact[key] = value[:20]
            if len(value) > 20:
                compact[f"{key}_truncated_count"] = len(value) - 20
    cross_cutting_groups = payload.get("cross_cutting_groups")
    if isinstance(cross_cutting_groups, list):
        compact["cross_cutting_groups"] = compact_cross_cutting_groups(
            cross_cutting_groups
        )
        if len(cross_cutting_groups) > 20:
            compact["cross_cutting_groups_truncated_count"] = (
                len(cross_cutting_groups) - 20
            )
    product_decision_groups = payload.get("product_decision_groups")
    if isinstance(product_decision_groups, list):
        compact["product_decision_groups"] = compact_product_decision_groups(
            product_decision_groups
        )
        if len(product_decision_groups) > 20:
            compact["product_decision_groups_truncated_count"] = (
                len(product_decision_groups) - 20
            )
    release_scope_decision_groups = payload.get("release_scope_decision_groups")
    if isinstance(release_scope_decision_groups, list):
        compact["release_scope_decision_groups"] = compact_product_decision_groups(
            release_scope_decision_groups
        )
        if len(release_scope_decision_groups) > 20:
            compact["release_scope_decision_groups_truncated_count"] = (
                len(release_scope_decision_groups) - 20
            )
    approved_alpha_support_groups = payload.get("approved_alpha_support_groups")
    if isinstance(approved_alpha_support_groups, list):
        compact["approved_alpha_support_groups"] = compact_product_decision_groups(
            approved_alpha_support_groups
        )
    deferred_alpha_scope_groups = payload.get("deferred_alpha_scope_groups")
    if isinstance(deferred_alpha_scope_groups, list):
        compact["deferred_alpha_scope_groups"] = compact_product_decision_groups(
            deferred_alpha_scope_groups
        )
    changed_batches: list[dict[str, object]] = []
    batches = payload.get("batches")
    if isinstance(batches, list):
        for batch in batches:
            if not isinstance(batch, dict):
                continue
            changed_count = batch.get("changed_count")
            if not isinstance(changed_count, int) or changed_count <= 0:
                continue
            validation_commands = batch.get("validation_commands")
            staging_plan = batch.get("staging_plan")
            compact_batch: dict[str, object] = {
                "id": batch.get("id"),
                "title": batch.get("title"),
                "message": batch.get("message"),
                "changed_count": changed_count,
                "validation_commands": validation_commands
                if isinstance(validation_commands, list)
                else [],
            }
            if isinstance(staging_plan, dict):
                compact_batch["staging_plan"] = compact_staging_plan(staging_plan)
            changed_batches.append(compact_batch)
    compact["changed_batches"] = changed_batches
    return compact


def compact_staging_plan(staging_plan: dict[str, object]) -> dict[str, object]:
    """Return summary-only staging guidance without incomplete commands."""
    compact: dict[str, object] = {}
    include_paths = staging_plan.get("include_paths")
    if isinstance(include_paths, list):
        compact["include_path_count"] = len(include_paths)
        compact["include_paths"] = include_paths[:20]
        if len(include_paths) > 20:
            compact["include_paths_truncated_count"] = len(include_paths) - 20
        else:
            git_add_command = staging_plan.get("git_add_command")
            if isinstance(git_add_command, list):
                compact["git_add_command"] = git_add_command
                compact["git_add_command_text"] = render_command(git_add_command)
    candidate_patch_add_paths = staging_plan.get("candidate_patch_add_paths")
    if isinstance(candidate_patch_add_paths, list) and candidate_patch_add_paths:
        compact["candidate_patch_add_count"] = len(candidate_patch_add_paths)
        compact["candidate_patch_add_paths"] = candidate_patch_add_paths[:20]
        if len(candidate_patch_add_paths) > 20:
            compact["candidate_patch_add_paths_truncated_count"] = (
                len(candidate_patch_add_paths) - 20
            )
        else:
            git_add_patch_command = staging_plan.get("git_add_patch_command")
            if isinstance(git_add_patch_command, list) and git_add_patch_command:
                compact["git_add_patch_command"] = git_add_patch_command
                compact["git_add_patch_command_text"] = render_command(
                    git_add_patch_command
                )
    return compact


def compact_cross_cutting_groups(groups: list[object]) -> list[dict[str, object]]:
    """Return compact cross-cutting group previews for summary-only evidence."""
    compact_groups: list[dict[str, object]] = []
    for group in groups[:20]:
        if not isinstance(group, dict):
            continue
        compact_group: dict[str, object] = {
            "id": group.get("id"),
            "title": group.get("title"),
            "path_count": group.get("path_count"),
        }
        paths = group.get("paths")
        if isinstance(paths, list):
            compact_group["paths"] = paths[:20]
            if len(paths) > 20:
                compact_group["paths_truncated_count"] = len(paths) - 20
        patch_command = group.get("patch_command")
        if isinstance(patch_command, list):
            compact_group["patch_command"] = patch_command
            compact_group["patch_command_text"] = render_command(patch_command)
        compact_groups.append(compact_group)
    return compact_groups


def compact_product_decision_groups(groups: list[object]) -> list[dict[str, object]]:
    """Return compact ownership-group previews for summary-only evidence."""
    compact_groups: list[dict[str, object]] = []
    for group in groups[:20]:
        if not isinstance(group, dict):
            continue
        compact_group: dict[str, object] = {
            "id": group.get("id"),
            "title": group.get("title"),
            "ownership": group.get("ownership"),
            "release_scope": group.get("release_scope"),
            "path_count": group.get("path_count"),
            "next_action": group.get("next_action"),
        }
        paths = group.get("paths")
        if isinstance(paths, list):
            compact_group["paths"] = paths[:20]
            if len(paths) > 20:
                compact_group["paths_truncated_count"] = len(paths) - 20
        compact_groups.append(compact_group)
    return compact_groups


def render_human(payload: dict[str, object]) -> str:
    summary = payload.get("summary")
    changed_path_count = payload.get("changed_path_count")
    if changed_path_count is None and isinstance(summary, dict):
        changed_path_count = summary.get("changed_path_count")
    lines = [
        f"Generated at: {payload['generated_at']}",
        f"Status: {payload['status']}",
        f"Changed paths: {changed_path_count or 0}",
    ]
    if isinstance(summary, dict):
        changed_batches = summary.get("changed_batch_count")
        unchanged_batches = summary.get("unchanged_batch_count")
        if changed_batches is not None and unchanged_batches is not None:
            lines.append(
                f"Batches: changed={changed_batches}, unchanged={unchanged_batches}"
            )
    selected_batch_summary = payload.get("selected_batch_summary")
    if isinstance(selected_batch_summary, dict):
        selected_id = selected_batch_summary.get("id")
        selected_status = selected_batch_summary.get("status")
        selected_count = selected_batch_summary.get("changed_count")
        if selected_id and selected_status is not None and selected_count is not None:
            lines.append(
                f"Selected batch: {selected_id} ({selected_status}, "
                f"{selected_count} paths)"
            )
        include_count = selected_batch_summary.get("include_path_count")
        patch_add_count = selected_batch_summary.get("patch_add_candidate_count")
        generated_exclude_count = selected_batch_summary.get("generated_exclude_count")
        if (
            include_count is not None
            and patch_add_count is not None
            and generated_exclude_count is not None
        ):
            lines.append(
                "Selected staging: "
                f"include={include_count}, patch_add={patch_add_count}, "
                f"generated_excludes={generated_exclude_count}"
            )
    global_status = payload.get("global_status")
    if isinstance(global_status, str):
        lines.append(f"Global status: {global_status}")
    global_attention_reasons = payload.get("global_attention_reasons")
    if isinstance(global_attention_reasons, list):
        reasons = unique_strings(global_attention_reasons)
        if reasons:
            lines.append(f"Global attention reasons: {', '.join(reasons)}")
    strict_mode = payload.get("strict_mode")
    if isinstance(strict_mode, dict):
        strict_flags = [
            key
            for key in ("fail_on_generated", "fail_on_cross_cutting")
            if strict_mode.get(key) is True
        ]
        if strict_flags:
            lines.append(f"Strict mode: {', '.join(strict_flags)}")
    attention_reasons = payload.get("attention_reasons")
    if isinstance(attention_reasons, list):
        reasons = unique_strings(attention_reasons)
        if reasons:
            lines.append(f"Attention reasons: {', '.join(reasons)}")
    batches = payload.get("batches")
    if not isinstance(batches, list):
        changed_batches = payload.get("changed_batches")
        batches = changed_batches if isinstance(changed_batches, list) else []
    for batch in batches:
        if not isinstance(batch, dict):
            continue
        changed_count = batch["changed_count"]
        if changed_count:
            lines.append(f"- {batch['id']}: {changed_count} paths")
            staging_plan = batch.get("staging_plan")
            if isinstance(staging_plan, dict):
                include_paths = staging_plan.get("include_paths")
                if isinstance(include_paths, list) and include_paths:
                    rendered_paths = ", ".join(str(path) for path in include_paths[:3])
                    suffix = " ..." if len(include_paths) > 3 else ""
                    lines.append(f"  include: {rendered_paths}{suffix}")
                patch_add_paths = staging_plan.get("candidate_patch_add_paths")
                if isinstance(patch_add_paths, list) and patch_add_paths:
                    rendered_paths = ", ".join(
                        str(path) for path in patch_add_paths[:3]
                    )
                    suffix = " ..." if len(patch_add_paths) > 3 else ""
                    lines.append(f"  patch-add candidates: {rendered_paths}{suffix}")
                exclude_count = staging_plan.get("exclude_path_count")
                if isinstance(exclude_count, int) and exclude_count:
                    lines.append(f"  generated excludes: {exclude_count}")
                git_add_command = staging_plan.get("git_add_command")
                if isinstance(git_add_command, list) and git_add_command:
                    lines.append(f"  stage command: {render_command(git_add_command)}")
                git_add_patch_command = staging_plan.get("git_add_patch_command")
                if isinstance(git_add_patch_command, list) and git_add_patch_command:
                    lines.append(
                        f"  patch command: {render_command(git_add_patch_command)}"
                    )
            validation_commands = batch.get("validation_commands")
            if isinstance(validation_commands, list):
                lines.extend(
                    f"  validation: {command}"
                    for command in validation_commands
                    if isinstance(command, str)
                )
    generated_paths = payload["generated_artifact_paths"]
    if isinstance(generated_paths, list) and generated_paths:
        generated_line = f"Generated artifacts: {len(generated_paths)}"
        if isinstance(summary, dict):
            generated_file_count = summary.get("generated_artifact_file_count")
            generated_dir_count = summary.get("generated_artifact_dir_count")
            if generated_file_count is not None and generated_dir_count is not None:
                generated_line = (
                    f"{generated_line} "
                    f"(files={generated_file_count}, dirs={generated_dir_count})"
                )
        lines.append(generated_line)
    generated_local_only_paths = payload.get("generated_local_only_paths")
    generated_local_by_default_paths = payload.get("generated_local_by_default_paths")
    generated_local_only_count = None
    generated_local_by_default_count = None
    if isinstance(summary, dict):
        local_only_count = summary.get("generated_local_only_count")
        if isinstance(local_only_count, int):
            generated_local_only_count = local_only_count
        local_by_default_count = summary.get("generated_local_by_default_count")
        if isinstance(local_by_default_count, int):
            generated_local_by_default_count = local_by_default_count
    if generated_local_only_count is None and isinstance(
        generated_local_only_paths, list
    ):
        generated_local_only_count = len(generated_local_only_paths)
    if generated_local_by_default_count is None and isinstance(
        generated_local_by_default_paths, list
    ):
        generated_local_by_default_count = len(generated_local_by_default_paths)
    if (
        generated_local_only_count is not None
        or generated_local_by_default_count is not None
    ):
        lines.append(
            "Generated policy: "
            f"local_only={generated_local_only_count or 0}, "
            f"local_by_default={generated_local_by_default_count or 0}"
        )
    if isinstance(generated_local_only_paths, list) and generated_local_only_paths:
        rendered_paths = ", ".join(str(path) for path in generated_local_only_paths[:3])
        suffix = " ..." if len(generated_local_only_paths) > 3 else ""
        lines.append(f"Local-only generated preview: {rendered_paths}{suffix}")
    if (
        isinstance(generated_local_by_default_paths, list)
        and generated_local_by_default_paths
    ):
        rendered_paths = ", ".join(
            str(path) for path in generated_local_by_default_paths[:3]
        )
        suffix = " ..." if len(generated_local_by_default_paths) > 3 else ""
        lines.append(f"Local-by-default generated preview: {rendered_paths}{suffix}")
    report_paths = payload.get("report_paths")
    if isinstance(report_paths, list) and report_paths:
        lines.append(f"Report paths: {len(report_paths)}")
        rendered_paths = ", ".join(str(path) for path in report_paths[:3])
        suffix = " ..." if len(report_paths) > 3 else ""
        lines.append(f"Report preview: {rendered_paths}{suffix}")
    patch_add_paths = payload.get("shared_patch_add_paths")
    if isinstance(patch_add_paths, list) and patch_add_paths:
        lines.append(f"Shared patch-add paths: {len(patch_add_paths)}")
        rendered_paths = ", ".join(str(path) for path in patch_add_paths[:3])
        suffix = " ..." if len(patch_add_paths) > 3 else ""
        lines.append(f"Shared patch-add preview: {rendered_paths}{suffix}")
    cross_cutting_groups = payload.get("cross_cutting_groups")
    if isinstance(cross_cutting_groups, list) and cross_cutting_groups:
        lines.append(f"Cross-cutting groups: {len(cross_cutting_groups)}")
        for group in cross_cutting_groups:
            if not isinstance(group, dict):
                continue
            group_id = group.get("id", "unknown")
            path_count = group.get("path_count", 0)
            lines.append(f"- {group_id}: {path_count} paths")
            paths = group.get("paths")
            if isinstance(paths, list) and paths:
                rendered_paths = ", ".join(str(path) for path in paths[:3])
                suffix = " ..." if len(paths) > 3 else ""
                lines.append(f"  paths: {rendered_paths}{suffix}")
            patch_command = group.get("patch_command")
            if isinstance(patch_command, list) and patch_command:
                lines.append(f"  patch command: {render_command(patch_command)}")
    unassigned_paths = payload["unassigned_source_paths"]
    if isinstance(unassigned_paths, list) and unassigned_paths:
        lines.append(f"Unassigned source paths: {len(unassigned_paths)}")
    approved_alpha_support_paths = payload.get("approved_alpha_support_paths")
    if isinstance(approved_alpha_support_paths, list) and approved_alpha_support_paths:
        lines.append(
            f"Approved alpha support paths: {len(approved_alpha_support_paths)}"
        )
        rendered_paths = ", ".join(
            str(path) for path in approved_alpha_support_paths[:3]
        )
        suffix = " ..." if len(approved_alpha_support_paths) > 3 else ""
        lines.append(f"Approved alpha support preview: {rendered_paths}{suffix}")
    deferred_alpha_scope_paths = payload.get("deferred_alpha_scope_paths")
    if isinstance(deferred_alpha_scope_paths, list) and deferred_alpha_scope_paths:
        lines.append(f"Deferred out-of-alpha paths: {len(deferred_alpha_scope_paths)}")
        rendered_paths = ", ".join(str(path) for path in deferred_alpha_scope_paths[:3])
        suffix = " ..." if len(deferred_alpha_scope_paths) > 3 else ""
        lines.append(f"Deferred out-of-alpha preview: {rendered_paths}{suffix}")
    release_scope_decision_groups = payload.get("release_scope_decision_groups")
    if (
        isinstance(release_scope_decision_groups, list)
        and release_scope_decision_groups
    ):
        lines.append(
            f"Release-scope decision groups: {len(release_scope_decision_groups)}"
        )
        for group in release_scope_decision_groups:
            if not isinstance(group, dict):
                continue
            group_id = group.get("id", "unknown")
            release_scope = group.get("release_scope", "unknown")
            path_count = group.get("path_count", 0)
            noun = "path" if path_count == 1 else "paths"
            lines.append(f"- {group_id}: {release_scope} ({path_count} {noun})")
            paths = group.get("paths")
            if isinstance(paths, list) and paths:
                rendered_paths = ", ".join(str(path) for path in paths[:3])
                suffix = " ..." if len(paths) > 3 else ""
                lines.append(f"  paths: {rendered_paths}{suffix}")
            next_action = group.get("next_action")
            if isinstance(next_action, str) and next_action:
                lines.append(f"  next action: {next_action}")
    product_decision_paths = payload.get("product_decision_paths")
    if isinstance(product_decision_paths, list) and product_decision_paths:
        lines.append(f"Product decision paths: {len(product_decision_paths)}")
        rendered_paths = ", ".join(str(path) for path in product_decision_paths[:3])
        suffix = " ..." if len(product_decision_paths) > 3 else ""
        lines.append(f"Product decision preview: {rendered_paths}{suffix}")
    product_decision_groups = payload.get("product_decision_groups")
    if isinstance(product_decision_groups, list) and product_decision_groups:
        lines.append(f"Product decision groups: {len(product_decision_groups)}")
        for group in product_decision_groups:
            if not isinstance(group, dict):
                continue
            group_id = group.get("id", "unknown")
            ownership = group.get("ownership", "unknown")
            path_count = group.get("path_count", 0)
            noun = "path" if path_count == 1 else "paths"
            lines.append(f"- {group_id}: {ownership} ({path_count} {noun})")
            paths = group.get("paths")
            if isinstance(paths, list) and paths:
                rendered_paths = ", ".join(str(path) for path in paths[:3])
                suffix = " ..." if len(paths) > 3 else ""
                lines.append(f"  paths: {rendered_paths}{suffix}")
            next_action = group.get("next_action")
            if isinstance(next_action, str) and next_action:
                lines.append(f"  next action: {next_action}")
    multi_batch_paths = payload.get("multi_batch_paths")
    if isinstance(multi_batch_paths, list) and multi_batch_paths:
        lines.append(f"Multi-batch paths: {len(multi_batch_paths)}")
    next_action_items = payload.get("next_actions")
    if isinstance(next_action_items, list) and next_action_items:
        lines.append("Next actions:")
        lines.extend(f"- {item}" for item in unique_strings(next_action_items))
    return "\n".join(lines)


def unique_strings(values: Sequence[object]) -> list[str]:
    strings: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, str) and value not in seen:
            strings.append(value)
            seen.add(value)
    return strings
