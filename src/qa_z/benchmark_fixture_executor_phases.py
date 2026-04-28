"""Executor-related benchmark fixture phase helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z import benchmark as benchmark_module


def run_executor_bridge_phase(
    *,
    expectation: Any,
    workspace: Path,
    config: dict[str, Any],
    results_dir: Path,
    actual: dict[str, Any],
    artifacts: dict[str, str],
) -> None:
    executor_bridge_config = expectation.executor_bridge_config()
    if executor_bridge_config is None:
        return
    bridge_manifest, bridge_guide = benchmark_module.execute_executor_bridge_fixture(
        workspace=workspace,
        config=config,
        baseline_run=str(executor_bridge_config["baseline_run"]),
        session_id=str(executor_bridge_config["session_id"]),
        bridge_id=str(executor_bridge_config["bridge_id"]),
        loop_id=str(executor_bridge_config["loop_id"]),
        context_paths=list(executor_bridge_config["context_paths"]),
    )
    actual["executor_bridge"] = benchmark_module.summarize_executor_bridge_actual(
        workspace=workspace,
        manifest=bridge_manifest,
        guide=bridge_guide,
    )
    artifacts["executor_bridge"] = benchmark_module.format_path(
        workspace
        / ".qa-z"
        / "executor"
        / str(executor_bridge_config["bridge_id"])
        / "bridge.json",
        results_dir,
    )


def run_executor_result_phase(
    *,
    expectation: Any,
    workspace: Path,
    config: dict[str, Any],
    results_dir: Path,
    actual: dict[str, Any],
    artifacts: dict[str, str],
) -> None:
    executor_result_config = expectation.executor_result_config()
    if executor_result_config is None:
        return
    outcome = benchmark_module.execute_executor_result_fixture(
        workspace=workspace,
        config=config,
        baseline_run=executor_result_config["baseline_run"],
        session_id=executor_result_config["session_id"],
        bridge_id=executor_result_config["bridge_id"],
        result_path=executor_result_config["result_path"],
        loop_id=executor_result_config.get("loop_id") or None,
    )
    actual["executor_result"] = benchmark_module.summarize_executor_result_actual(
        outcome.summary
    )
    if not (
        outcome.summary.get("verification_triggered")
        and outcome.summary.get("verify_summary_path")
    ):
        return
    verify_summary_path = workspace / str(outcome.summary["verify_summary_path"])
    verify_summary = benchmark_module.read_json_object(verify_summary_path)
    actual["verify"] = benchmark_module.summarize_verify_summary_actual(verify_summary)
    artifacts["verify_summary"] = benchmark_module.format_path(
        verify_summary_path, results_dir
    )


def run_executor_dry_run_phase(
    *,
    expectation: Any,
    workspace: Path,
    actual: dict[str, Any],
    artifacts: dict[str, str],
) -> None:
    del artifacts
    executor_dry_run_config = expectation.executor_result_dry_run_config()
    if executor_dry_run_config is None:
        return
    dry_run_outcome = benchmark_module.execute_executor_dry_run_fixture(
        workspace=workspace,
        session_id=executor_dry_run_config["session_id"],
    )
    actual["executor_dry_run"] = benchmark_module.summarize_executor_dry_run_actual(
        dry_run_outcome.summary
    )
