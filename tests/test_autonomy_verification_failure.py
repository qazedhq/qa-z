"""Tests for verification-failure autonomy action mapping."""

from __future__ import annotations

from pathlib import Path

from qa_z.autonomy import action_for_task


def test_action_mapping_handles_verification_failure_category(
    tmp_path: Path,
) -> None:
    action = action_for_task(
        root=tmp_path,
        config=None,
        loop_id="loop-one",
        task={
            "id": "verify_failure-candidate",
            "category": "verification_failure",
            "recommendation": "",
            "evidence": [
                {
                    "source": "verification",
                    "path": ".qa-z/runs/candidate/verify/summary.json",
                    "summary": (
                        "verdict=verification_failed; regressions=0; "
                        "new_issues=0; not_comparable=1"
                    ),
                }
            ],
        },
    )

    assert action["type"] == "verification_stabilization_plan"
    assert action["title"] == "Create a stabilization plan from verification evidence."
