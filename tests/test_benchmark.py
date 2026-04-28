"""Tests for the QA-Z benchmark corpus runner."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from qa_z.benchmark import (
    BenchmarkExpectation,
    benchmark_results_lock,
    compare_expected,
    discover_fixtures,
    reset_directory,
    run_benchmark,
    summarize_deep_actual,
    summarize_executor_dry_run_actual,
)
from qa_z.cli import main
from qa_z.runners.models import CheckResult, RunSummary
from tests.benchmark_test_support import (
    write_config,
    write_contract,
    write_expected,
    write_fast_summary,
)


def test_discover_fixtures_loads_expected_contracts(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    write_expected(
        fixtures_dir / "py_type_error" / "expected.json",
        {
            "name": "py_type_error",
            "run": {"fast": True},
            "expect_fast": {"status": "failed", "failed_checks": ["py_type"]},
        },
    )
    write_expected(
        fixtures_dir / "clean" / "expected.json",
        {"name": "clean", "run": {"fast": True}, "expect_fast": {"status": "passed"}},
    )

    fixtures = discover_fixtures(fixtures_dir)

    assert [fixture.name for fixture in fixtures] == ["clean", "py_type_error"]
    assert fixtures[1].expectation.expect_fast["failed_checks"] == ["py_type"]


def test_compare_expected_reports_precise_missing_fast_check() -> None:
    expectation = BenchmarkExpectation.from_dict(
        {
            "name": "py_type_error",
            "expect_fast": {
                "status": "failed",
                "failed_checks": ["py_type"],
                "schema_version": 2,
            },
        }
    )
    actual = {
        "fast": {
            "status": "failed",
            "failed_checks": ["py_test"],
            "schema_version": 2,
        }
    }

    failures = compare_expected(actual, expectation)

    assert failures == ["fast.failed_checks missing expected values: py_type"]


def test_compare_expected_supports_deep_policy_expectation_keys() -> None:
    expectation = BenchmarkExpectation.from_dict(
        {
            "name": "deep_policy",
            "expect_deep": {
                "status": "passed",
                "blocking_findings_count": 0,
                "filtered_findings_count_min": 1,
                "grouped_findings_count": 1,
                "grouped_findings_min": 1,
                "rule_ids_present": ["generic.safe.warning"],
                "rule_ids_absent": ["python.lang.security.audit.eval"],
                "scan_warning_count": 1,
                "scan_warning_types_present": ["Fixpoint timeout"],
                "scan_warning_paths_present": ["src/app.py"],
                "scan_quality_status": "warning",
                "scan_quality_warning_count": 1,
                "scan_quality_warning_types_present": ["Fixpoint timeout"],
                "scan_quality_warning_paths_present": ["src/app.py"],
                "scan_quality_check_ids_present": ["sg_scan"],
                "expect_config_error": False,
                "schema_version": 2,
            },
        }
    )
    actual = {
        "deep": {
            "status": "passed",
            "blocking_findings_count": 0,
            "filtered_findings_count": 2,
            "grouped_findings_count": 1,
            "rule_ids": ["generic.safe.warning"],
            "scan_warning_count": 1,
            "scan_warning_types": ["Fixpoint timeout"],
            "scan_warning_paths": ["src/app.py"],
            "scan_quality_status": "warning",
            "scan_quality_warning_count": 1,
            "scan_quality_warning_types": ["Fixpoint timeout"],
            "scan_quality_warning_paths": ["src/app.py"],
            "scan_quality_check_ids": ["sg_scan"],
            "config_error": False,
            "schema_version": 2,
        }
    }

    assert compare_expected(actual, expectation) == []


def test_compare_expected_supports_additive_mixed_surface_expectation_aliases() -> None:
    expectation = BenchmarkExpectation.from_dict(
        {
            "name": "mixed_surface_aliases",
            "expect_verify": {
                "verdict": "unchanged",
                "remaining_issue_count_min": 1,
                "resolved_count_min": 0,
                "schema_version": 1,
            },
            "expect_executor_result": {
                "expected_ingest_status": "accepted_partial",
                "expected_recommendation": "continue repair",
                "backlog_categories": ["partial_completion_gap"],
                "warning_ids_absent": ["no_op_without_explanation"],
                "schema_version": 1,
            },
        }
    )
    actual = {
        "verify": {
            "verdict": "unchanged",
            "remaining_issue_count": 2,
            "resolved_count": 0,
            "schema_version": 1,
        },
        "executor_result": {
            "ingest_status": "accepted_partial",
            "next_recommendation": "continue repair",
            "backlog_categories": ["partial_completion_gap"],
            "warning_ids": [],
            "schema_version": 1,
        },
    }

    assert compare_expected(actual, expectation) == []


def test_compare_expected_supports_executor_bridge_expectations() -> None:
    expectation = BenchmarkExpectation.from_dict(
        {
            "name": "bridge_context",
            "expect_executor_bridge": {
                "action_context_count": 1,
                "action_context_paths": [".qa-z/runs/candidate/verify/summary.json"],
                "guide_mentions_missing_action_context": True,
                "schema_version": 1,
            },
        }
    )
    actual = {
        "executor_bridge": {
            "action_context_count": 0,
            "action_context_paths": [],
            "guide_mentions_missing_action_context": False,
            "schema_version": 1,
        }
    }

    assert compare_expected(actual, expectation) == [
        "executor_bridge.action_context_count expected 1 but got 0",
        (
            "executor_bridge.action_context_paths missing expected values: "
            ".qa-z/runs/candidate/verify/summary.json"
        ),
        "executor_bridge.guide_mentions_missing_action_context expected True but got False",
    ]


def test_compare_expected_supports_executor_dry_run_expectations() -> None:
    expectation = BenchmarkExpectation.from_dict(
        {
            "name": "executor_dry_run_aliases",
            "expect_executor_dry_run": {
                "verdict": "attention_required",
                "verdict_reason": "manual_retry_review_required",
                "expected_source": "materialized",
                "history_signals": ["repeated_partial_attempts"],
                "expected_recommendation": "inspect repeated partial attempts before another retry",
                "attention_rule_ids": ["retry_boundary_is_manual"],
                "attention_rule_count": 1,
                "clear_rule_count": 5,
                "blocked_rule_count": 0,
                "clear_rule_ids": ["no_op_requires_explanation"],
                "operator_summary": (
                    "Repeated partial executor attempts need manual review before "
                    "another retry."
                ),
                "recommended_action_ids": ["inspect_partial_attempts"],
                "recommended_action_summaries": [
                    (
                        "Review unresolved repair targets across repeated partial "
                        "attempts before retrying."
                    )
                ],
                "schema_version": 1,
            },
        }
    )
    actual = {
        "executor_dry_run": {
            "verdict": "attention_required",
            "verdict_reason": "manual_retry_review_required",
            "summary_source": "materialized",
            "history_signals": ["repeated_partial_attempts"],
            "next_recommendation": "inspect repeated partial attempts before another retry",
            "attention_rule_ids": ["retry_boundary_is_manual"],
            "attention_rule_count": 1,
            "clear_rule_count": 5,
            "blocked_rule_count": 0,
            "clear_rule_ids": ["no_op_requires_explanation"],
            "operator_summary": (
                "Repeated partial executor attempts need manual review before "
                "another retry."
            ),
            "recommended_action_ids": ["inspect_partial_attempts"],
            "recommended_action_summaries": [
                (
                    "Review unresolved repair targets across repeated partial attempts "
                    "before retrying."
                )
            ],
            "schema_version": 1,
        }
    }

    assert expectation.expect_executor_dry_run["verdict"] == "attention_required"
    assert compare_expected(actual, expectation) == []


def test_summarize_executor_dry_run_actual_preserves_operator_actions() -> None:
    actual = summarize_executor_dry_run_actual(
        {
            "kind": "qa_z.executor_result_dry_run",
            "schema_version": 1,
            "session_id": "session-one",
            "summary_source": "materialized",
            "evaluated_attempt_count": 1,
            "latest_attempt_id": "attempt-one",
            "latest_result_status": "no_op",
            "latest_ingest_status": "accepted_no_op",
            "verdict": "attention_required",
            "verdict_reason": "classification_conflict_requires_review",
            "history_signals": [
                "validation_conflict",
                "missing_no_op_explanation",
            ],
            "operator_summary": (
                "Executor history has validation conflicts that need manual review."
            ),
            "recommended_actions": [
                {
                    "id": "review_validation_conflict",
                    "summary": (
                        "Compare executor validation claims with deterministic "
                        "verification artifacts before retrying."
                    ),
                },
                {
                    "id": "require_no_op_explanation",
                    "summary": (
                        "Ask the executor to explain the no-op or not-applicable "
                        "result before accepting it."
                    ),
                },
            ],
            "next_recommendation": "inspect executor attempt history before another retry",
            "rule_status_counts": {"clear": 4, "attention": 2, "blocked": 0},
            "rule_evaluations": [],
        }
    )

    assert actual["operator_summary"] == (
        "Executor history has validation conflicts that need manual review."
    )
    assert actual["recommended_action_ids"] == [
        "review_validation_conflict",
        "require_no_op_explanation",
    ]
    assert actual["recommended_action_summaries"] == [
        (
            "Compare executor validation claims with deterministic verification "
            "artifacts before retrying."
        ),
        (
            "Ask the executor to explain the no-op or not-applicable result before "
            "accepting it."
        ),
    ]


def test_compare_expected_reports_deep_policy_absent_rule_violations() -> None:
    expectation = BenchmarkExpectation.from_dict(
        {
            "name": "deep_policy",
            "expect_deep": {
                "rule_ids_absent": ["python.lang.security.audit.eval"],
            },
        }
    )
    actual = {
        "deep": {
            "rule_ids": [
                "python.lang.security.audit.eval",
                "generic.safe.warning",
            ],
        }
    }

    failures = compare_expected(actual, expectation)

    assert failures == [
        "deep.rule_ids expected values absent but found: python.lang.security.audit.eval"
    ]


def test_summarize_deep_actual_includes_policy_counts_and_config_errors() -> None:
    summary = RunSummary(
        mode="deep",
        contract_path=None,
        project_root=".",
        status="error",
        started_at="2026-04-14T00:00:00Z",
        finished_at="2026-04-14T00:00:01Z",
        schema_version=2,
        run_resolution={
            "source": "from_run",
            "attached_to_fast_run": True,
            "run_dir": ".qa-z/runs/ci",
            "deep_dir": ".qa-z/runs/ci/deep",
            "fast_summary_path": ".qa-z/runs/ci/fast/summary.json",
        },
        diagnostics={
            "scan_quality": {
                "status": "warning",
                "warning_count": 2,
                "warning_types": ["Fixpoint timeout", "Timeout"],
                "warning_paths": ["src/app.py", "tests/test_app.py"],
                "check_ids": ["sg_scan"],
            }
        },
        checks=[
            CheckResult(
                id="sg_scan",
                tool="semgrep",
                command=["semgrep", "--json"],
                kind="static-analysis",
                status="error",
                exit_code=2,
                duration_ms=1,
                error_type="semgrep_config_error",
                findings_count=3,
                blocking_findings_count=1,
                filtered_findings_count=1,
                filter_reasons={"ignored_rule": 1},
                grouped_findings=[
                    {
                        "rule_id": "python.lang.security.audit.eval",
                        "severity": "ERROR",
                        "path": "src/app.py",
                        "count": 2,
                        "representative_line": 2,
                        "message": "Avoid eval.",
                    }
                ],
                findings=[
                    {
                        "rule_id": "python.lang.security.audit.eval",
                        "severity": "ERROR",
                        "path": "src/app.py",
                        "line": 2,
                        "message": "Avoid eval.",
                    }
                ],
                scan_warning_count=2,
                scan_warnings=[
                    {
                        "error_type": "Fixpoint timeout",
                        "severity": "WARN",
                        "message": "Taint analysis timed out.",
                        "path": "src/app.py",
                        "line": 7,
                    },
                    {
                        "error_type": "Timeout",
                        "severity": "WARN",
                        "message": "Rule timed out.",
                        "path": "tests/test_app.py",
                        "line": 12,
                    },
                ],
            )
        ],
    )

    actual = summarize_deep_actual(summary)

    assert actual["findings_count"] == 3
    assert actual["blocking_findings_count"] == 1
    assert actual["filtered_findings_count"] == 1
    assert actual["grouped_findings_count"] == 1
    assert actual["filter_reasons"] == {"ignored_rule": 1}
    assert actual["rule_ids"] == ["python.lang.security.audit.eval"]
    assert actual["scan_warning_count"] == 2
    assert actual["scan_warning_types"] == ["Fixpoint timeout", "Timeout"]
    assert actual["scan_warning_paths"] == ["src/app.py", "tests/test_app.py"]
    assert actual["scan_quality_status"] == "warning"
    assert actual["scan_quality_warning_count"] == 2
    assert actual["scan_quality_warning_types"] == ["Fixpoint timeout", "Timeout"]
    assert actual["scan_quality_warning_paths"] == ["src/app.py", "tests/test_app.py"]
    assert actual["scan_quality_check_ids"] == ["sg_scan"]
    assert actual["run_resolution_source"] == "from_run"
    assert actual["attached_to_fast_run"] is True
    assert actual["run_resolution_fast_summary_path"] == (
        ".qa-z/runs/ci/fast/summary.json"
    )
    assert actual["error_types"] == ["semgrep_config_error"]
    assert actual["config_error"] is True


def test_run_benchmark_executes_fast_handoff_and_verify_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "fixtures" / "fast_handoff_verify"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "app.py").write_text("value = 'bad'\n", encoding="utf-8")
    write_contract(repo)
    write_config(
        repo,
        [
            {
                "id": "py_type",
                "kind": "typecheck",
                "run": [
                    sys.executable,
                    "-c",
                    "import sys; print('src/app.py:1: error: bad type'); sys.exit(1)",
                ],
            }
        ],
    )
    write_fast_summary(
        repo, "baseline", check_id="py_test", status="failed", exit_code=1
    )
    write_fast_summary(
        repo, "candidate", check_id="py_test", status="passed", exit_code=0
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "fast_handoff_verify",
            "run": {
                "fast": True,
                "repair_handoff": True,
                "verify": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "candidate_run": ".qa-z/runs/candidate",
                },
            },
            "expect_fast": {
                "status": "failed",
                "failed_checks": ["py_type"],
                "schema_version": 2,
            },
            "expect_handoff": {
                "repair_needed": True,
                "target_sources": ["fast_check"],
                "target_ids": ["check:py_type"],
                "affected_files": ["src/app.py"],
                "validation_command_ids": ["check:py_type", "qa-z-fast"],
                "schema_version": 1,
            },
            "expect_verify": {
                "verdict": "improved",
                "blocking_before": 1,
                "blocking_after": 0,
                "resolved_count": 1,
                "schema_version": 1,
            },
            "expect_artifacts": {
                "files": [
                    ".qa-z/runs/benchmark/fast/summary.json",
                    ".qa-z/runs/benchmark/repair/handoff.json",
                    ".qa-z/runs/candidate/verify/summary.json",
                ]
            },
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    assert (tmp_path / "results" / "summary.json").exists()
    assert (tmp_path / "results" / "report.md").exists()
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["fast"]["failed_checks"] == ["py_type"]
    assert fixture_result["actual"]["handoff"]["target_sources"] == ["fast_check"]
    assert fixture_result["actual"]["verify"]["verdict"] == "improved"
    assert fixture_result["categories"]["artifact"] is True


def test_run_benchmark_executes_typescript_fast_handoff_and_verify_fixture(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "ts_fast_handoff_verify"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "invoice.ts").write_text(
        "export const total: number = 'bad';\n", encoding="utf-8"
    )
    write_contract(
        repo,
        related_files=["src/invoice.ts"],
        title="TypeScript benchmark fixture",
    )
    write_config(
        repo,
        [
            {
                "id": "ts_type",
                "kind": "typecheck",
                "run": [
                    sys.executable,
                    ".qa-z-benchmark/fast_check.py",
                    "fail",
                    "src/invoice.ts(1,14): error TS2322: Type 'string' is not assignable to type 'number'.",
                ],
            }
        ],
        languages=["typescript"],
    )
    write_fast_summary(
        repo, "baseline", check_id="ts_type", status="failed", exit_code=1
    )
    write_fast_summary(
        repo, "candidate", check_id="ts_type", status="passed", exit_code=0
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "ts_fast_handoff_verify",
            "run": {
                "fast": True,
                "repair_handoff": True,
                "verify": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "candidate_run": ".qa-z/runs/candidate",
                },
            },
            "expect_fast": {
                "status": "failed",
                "blocking_failed_checks": ["ts_type"],
                "schema_version": 2,
            },
            "expect_handoff": {
                "repair_needed": True,
                "target_sources": ["fast_check"],
                "target_ids": ["check:ts_type"],
                "affected_files": ["src/invoice.ts"],
                "validation_command_ids": ["check:ts_type", "qa-z-fast"],
                "schema_version": 1,
            },
            "expect_verify": {
                "verdict": "improved",
                "blocking_before": 1,
                "blocking_after": 0,
                "resolved_count": 1,
                "schema_version": 1,
            },
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["fast"]["blocking_failed_checks"] == ["ts_type"]
    assert fixture_result["actual"]["handoff"]["target_sources"] == ["fast_check"]
    assert fixture_result["actual"]["verify"]["verdict"] == "improved"
    assert fixture_result["categories"]["detection"] is True
    assert fixture_result["categories"]["handoff"] is True
    assert fixture_result["categories"]["verify"] is True


def test_run_benchmark_executes_maintenance_verify_fixture_with_remaining_issue_count(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "mixed_docs_schema_sync_maintenance_candidate"
    repo = fixture / "repo"
    write_contract(
        repo,
        related_files=["README.md", "docs/artifact-schema-v1.md"],
        title="Docs/schema sync maintenance fixture",
    )
    write_config(
        repo,
        [{"id": "docs_schema", "kind": "lint", "run": [sys.executable, "-c", ""]}],
    )
    write_fast_summary(
        repo, "baseline", check_id="docs_schema", status="failed", exit_code=1
    )
    write_fast_summary(
        repo, "candidate", check_id="docs_schema", status="failed", exit_code=1
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "mixed_docs_schema_sync_maintenance_candidate",
            "run": {
                "verify": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "candidate_run": ".qa-z/runs/candidate",
                }
            },
            "expect_verify": {
                "verdict": "unchanged",
                "blocking_before": 1,
                "blocking_after": 1,
                "remaining_issue_count_min": 1,
                "resolved_count": 0,
                "new_issue_count": 0,
                "schema_version": 1,
            },
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["verify"]["verdict"] == "unchanged"
    assert fixture_result["actual"]["verify"]["remaining_issue_count"] == 1


def test_benchmark_cli_writes_report_and_returns_success(
    tmp_path: Path, capsys
) -> None:
    fixture = tmp_path / "fixtures" / "clean_fast"
    repo = fixture / "repo"
    write_contract(repo)
    write_config(
        repo,
        [
            {
                "id": "py_test",
                "kind": "test",
                "run": [sys.executable, "-c", ""],
            }
        ],
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "clean_fast",
            "run": {"fast": True},
            "expect_fast": {
                "status": "passed",
                "failed_checks": [],
                "schema_version": 2,
            },
        },
    )

    exit_code = main(
        [
            "benchmark",
            "--path",
            str(tmp_path),
            "--fixtures-dir",
            "fixtures",
            "--results-dir",
            "results",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "# QA-Z Benchmark Report" in output
    assert (tmp_path / "results" / "summary.json").exists()


def test_benchmark_results_lock_records_operator_metadata(tmp_path: Path) -> None:
    results_dir = tmp_path / "results"
    results_dir.mkdir()

    with benchmark_results_lock(results_dir):
        lock_text = (results_dir / ".benchmark.lock").read_text(encoding="utf-8")

    assert f"pid={os.getpid()}" in lock_text
    assert "started_at=" in lock_text
    assert str(results_dir) in lock_text


def test_reset_directory_retries_permission_error_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "work"
    target.mkdir()
    (target / "artifact.txt").write_text("old", encoding="utf-8")
    calls: list[str] = []
    original_rmtree = __import__("shutil").rmtree

    def flaky_rmtree(path: Path) -> None:
        calls.append("rmtree")
        if len(calls) == 1:
            raise PermissionError("locked")
        original_rmtree(path)

    monkeypatch.setattr("qa_z.benchmark_workspace.shutil.rmtree", flaky_rmtree)
    monkeypatch.setattr("qa_z.benchmark_workspace.time.sleep", lambda _seconds: None)

    reset_directory(target)

    assert calls == ["rmtree", "rmtree"]
    assert target.exists()
    assert list(target.iterdir()) == []
