"""Behavior tests for executor-bridge render helpers."""

from __future__ import annotations

from qa_z.executor_bridge_render import (
    render_bridge_stdout,
    render_executor_bridge_guide,
)


def _manifest() -> dict[str, object]:
    return {
        "bridge_id": "bridge-one",
        "status": "ready_for_external_executor",
        "source_loop_id": "loop-001",
        "source_session_id": "session-one",
        "baseline_run_dir": ".qa-z/runs/baseline",
        "bridge_dir": ".qa-z/executor/bridge-one",
        "handoff_path": ".qa-z/executor/bridge-one/inputs/handoff.json",
        "selected_task_ids": ["task-1"],
        "validation_commands": [["python", "-m", "qa_z", "repair-session", "verify"]],
        "non_goals": ["do not broaden scope"],
        "inputs": {
            "session": ".qa-z/executor/bridge-one/inputs/session.json",
            "handoff": ".qa-z/executor/bridge-one/inputs/handoff.json",
            "executor_safety_markdown": ".qa-z/executor/bridge-one/inputs/executor_safety.md",
            "action_context": [
                {
                    "source_path": "docs/source.md",
                    "copied_path": ".qa-z/executor/bridge-one/inputs/context/001-source.md",
                }
            ],
            "action_context_missing": ["docs/missing.md"],
        },
        "safety_package": {
            "policy_json": ".qa-z/executor/bridge-one/inputs/executor_safety.json",
            "policy_markdown": ".qa-z/executor/bridge-one/inputs/executor_safety.md",
            "rule_count": 4,
        },
        "return_contract": {
            "expected_next_step": "run repair-session verify after edits",
            "expected_result_artifact": ".qa-z/executor/bridge-one/result.json",
            "result_template_path": ".qa-z/executor/bridge-one/result_template.json",
            "expected_verify_artifacts": {
                "summary_json": ".qa-z/sessions/session-one/verify/summary.json",
                "compare_json": ".qa-z/sessions/session-one/verify/compare.json",
                "report_markdown": ".qa-z/sessions/session-one/verify/report.md",
            },
            "verify_command": ["python", "-m", "qa_z", "repair-session", "verify"],
        },
        "evidence_summary": {
            "why_selected": ["repair remaining blockers"],
        },
        "live_repository": {
            "dirty": True,
            "tracked_changes": 3,
            "untracked_count": 1,
            "high_signal_paths": ["src/qa_z/executor_bridge.py"],
        },
    }


def test_render_executor_bridge_guide_surfaces_context_and_return_contract() -> None:
    output = render_executor_bridge_guide(
        _manifest(),
        {
            "repair": {
                "objectives": ["Fix the remaining deterministic blocker."],
            }
        },
    )

    assert "# QA-Z External Executor Bridge" in output
    assert "Selected task: `task-1`" in output
    assert "Action context missing:" in output
    assert "run repair-session verify after edits" in output
    assert "verify/report.md" in output


def test_render_bridge_stdout_surfaces_verify_command_and_missing_context() -> None:
    output = render_bridge_stdout(_manifest())

    assert "qa-z executor-bridge: ready_for_external_executor" in output
    assert "Verify command: python -m qa_z repair-session verify" in output
    assert "Missing action context: 1 (docs/missing.md)" in output
