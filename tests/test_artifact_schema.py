"""Schema stability tests for QA-Z artifacts."""

from __future__ import annotations

from pathlib import Path

from qa_z.benchmark import BenchmarkFixtureResult, build_benchmark_summary
from qa_z.reporters.run_summary import (
    render_summary_markdown,
    write_run_summary_artifacts,
)
from qa_z.reporters.repair_prompt import FailureContext, RepairPacket
from qa_z.executor_result import (
    ExecutorChangedFile,
    ExecutorResult,
    ExecutorValidation,
    ExecutorValidationResult,
    ingest_summary_dict,
)
from qa_z.executor_history import executor_result_history_payload
from qa_z.executor_safety import EXECUTOR_SAFETY_RULE_IDS, executor_safety_package
from qa_z.repair_session import RepairSession
from qa_z.diffing.models import ChangedFile
from qa_z.runners.models import CheckResult, RunSummary, SelectionSummary
from tests.runtime_artifact_cleanup_test_support import load_cleanup_module


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


def test_run_summary_per_check_artifacts_use_safe_unique_filenames(
    tmp_path: Path,
) -> None:
    summary = RunSummary(
        mode="fast",
        contract_path="qa/contracts/example.md",
        project_root="/repo",
        status="failed",
        started_at="2026-04-11T12:00:00Z",
        finished_at="2026-04-11T12:00:01Z",
        checks=[
            CheckResult(
                id="../escape",
                tool="custom",
                command=["custom"],
                kind="custom",
                status="failed",
                exit_code=1,
                duration_ms=1,
            ),
            CheckResult(
                id="../escape",
                tool="custom",
                command=["custom"],
                kind="custom",
                status="failed",
                exit_code=1,
                duration_ms=1,
            ),
        ],
    )

    write_run_summary_artifacts(summary, tmp_path / "run")

    assert (tmp_path / "run" / "checks" / "escape.json").exists()
    assert (tmp_path / "run" / "checks" / "escape-2.json").exists()
    assert not (tmp_path / "run" / "escape.json").exists()


def test_runtime_artifact_cleanup_schema_v1_required_fields_are_stable(
    tmp_path: Path,
) -> None:
    module = load_cleanup_module()
    (tmp_path / ".qa-z" / "runs").mkdir(parents=True)

    def runner(command, _cwd):
        if tuple(command) == (
            "git",
            "status",
            "--short",
            "--ignored",
            "--untracked-files=all",
        ):
            return (0, "?? .qa-z/runs/summary.json\n", "")
        return (0, "", "")

    payload = module.collect_cleanup_plan(tmp_path, runner=runner)
    candidate = payload["candidates"][0]

    assert payload["kind"] == "qa_z.runtime_artifact_cleanup"
    assert payload["schema_version"] == 1
    assert {
        "kind",
        "schema_version",
        "generated_at",
        "repo_root",
        "mode",
        "candidates",
        "counts",
    } <= payload.keys()
    assert {
        "path",
        "kind",
        "policy_bucket",
        "status",
        "reason",
        "tracked_paths",
    } <= candidate.keys()
    assert candidate["reason"]


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


def test_run_summary_schema_v2_diagnostics_are_persisted() -> None:
    summary = RunSummary(
        mode="deep",
        contract_path="qa/contracts/example.md",
        project_root="/repo",
        status="passed",
        started_at="2026-04-11T12:00:00Z",
        finished_at="2026-04-11T12:00:01Z",
        schema_version=2,
        diagnostics={
            "scan_quality": {
                "status": "warning",
                "warning_count": 1,
                "warning_types": ["Fixpoint timeout"],
                "warning_paths": ["src/app.py"],
                "check_ids": ["sg_scan"],
            }
        },
        checks=[],
    )

    payload = summary.to_dict()
    loaded = RunSummary.from_dict(payload)

    assert payload["diagnostics"]["scan_quality"]["status"] == "warning"
    assert payload["diagnostics"]["scan_quality"]["warning_count"] == 1
    assert loaded.diagnostics["scan_quality"]["warning_types"] == ["Fixpoint timeout"]


def test_run_summary_redacts_summary_level_diagnostics_and_markdown() -> None:
    summary = RunSummary(
        mode="deep",
        contract_path="qa/contracts/example.md",
        project_root="/repo",
        status="failed",
        started_at="2026-04-11T12:00:00Z",
        finished_at="2026-04-11T12:00:01Z",
        schema_version=2,
        message="api_key=abcdef",
        diagnostics={
            "scan_quality": {
                "status": "warning",
                "warning_count": 1,
                "warning_types": ["Authorization: Bearer abc.def.ghi"],
                "warning_paths": ["src/app.py"],
                "check_ids": ["sg_scan"],
            }
        },
        checks=[
            CheckResult(
                id="secret_check",
                tool="custom",
                command=["custom"],
                kind="static-analysis",
                status="failed",
                exit_code=1,
                duration_ms=1,
                message="password=hunter2",
            )
        ],
    )

    payload = summary.to_dict()
    markdown = render_summary_markdown(summary)

    assert "abcdef" not in payload["message"]
    assert "abc.def.ghi" not in str(payload["diagnostics"])
    assert "hunter2" not in markdown
    assert "abc.def.ghi" not in markdown
    assert "[REDACTED_SECRET]" in markdown
    assert "[REDACTED_TOKEN]" in markdown


def test_run_summary_redacts_prefixed_env_secret_names_in_json_and_markdown() -> None:
    summary = RunSummary(
        mode="deep",
        contract_path="qa/contracts/example.md",
        project_root="/repo",
        status="failed",
        started_at="2026-04-11T12:00:00Z",
        finished_at="2026-04-11T12:00:01Z",
        schema_version=2,
        message="GITHUB_TOKEN=github-raw",
        diagnostics={
            "scan_quality": {
                "status": "warning",
                "warning_count": 1,
                "warning_types": ["OPENAI_API_KEY=openai-raw"],
                "warning_paths": ["src/app.py"],
                "check_ids": ["sg_scan"],
            }
        },
        checks=[
            CheckResult(
                id="secret_check",
                tool="custom",
                command=["custom", "CLIENT_SECRET=client-raw"],
                kind="static-analysis",
                status="failed",
                exit_code=1,
                duration_ms=1,
                message="AWS_SECRET_ACCESS_KEY=aws-raw",
            )
        ],
    )

    payload = summary.to_dict()
    markdown = render_summary_markdown(summary)
    rendered = f"{payload}\n{markdown}"

    for raw_secret in ("github-raw", "openai-raw", "client-raw", "aws-raw"):
        assert raw_secret not in rendered
    assert "GITHUB_TOKEN=[REDACTED_TOKEN]" in payload["message"]
    assert "OPENAI_API_KEY=[REDACTED_SECRET]" in str(payload["diagnostics"])
    assert "AWS_SECRET_ACCESS_KEY=[REDACTED_SECRET]" in markdown


def test_run_summary_redacts_secret_like_mapping_keys() -> None:
    summary = RunSummary(
        mode="deep",
        contract_path="qa/contracts/example.md",
        project_root="/repo",
        status="failed",
        started_at="2026-04-11T12:00:00Z",
        finished_at="2026-04-11T12:00:01Z",
        schema_version=2,
        diagnostics={
            "scan_quality": {
                "status": "warning",
                "warning_count": 1,
                "GITHUB_TOKEN": "github-raw",
                "token_count": 3,
            }
        },
        checks=[],
    )

    payload = summary.to_dict()

    assert "github-raw" not in str(payload)
    assert payload["diagnostics"]["scan_quality"]["GITHUB_TOKEN"] == (
        "[REDACTED_TOKEN]"
    )
    assert payload["diagnostics"]["scan_quality"]["token_count"] == 3


def test_run_summary_markdown_tolerates_malformed_diagnostics() -> None:
    summary = RunSummary(
        mode="deep",
        contract_path="qa/contracts/example.md",
        project_root="/repo",
        status="passed",
        started_at="2026-04-11T12:00:00Z",
        finished_at="2026-04-11T12:00:01Z",
        schema_version=2,
        diagnostics={
            "scan_quality": {
                "status": "warning",
                "warning_count": "many",
                "warning_types": ["Fixpoint timeout", None],
                "warning_paths": "src/app.py",
                "check_ids": ["sg_scan"],
            }
        },
        checks=[],
    )

    markdown = render_summary_markdown(summary)

    assert "- Scan quality: warning (0 warnings)" in markdown
    assert "- Warning types: Fixpoint timeout" in markdown
    assert "- Warning paths: none" in markdown
    assert "- Warning checks: sg_scan" in markdown


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
    assert loaded.diagnostics == {}


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


def test_repair_session_schema_v1_required_fields_are_stable() -> None:
    session = RepairSession(
        session_id="session-one",
        session_dir=".qa-z/sessions/session-one",
        baseline_run_dir=".qa-z/runs/baseline",
        baseline_fast_summary_path=".qa-z/runs/baseline/fast/summary.json",
        handoff_dir=".qa-z/sessions/session-one/handoff",
        handoff_artifacts={
            "handoff_json": ".qa-z/sessions/session-one/handoff/handoff.json"
        },
        executor_guide_path=".qa-z/sessions/session-one/executor_guide.md",
        state="waiting_for_external_repair",
        created_at="2026-04-14T00:00:00Z",
        updated_at="2026-04-14T00:00:00Z",
        safety_artifacts={
            "policy_json": ".qa-z/sessions/session-one/executor_safety.json",
            "policy_markdown": ".qa-z/sessions/session-one/executor_safety.md",
        },
    )

    payload = session.to_dict()
    loaded = RepairSession.from_dict(payload)

    assert payload["kind"] == "qa_z.repair_session"
    assert payload["schema_version"] == 1
    assert {
        "kind",
        "schema_version",
        "session_id",
        "session_dir",
        "state",
        "created_at",
        "updated_at",
        "baseline_run_dir",
        "baseline_fast_summary_path",
        "baseline_deep_summary_path",
        "handoff_dir",
        "handoff_artifacts",
        "executor_guide_path",
        "safety_artifacts",
        "candidate_run_dir",
        "verify_dir",
        "verify_artifacts",
        "outcome_path",
        "summary_path",
        "provenance",
    } <= payload.keys()
    assert loaded.session_id == "session-one"
    assert loaded.state == "waiting_for_external_repair"
    assert loaded.safety_artifacts["policy_json"].endswith("executor_safety.json")


def test_benchmark_summary_schema_v1_snapshot_field_is_stable() -> None:
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="passing_case",
                passed=True,
                failures=[],
                categories={"detection": True},
                actual={},
                artifacts={},
            ),
            BenchmarkFixtureResult(
                name="failing_case",
                passed=False,
                failures=["fast.status expected passed but got failed"],
                categories={"detection": False},
                actual={},
                artifacts={},
            ),
        ]
    )

    assert summary["kind"] == "qa_z.benchmark_summary"
    assert summary["schema_version"] == 1
    assert {
        "kind",
        "schema_version",
        "fixtures_total",
        "fixtures_passed",
        "fixtures_failed",
        "overall_rate",
        "snapshot",
        "category_rates",
        "failed_fixtures",
        "fixtures",
    } <= summary.keys()
    assert summary["snapshot"] == "1/2 fixtures, overall_rate 0.5"


def test_worktree_commit_plan_schema_is_documented() -> None:
    schema = (
        Path(__file__).resolve().parents[1] / "docs" / "artifact-schema-v1.md"
    ).read_text(encoding="utf-8")

    assert "`kind`: `qa_z.worktree_commit_plan`" in schema
    assert "`summary`" in schema
    assert "`validation_commands`" in schema
    assert "`generated_artifact_paths`" in schema
    assert "`generated_local_only_paths`" in schema
    assert "`generated_local_by_default_paths`" in schema
    assert "`unassigned_source_paths`" in schema


def test_alpha_release_preflight_generated_policy_split_is_documented() -> None:
    schema = (
        Path(__file__).resolve().parents[1] / "docs" / "artifact-schema-v1.md"
    ).read_text(encoding="utf-8")

    assert "`tracked_generated_artifact_count`" in schema
    assert "`generated_local_only_tracked_count`" in schema
    assert "`generated_local_by_default_tracked_count`" in schema
    assert "`generated_local_only_tracked_paths`" in schema
    assert "`generated_local_by_default_tracked_paths`" in schema
    assert "local-only runtime artifacts" in schema
    assert "local-by-default benchmark evidence" in schema


def test_executor_safety_package_schema_v1_required_fields_are_stable() -> None:
    payload = executor_safety_package()

    assert payload["kind"] == "qa_z.executor_safety"
    assert payload["schema_version"] == 1
    assert {
        "kind",
        "schema_version",
        "package_id",
        "status",
        "summary",
        "rules",
        "non_goals",
        "enforcement_points",
    } <= payload.keys()
    assert payload["package_id"] == "pre_live_executor_safety_v1"
    assert tuple(rule["id"] for rule in payload["rules"]) == EXECUTOR_SAFETY_RULE_IDS
    assert any(
        rule["id"] == "verification_required_for_completed" for rule in payload["rules"]
    )


def test_executor_result_history_schema_v1_required_fields_are_stable() -> None:
    payload = executor_result_history_payload(
        session_id="session-one",
        attempts=[
            {
                "attempt_id": "bridge-session-20260416t000000z",
                "recorded_at": "2026-04-16T00:00:00Z",
                "bridge_id": "bridge-session",
                "source_loop_id": None,
                "result_status": "partial",
                "ingest_status": "accepted_partial",
                "verify_resume_status": "verify_blocked",
                "verification_hint": "skip",
                "verification_triggered": False,
                "verification_verdict": None,
                "validation_status": "failed",
                "warning_ids": [],
                "backlog_categories": ["partial_completion_gap"],
                "changed_files_count": 1,
                "notes_count": 1,
                "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/bridge-session-20260416t000000z.json",
                "ingest_artifact_path": ".qa-z/executor-results/bridge-session-20260416t000000z/ingest.json",
                "ingest_report_path": ".qa-z/executor-results/bridge-session-20260416t000000z/ingest_report.md",
            }
        ],
        updated_at="2026-04-16T00:00:00Z",
    )

    assert payload["kind"] == "qa_z.executor_result_history"
    assert payload["schema_version"] == 1
    assert {
        "kind",
        "schema_version",
        "session_id",
        "updated_at",
        "attempt_count",
        "latest_attempt_id",
        "attempts",
    } <= payload.keys()
    assert {
        "attempt_id",
        "recorded_at",
        "bridge_id",
        "source_loop_id",
        "result_status",
        "ingest_status",
        "verify_resume_status",
        "verification_hint",
        "verification_triggered",
        "verification_verdict",
        "validation_status",
        "warning_ids",
        "backlog_categories",
        "changed_files_count",
        "notes_count",
        "attempt_path",
        "ingest_artifact_path",
        "ingest_report_path",
    } <= payload["attempts"][0].keys()


def test_executor_result_schema_v1_required_fields_are_stable() -> None:
    result = ExecutorResult(
        bridge_id="bridge-one",
        source_session_id="session-one",
        source_loop_id="loop-20260415-000000-01",
        created_at="2026-04-16T00:00:00Z",
        status="completed",
        summary="Applied the scoped repair and left unrelated files untouched.",
        verification_hint="rerun",
        candidate_run_dir=None,
        changed_files=[
            ExecutorChangedFile(
                path="src/qa_z/executor_result.py",
                status="added",
                summary="Added ingest workflow support.",
            )
        ],
        validation=ExecutorValidation(
            status="passed",
            commands=[["python", "-m", "pytest"]],
            results=[
                ExecutorValidationResult(
                    command=["python", "-m", "pytest"],
                    status="passed",
                    exit_code=0,
                    summary="pytest passed locally",
                )
            ],
        ),
        notes=["verification rerun required before merge"],
    )

    payload = result.to_dict()
    loaded = ExecutorResult.from_dict(payload)

    assert payload["kind"] == "qa_z.executor_result"
    assert payload["schema_version"] == 1
    assert {
        "kind",
        "schema_version",
        "bridge_id",
        "source_session_id",
        "source_loop_id",
        "created_at",
        "status",
        "summary",
        "verification_hint",
        "candidate_run_dir",
        "changed_files",
        "validation",
        "notes",
    } <= payload.keys()
    assert {
        "path",
        "status",
        "old_path",
        "summary",
    } <= payload["changed_files"][0].keys()
    assert {
        "status",
        "commands",
        "results",
    } <= payload["validation"].keys()
    assert {
        "command",
        "status",
        "exit_code",
        "summary",
    } <= payload["validation"]["results"][0].keys()
    assert loaded.bridge_id == "bridge-one"
    assert loaded.validation.status == "passed"


def test_executor_result_ingest_schema_v1_required_fields_are_stable() -> None:
    payload = ingest_summary_dict(
        result_id="bridge-one-20260416t000000z",
        bridge_id="bridge-one",
        session_id="session-one",
        source_loop_id="loop-20260415-000000-01",
        result_status="completed",
        stored_result_path=None,
        root=Path("/repo"),
        session_state="candidate_generated",
        verification_hint="rerun",
        verification_triggered=False,
        verification_verdict=None,
        verify_summary_path=None,
        next_recommendation="run repair-session verify",
        ingest_status="accepted",
        warnings=[],
        freshness_check={"status": "passed", "details": []},
        provenance_check={"status": "passed", "details": []},
        verify_resume_status="ready_for_verify",
        backlog_implications=[],
        ingest_artifact_path=Path(
            "/repo/.qa-z/executor-results/result-one/ingest.json"
        ),
        ingest_report_path=Path(
            "/repo/.qa-z/executor-results/result-one/ingest_report.md"
        ),
    )

    assert payload["kind"] == "qa_z.executor_result_ingest"
    assert payload["schema_version"] == 1
    assert {
        "kind",
        "schema_version",
        "result_id",
        "bridge_id",
        "session_id",
        "source_loop_id",
        "result_status",
        "ingest_status",
        "stored_result_path",
        "session_state",
        "verification_hint",
        "verification_triggered",
        "verification_verdict",
        "verify_summary_path",
        "warnings",
        "freshness_check",
        "provenance_check",
        "verify_resume_status",
        "backlog_implications",
        "next_recommendation",
        "ingest_artifact_path",
        "ingest_report_path",
    } <= payload.keys()
