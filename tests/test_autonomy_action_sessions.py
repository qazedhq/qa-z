from __future__ import annotations

import json
from pathlib import Path

import qa_z.autonomy_action_sessions as autonomy_action_sessions_module

from qa_z.autonomy_actions import (
    baseline_run_from_verify_evidence,
    existing_session_id,
    executor_dry_run_command,
    repair_session_action,
)


def test_autonomy_action_sessions_module_exports_match_autonomy_surface() -> None:
    assert (
        autonomy_action_sessions_module.baseline_run_from_verify_evidence
        is baseline_run_from_verify_evidence
    )
    assert autonomy_action_sessions_module.existing_session_id is existing_session_id
    assert (
        autonomy_action_sessions_module.executor_dry_run_command
        is executor_dry_run_command
    )
    assert (
        autonomy_action_sessions_module.repair_session_action is repair_session_action
    )


def test_existing_session_id_reads_session_from_evidence_path() -> None:
    assert (
        autonomy_action_sessions_module.existing_session_id(
            {
                "evidence": [
                    {
                        "path": ".qa-z/sessions/session-123/executor_results/dry_run_summary.json"
                    }
                ]
            }
        )
        == "session-123"
    )


def test_baseline_run_from_verify_evidence_reads_compare_json(
    tmp_path: Path,
) -> None:
    compare = tmp_path / ".qa-z" / "runs" / "candidate" / "verify" / "compare.json"
    compare.parent.mkdir(parents=True, exist_ok=True)
    compare.write_text(
        json.dumps(
            {
                "kind": "qa_z.verify_compare",
                "baseline": {"run_dir": ".qa-z/runs/baseline"},
            }
        ),
        encoding="utf-8",
    )

    assert (
        autonomy_action_sessions_module.baseline_run_from_verify_evidence(
            tmp_path,
            {
                "evidence": [
                    {"path": ".qa-z/runs/candidate/verify/compare.json"},
                ]
            },
        )
        == ".qa-z/runs/baseline"
    )
