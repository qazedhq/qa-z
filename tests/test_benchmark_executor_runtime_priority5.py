"""Priority 5 benchmark regressions for executor dry-run operator actions."""

from __future__ import annotations

from pathlib import Path

from qa_z.benchmark import run_benchmark


def test_run_benchmark_executes_validation_rejected_mixed_history_fixture(
    tmp_path: Path,
) -> None:
    summary = run_benchmark(
        fixtures_dir=Path("benchmarks") / "fixtures",
        results_dir=tmp_path / "results",
        fixture_names=[
            "executor_dry_run_validation_conflict_repeated_rejected_operator_actions"
        ],
    )

    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_dry_run"]["operator_decision"] == (
        "review_validation_conflict"
    )
    assert fixture_result["actual"]["executor_dry_run"]["operator_summary"] == (
        "Executor history has validation conflicts and retry pressure; review both "
        "recommended actions before another retry."
    )
    assert fixture_result["actual"]["executor_dry_run"]["recommended_action_ids"] == [
        "review_validation_conflict",
        "inspect_rejected_results",
        "inspect_partial_attempts",
    ]
    assert fixture_result["categories"]["policy"] is True
