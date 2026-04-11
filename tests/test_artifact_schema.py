"""Schema stability tests for QA-Z artifacts."""

from __future__ import annotations

from qa_z.reporters.repair_prompt import FailureContext, RepairPacket
from qa_z.runners.models import CheckResult, RunSummary


def test_run_summary_schema_v1_required_fields_are_stable() -> None:
    summary = RunSummary(
        mode="fast",
        contract_path="qa/contracts/example.md",
        project_root="/repo",
        status="failed",
        started_at="2026-04-11T12:00:00Z",
        finished_at="2026-04-11T12:00:01Z",
        artifact_dir=".qa-z/runs/example/fast",
        checks=[
            CheckResult(
                id="py_test",
                tool="pytest",
                command=["pytest", "-q"],
                kind="test",
                status="failed",
                exit_code=1,
                duration_ms=123,
                stdout_tail="tests/test_example.py:1: assertion failed\n",
            )
        ],
    )

    payload = summary.to_dict()

    assert payload["schema_version"] == 1
    assert {
        "schema_version",
        "mode",
        "contract_path",
        "project_root",
        "status",
        "started_at",
        "finished_at",
        "artifact_dir",
        "checks",
        "totals",
    } <= payload.keys()
    assert {
        "id",
        "tool",
        "command",
        "kind",
        "status",
        "exit_code",
        "duration_ms",
        "stdout_tail",
        "stderr_tail",
    } <= payload["checks"][0].keys()
    assert RunSummary.from_dict(payload).schema_version == 1


def test_repair_packet_schema_v1_required_fields_are_stable() -> None:
    packet = RepairPacket(
        version=1,
        generated_at="2026-04-11T12:00:02Z",
        repair_needed=True,
        run={
            "dir": ".qa-z/runs/example",
            "status": "failed",
            "contract_path": "qa/contracts/example.md",
            "started_at": "2026-04-11T12:00:00Z",
            "finished_at": "2026-04-11T12:00:01Z",
        },
        contract={
            "path": "qa/contracts/example.md",
            "title": "Example",
            "summary": "Example summary.",
            "scope_items": ["example scope"],
            "acceptance_checks": ["run fast checks"],
            "constraints": ["Do not weaken tests."],
        },
        failures=[
            FailureContext(
                id="py_test",
                kind="test",
                tool="pytest",
                command=["pytest", "-q"],
                exit_code=1,
                duration_ms=123,
                summary="pytest exited with code 1.",
                stdout_tail="tests/test_example.py:1: assertion failed\n",
                stderr_tail="",
                candidate_files=["tests/test_example.py"],
            )
        ],
        suggested_fix_order=["py_test"],
        done_when=["qa-z fast exits with code 0"],
        agent_prompt="# QA-Z Repair Prompt\n",
    )

    payload = packet.to_dict()

    assert payload["version"] == 1
    assert {
        "version",
        "generated_at",
        "repair_needed",
        "run",
        "contract",
        "failures",
        "suggested_fix_order",
        "done_when",
        "agent_prompt",
    } <= payload.keys()
    assert {
        "id",
        "kind",
        "tool",
        "command",
        "exit_code",
        "duration_ms",
        "summary",
        "stdout_tail",
        "stderr_tail",
        "candidate_files",
    } <= payload["failures"][0].keys()
