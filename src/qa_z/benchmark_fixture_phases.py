"""Non-executor benchmark fixture phase helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z import benchmark as benchmark_module


def run_fast_phase(
    *,
    expectation: Any,
    workspace: Path,
    config: dict[str, Any],
    run_dir: Path,
    results_dir: Path,
    actual: dict[str, Any],
    artifacts: dict[str, str],
) -> None:
    if not expectation.should_run_fast():
        return
    fast_summary = benchmark_module.execute_fast_fixture(workspace, config, run_dir)
    actual["fast"] = benchmark_module.summarize_fast_actual(fast_summary)
    artifacts["fast_summary"] = benchmark_module.format_path(
        run_dir / "fast" / "summary.json", results_dir
    )


def run_deep_phase(
    *,
    expectation: Any,
    workspace: Path,
    config: dict[str, Any],
    run_dir: Path,
    results_dir: Path,
    actual: dict[str, Any],
    artifacts: dict[str, str],
) -> None:
    if not expectation.should_run_deep():
        return
    deep_summary = benchmark_module.execute_deep_fixture(
        workspace=workspace,
        config=config,
        run_dir=run_dir,
        attach_to_fast=expectation.should_run_fast(),
    )
    actual["deep"] = benchmark_module.summarize_deep_actual(deep_summary)
    artifacts["deep_summary"] = benchmark_module.format_path(
        run_dir / "deep" / "summary.json", results_dir
    )


def run_handoff_phase(
    *,
    expectation: Any,
    workspace: Path,
    config: dict[str, Any],
    run_dir: Path,
    results_dir: Path,
    actual: dict[str, Any],
    artifacts: dict[str, str],
) -> None:
    if not expectation.should_run_handoff():
        return
    handoff = benchmark_module.execute_handoff_fixture(workspace, config, run_dir)
    actual["handoff"] = benchmark_module.summarize_handoff_actual(handoff)
    artifacts["handoff"] = benchmark_module.format_path(
        run_dir / "repair" / "handoff.json", results_dir
    )


def run_verify_phase(
    *,
    expectation: Any,
    workspace: Path,
    config: dict[str, Any],
    results_dir: Path,
    actual: dict[str, Any],
    artifacts: dict[str, str],
) -> None:
    verify_config = expectation.verify_config()
    if verify_config is None:
        return
    comparison = benchmark_module.execute_verify_fixture(
        workspace=workspace,
        config=config,
        baseline_run=verify_config["baseline_run"],
        candidate_run=verify_config["candidate_run"],
    )
    actual["verify"] = benchmark_module.summarize_verify_actual(comparison.to_dict())
    artifacts["verify_summary"] = benchmark_module.format_path(
        workspace / str(verify_config["candidate_run"]) / "verify" / "summary.json",
        results_dir,
    )
