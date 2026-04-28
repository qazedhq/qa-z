from __future__ import annotations

from pathlib import Path

from qa_z.benchmark import run_benchmark


def test_run_benchmark_executes_completed_verify_blocked_executor_dry_run_fixture(
    tmp_path: Path,
) -> None:
    summary = run_benchmark(
        fixtures_dir=Path("benchmarks") / "fixtures",
        results_dir=tmp_path / "results",
        fixture_names=["executor_dry_run_completed_verify_blocked"],
    )

    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_dry_run"]["history_signals"] == [
        "completed_verify_blocked",
        "validation_conflict",
    ]
    assert fixture_result["actual"]["executor_dry_run"]["operator_decision"] == (
        "resolve_verification_blockers"
    )
    assert fixture_result["actual"]["executor_dry_run"]["operator_summary"] == (
        "A completed executor attempt is still blocked by verification evidence; "
        "validation conflicts still need review before another retry."
    )
    assert fixture_result["actual"]["executor_dry_run"]["recommended_action_ids"] == [
        "resolve_verification_blockers",
        "review_validation_conflict",
    ]
    assert fixture_result["categories"]["policy"] is True
