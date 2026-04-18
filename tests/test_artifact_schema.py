"""Schema stability tests for QA-Z artifacts."""

from __future__ import annotations

from pathlib import Path

from qa_z.diffing.models import ChangedFile
from qa_z.reporters.repair_prompt import FailureContext, RepairPacket
from qa_z.runners.models import CheckResult, RunSummary, SelectionSummary


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


def test_run_summary_schema_v2_selection_fields_are_persisted() -> None:
    changed_file = ChangedFile(
        path="src/qa_z/cli.py",
        old_path="src/qa_z/cli.py",
        status="modified",
        additions=8,
        deletions=2,
        language="python",
        kind="source",
    )
    summary = RunSummary(
        mode="fast",
        contract_path="qa/contracts/example.md",
        project_root="/repo",
        status="passed",
        started_at="2026-04-11T12:00:00Z",
        finished_at="2026-04-11T12:00:01Z",
        schema_version=2,
        selection=SelectionSummary(
            mode="smart",
            input_source="cli_diff",
            changed_files=[changed_file],
            selected_checks=["py_lint"],
            targeted_checks=["py_lint"],
        ),
        checks=[
            CheckResult(
                id="py_lint",
                tool="ruff",
                command=["ruff", "check", "src/qa_z/cli.py"],
                kind="lint",
                status="passed",
                exit_code=0,
                duration_ms=123,
                execution_mode="targeted",
                target_paths=["src/qa_z/cli.py"],
                selection_reason="python source/test files changed",
            )
        ],
    )

    payload = summary.to_dict()
    loaded = RunSummary.from_dict(payload)

    assert payload["schema_version"] == 2
    assert payload["selection"]["changed_files"][0]["path"] == "src/qa_z/cli.py"
    assert payload["checks"][0]["execution_mode"] == "targeted"
    assert loaded.selection is not None
    assert loaded.selection.input_source == "cli_diff"
    assert loaded.selection.changed_files[0].kind == "source"
    assert loaded.checks[0].target_paths == ["src/qa_z/cli.py"]


def test_run_summary_loads_v1_without_schema_version_or_selection() -> None:
    loaded = RunSummary.from_dict(
        {
            "mode": "fast",
            "contract_path": None,
            "project_root": "/repo",
            "status": "passed",
            "started_at": "2026-04-11T12:00:00Z",
            "finished_at": "2026-04-11T12:00:01Z",
            "checks": [],
        }
    )

    assert loaded.schema_version == 1
    assert loaded.selection is None


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


def test_artifact_schema_documents_repair_session_and_publish_summary() -> None:
    schema = Path("docs/artifact-schema-v1.md").read_text(encoding="utf-8")

    assert "qa_z.repair_session" in schema
    assert "qa_z.repair_session_summary" in schema
    assert "qa_z.verification_publish_summary" in schema
    assert "qa_z.executor_bridge" in schema
    assert "executor-bridge" in schema
    assert "github-summary" in schema
