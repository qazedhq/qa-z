"""Tests for the QA-Z benchmark corpus runner."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from textwrap import dedent

from qa_z.benchmark import (
    BenchmarkExpectation,
    BenchmarkFixtureResult,
    build_benchmark_summary,
    compare_expected,
    discover_fixtures,
    render_benchmark_report,
    run_benchmark,
    summarize_deep_actual,
    summarize_executor_dry_run_actual,
)
from qa_z.cli import main
from qa_z.executor_dry_run_logic import DRY_RUN_RULE_IDS
from qa_z.runners.models import CheckResult, RunSummary


def write_expected(path: Path, payload: dict[str, object]) -> None:
    """Write an expected.json fixture contract."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_json(path: Path, payload: dict[str, object]) -> None:
    """Write a deterministic JSON object fixture."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_config(
    root: Path,
    checks: list[dict[str, object]],
    *,
    languages: list[str] | None = None,
) -> None:
    """Write a minimal QA-Z config with explicit fast checks."""
    config = {
        "project": {
            "name": "benchmark-fixture",
            "languages": languages or ["python"],
        },
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {
            "output_dir": ".qa-z/runs",
            "fail_on_missing_tool": True,
            "checks": checks,
        },
        "deep": {"checks": []},
    }
    root.joinpath("qa-z.yaml").write_text(
        json.dumps(config, indent=2) + "\n", encoding="utf-8"
    )


def write_contract(
    root: Path,
    *,
    related_files: list[str] | None = None,
    title: str = "Benchmark fixture",
) -> None:
    """Write a contract with one candidate source file."""
    contract = root / "qa" / "contracts" / "contract.md"
    contract.parent.mkdir(parents=True, exist_ok=True)
    files = related_files or ["src/app.py"]
    contract.write_text(
        dedent(
            f"""
            # QA Contract: {title}

            ## Related Files

            {chr(10).join(f"- {path}" for path in files)}

            ## Acceptance Checks

            - Configured fast checks must pass.
            """
        ).strip()
        + "\n",
        encoding="utf-8",
    )


def write_fast_summary(
    root: Path, run_id: str, *, check_id: str, status: str, exit_code: int | None
) -> None:
    """Write a minimal fast summary artifact for verification fixtures."""
    run_dir = root / ".qa-z" / "runs" / run_id / "fast"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "mode": "fast",
        "contract_path": "qa/contracts/contract.md",
        "project_root": str(root),
        "status": "failed" if status in {"failed", "error"} else "passed",
        "started_at": "2026-04-14T00:00:00Z",
        "finished_at": "2026-04-14T00:00:01Z",
        "artifact_dir": f".qa-z/runs/{run_id}/fast",
        "checks": [
            {
                "id": check_id,
                "tool": check_id,
                "command": [check_id],
                "kind": "test",
                "status": status,
                "exit_code": exit_code,
                "duration_ms": 1,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        ],
    }
    run_dir.joinpath("summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def write_mixed_fast_summary(
    root: Path,
    run_id: str,
    *,
    py_status: str,
    py_exit_code: int | None,
    ts_status: str,
    ts_exit_code: int | None,
) -> None:
    """Write a mixed Python/TypeScript fast summary artifact."""
    run_dir = root / ".qa-z" / "runs" / run_id / "fast"
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 2,
        "mode": "fast",
        "contract_path": "qa/contracts/contract.md",
        "project_root": str(root),
        "status": "failed"
        if {py_status, ts_status} & {"failed", "error"}
        else "passed",
        "started_at": "2026-04-14T00:00:00Z",
        "finished_at": "2026-04-14T00:00:01Z",
        "artifact_dir": f".qa-z/runs/{run_id}/fast",
        "checks": [
            {
                "id": "py_test",
                "tool": "pytest",
                "command": ["pytest", "-q"],
                "kind": "test",
                "status": py_status,
                "exit_code": py_exit_code,
                "duration_ms": 1,
                "stdout_tail": "",
                "stderr_tail": "",
            },
            {
                "id": "ts_type",
                "tool": "tsc",
                "command": ["tsc", "--noEmit"],
                "kind": "typecheck",
                "status": ts_status,
                "exit_code": ts_exit_code,
                "duration_ms": 1,
                "stdout_tail": "",
                "stderr_tail": "",
            },
        ],
    }
    run_dir.joinpath("summary.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
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
    assert actual["error_types"] == ["semgrep_config_error"]
    assert actual["config_error"] is True


def test_build_benchmark_summary_calculates_category_rates() -> None:
    results = [
        BenchmarkFixtureResult(
            name="fast_case",
            passed=True,
            failures=[],
            categories={
                "detection": True,
                "handoff": None,
                "verify": None,
                "policy": None,
            },
            actual={},
            artifacts={},
        ),
        BenchmarkFixtureResult(
            name="handoff_case",
            passed=False,
            failures=["handoff.repair_needed expected True but got False"],
            categories={
                "detection": True,
                "handoff": False,
                "verify": None,
                "policy": True,
            },
            actual={},
            artifacts={},
        ),
    ]

    summary = build_benchmark_summary(results)

    assert summary["fixtures_total"] == 2
    assert summary["fixtures_passed"] == 1
    assert summary["fixtures_failed"] == 1
    assert summary["snapshot"] == "1/2 fixtures, overall_rate 0.5"
    assert summary["category_rates"]["detection"] == {
        "passed": 2,
        "total": 2,
        "rate": 1.0,
    }
    assert summary["category_rates"]["handoff"] == {
        "passed": 0,
        "total": 1,
        "rate": 0.0,
    }
    assert summary["category_rates"]["policy"] == {
        "passed": 1,
        "total": 1,
        "rate": 1.0,
    }


def test_build_benchmark_summary_counts_executor_dry_run_fixtures_under_policy() -> (
    None
):
    results = [
        BenchmarkFixtureResult(
            name="dry_run_case",
            passed=True,
            failures=[],
            categories={
                "detection": None,
                "handoff": None,
                "verify": None,
                "artifact": None,
                "policy": True,
            },
            actual={"executor_dry_run": {"verdict": "clear"}},
            artifacts={},
        )
    ]

    summary = build_benchmark_summary(results)

    assert summary["category_rates"]["policy"] == {
        "passed": 1,
        "total": 1,
        "rate": 1.0,
    }


def test_render_benchmark_report_includes_failed_fixture_reasons() -> None:
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="handoff_case",
                passed=False,
                failures=[
                    "handoff.target_sources missing expected values: deep_finding"
                ],
                categories={"detection": None, "handoff": False, "verify": None},
                actual={},
                artifacts={},
            )
        ]
    )

    report = render_benchmark_report(summary)

    assert "# QA-Z Benchmark Report" in report
    assert "- Snapshot: 0/1 fixtures, overall_rate 0.0" in report
    assert "- Fixtures failed: 1" in report
    assert "handoff_case" in report
    assert "handoff.target_sources missing expected values: deep_finding" in report


def test_render_benchmark_report_includes_generated_policy_and_category_coverage() -> (
    None
):
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="handoff_case",
                passed=False,
                failures=[
                    "handoff.target_sources missing expected values: deep_finding"
                ],
                categories={
                    "detection": None,
                    "handoff": False,
                    "verify": None,
                    "artifact": None,
                    "policy": None,
                },
                actual={},
                artifacts={},
            )
        ]
    )

    report = render_benchmark_report(summary)

    assert "## Generated Output Policy" in report
    assert (
        "- `benchmarks/results/summary.json` and "
        "`benchmarks/results/report.md` are generated benchmark outputs."
    ) in report
    assert (
        "- They are local by default; commit them only as intentional frozen "
        "evidence with surrounding context."
    ) in report
    assert "- `benchmarks/results/work/` is disposable scratch output." in report
    assert "- handoff: 0/1 (0.0, covered)" in report
    assert "- detection: 0/0 (0.0, not covered)" in report


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


def test_run_benchmark_executes_executor_result_candidate_run_fixture(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "executor_result_mixed_candidate_run"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "app.py").write_text("def answer():\n    return 42\n")
    repo.joinpath("src", "invoice.ts").write_text(
        "export const total: number = 1;\n", encoding="utf-8"
    )
    write_contract(
        repo,
        related_files=["src/app.py", "src/invoice.ts"],
        title="Executor result mixed candidate benchmark fixture",
    )
    write_config(
        repo,
        [{"id": "py_test", "kind": "test", "run": [sys.executable, "-c", ""]}],
        languages=["python", "typescript"],
    )
    write_mixed_fast_summary(
        repo,
        "baseline",
        py_status="failed",
        py_exit_code=1,
        ts_status="passed",
        ts_exit_code=0,
    )
    write_mixed_fast_summary(
        repo,
        "candidate",
        py_status="passed",
        py_exit_code=0,
        ts_status="failed",
        ts_exit_code=1,
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_result_mixed_candidate_run",
            "run": {
                "executor_result": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "bridge_id": "bridge-session",
                    "result_path": "external-result.json",
                    "session_id": "session-one",
                }
            },
            "expect_executor_result": {
                "result_status": "completed",
                "session_id": "session-one",
                "session_state": "completed",
                "verification_hint": "candidate_run",
                "verification_triggered": True,
                "verification_verdict": "mixed",
                "next_recommendation": "inspect regressions",
                "verify_summary_path": ".qa-z/sessions/session-one/verify/summary.json",
                "schema_version": 1,
            },
            "expect_verify": {
                "verdict": "mixed",
                "blocking_before": 1,
                "blocking_after": 1,
                "resolved_count": 1,
                "regression_count": 1,
                "new_issue_count": 1,
                "schema_version": 1,
            },
        },
    )
    write_expected(
        repo / "external-result.json",
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-session",
            "source_session_id": "session-one",
            "source_loop_id": None,
            "created_at": "2026-04-16T00:00:00Z",
            "status": "completed",
            "summary": "Resolved the Python failure, but the TypeScript typecheck regressed.",
            "verification_hint": "candidate_run",
            "candidate_run_dir": ".qa-z/runs/candidate",
            "changed_files": [
                {
                    "path": "src/app.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Adjusted Python logic during repair.",
                },
                {
                    "path": "src/invoice.ts",
                    "status": "modified",
                    "old_path": None,
                    "summary": "TypeScript edits introduced a new failure.",
                },
            ],
            "validation": {
                "status": "failed",
                "commands": [["python", "-m", "pytest"], ["tsc", "--noEmit"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "passed",
                        "exit_code": 0,
                        "summary": "pytest passed locally",
                    },
                    {
                        "command": ["tsc", "--noEmit"],
                        "status": "failed",
                        "exit_code": 1,
                        "summary": "ts_type still fails",
                    },
                ],
            },
            "notes": ["candidate run should attach mixed verification evidence"],
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_result"]["result_status"] == "completed"
    assert (
        fixture_result["actual"]["executor_result"]["verification_verdict"] == "mixed"
    )
    assert fixture_result["actual"]["verify"]["verdict"] == "mixed"
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


def test_run_benchmark_executes_executor_result_partial_fixture_with_realism_fields(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "executor_result_partial_mixed_verify_candidate"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "app.py").write_text("def answer():\n    return 42\n")
    repo.joinpath("src", "invoice.ts").write_text(
        "export const total: number = 1;\n", encoding="utf-8"
    )
    write_contract(
        repo,
        related_files=["src/app.py", "src/invoice.ts"],
        title="Executor result partial mixed verify fixture",
    )
    write_config(
        repo,
        [{"id": "py_test", "kind": "test", "run": [sys.executable, "-c", ""]}],
        languages=["python", "typescript"],
    )
    write_mixed_fast_summary(
        repo,
        "baseline",
        py_status="failed",
        py_exit_code=1,
        ts_status="passed",
        ts_exit_code=0,
    )
    write_mixed_fast_summary(
        repo,
        "candidate",
        py_status="passed",
        py_exit_code=0,
        ts_status="failed",
        ts_exit_code=1,
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_result_partial_mixed_verify_candidate",
            "run": {
                "verify": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "candidate_run": ".qa-z/runs/candidate",
                },
                "executor_result": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "bridge_id": "bridge-partial",
                    "result_path": "external-result.json",
                    "session_id": "session-partial",
                },
            },
            "expect_executor_result": {
                "result_status": "partial",
                "expected_ingest_status": "accepted_partial",
                "session_id": "session-partial",
                "session_state": "candidate_generated",
                "verification_hint": "candidate_run",
                "verification_triggered": False,
                "expected_recommendation": "continue repair",
                "backlog_categories": ["partial_completion_gap"],
                "warning_ids_absent": ["no_op_without_explanation"],
                "schema_version": 1,
            },
            "expect_verify": {
                "verdict": "mixed",
                "blocking_before": 1,
                "blocking_after": 1,
                "resolved_count": 1,
                "regression_count": 1,
                "new_issue_count": 1,
                "schema_version": 1,
            },
        },
    )
    write_expected(
        repo / "external-result.json",
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-partial",
            "source_session_id": "session-partial",
            "source_loop_id": None,
            "created_at": "2026-04-16T00:00:00Z",
            "status": "partial",
            "summary": "Resolved the Python issue, but the TypeScript regression still needs follow-up.",
            "verification_hint": "candidate_run",
            "candidate_run_dir": ".qa-z/runs/candidate",
            "changed_files": [
                {
                    "path": "src/app.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Adjusted Python logic.",
                },
                {
                    "path": "src/invoice.ts",
                    "status": "modified",
                    "old_path": None,
                    "summary": "TypeScript still needs another pass.",
                },
            ],
            "validation": {
                "status": "failed",
                "commands": [["python", "-m", "pytest"], ["tsc", "--noEmit"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "passed",
                        "exit_code": 0,
                        "summary": "pytest passed locally",
                    },
                    {
                        "command": ["tsc", "--noEmit"],
                        "status": "failed",
                        "exit_code": 1,
                        "summary": "ts_type still fails",
                    },
                ],
            },
            "notes": ["needs another repair loop"],
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_result"]["ingest_status"] == (
        "accepted_partial"
    )
    assert fixture_result["actual"]["executor_result"]["backlog_categories"] == [
        "partial_completion_gap"
    ]
    assert fixture_result["actual"]["verify"]["verdict"] == "mixed"


def test_run_benchmark_executes_executor_result_future_timestamp_rejection_fixture(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "executor_result_future_timestamp_rejected"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "app.py").write_text("def answer():\n    return 42\n")
    write_contract(
        repo,
        related_files=["src/app.py"],
        title="Executor result future timestamp rejection fixture",
    )
    write_config(
        repo,
        [{"id": "py_test", "kind": "test", "run": [sys.executable, "-c", ""]}],
    )
    write_fast_summary(
        repo, "baseline", check_id="py_test", status="failed", exit_code=1
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_result_future_timestamp_rejected",
            "run": {
                "executor_result": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "bridge_id": "bridge-future",
                    "result_path": "external-result.json",
                    "session_id": "session-future",
                }
            },
            "expect_executor_result": {
                "result_status": "completed",
                "expected_ingest_status": "rejected_invalid",
                "session_id": "session-future",
                "verification_hint": "rerun",
                "verification_triggered": False,
                "verify_resume_status": "verify_blocked",
                "expected_recommendation": "fix executor result timestamps",
                "freshness_reason": "result_from_future",
                "backlog_categories": ["evidence_freshness_gap"],
                "schema_version": 1,
            },
        },
    )
    write_expected(
        repo / "external-result.json",
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-future",
            "source_session_id": "session-future",
            "source_loop_id": None,
            "created_at": "2026-04-16T00:10:00Z",
            "status": "completed",
            "summary": "Claims completion from a timestamp after benchmark ingest begins.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/app.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Adjusted Python logic.",
                }
            ],
            "validation": {"status": "passed", "commands": [], "results": []},
            "notes": ["should be rejected as future-dated evidence"],
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_result"]["ingest_status"] == (
        "rejected_invalid"
    )
    assert fixture_result["actual"]["executor_result"]["freshness_reason"] == (
        "result_from_future"
    )


def test_run_benchmark_executes_executor_result_validation_conflict_fixture(
    tmp_path: Path,
) -> None:
    fixture = tmp_path / "fixtures" / "executor_result_validation_conflict_blocked"
    repo = fixture / "repo"
    repo.joinpath("src").mkdir(parents=True)
    repo.joinpath("src", "app.py").write_text("def answer():\n    return 42\n")
    write_contract(
        repo,
        related_files=["src/app.py"],
        title="Executor result validation conflict fixture",
    )
    write_config(
        repo,
        [{"id": "py_test", "kind": "test", "run": [sys.executable, "-c", ""]}],
    )
    write_fast_summary(
        repo, "baseline", check_id="py_test", status="failed", exit_code=1
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_result_validation_conflict_blocked",
            "run": {
                "executor_result": {
                    "baseline_run": ".qa-z/runs/baseline",
                    "bridge_id": "bridge-validation",
                    "result_path": "external-result.json",
                    "session_id": "session-validation",
                }
            },
            "expect_executor_result": {
                "result_status": "completed",
                "expected_ingest_status": "accepted_with_warning",
                "session_id": "session-validation",
                "session_state": "candidate_generated",
                "verification_hint": "rerun",
                "verification_triggered": False,
                "verify_resume_status": "verify_blocked",
                "expected_recommendation": "inspect executor result warnings",
                "warning_ids_present": ["validation_summary_conflicts_with_results"],
                "backlog_categories": ["workflow_gap"],
                "schema_version": 1,
            },
        },
    )
    write_expected(
        repo / "external-result.json",
        {
            "kind": "qa_z.executor_result",
            "schema_version": 1,
            "bridge_id": "bridge-validation",
            "source_session_id": "session-validation",
            "source_loop_id": None,
            "created_at": "2026-04-16T00:00:00Z",
            "status": "completed",
            "summary": "Claims a passing summary while the detailed validation still fails.",
            "verification_hint": "rerun",
            "candidate_run_dir": None,
            "changed_files": [
                {
                    "path": "src/app.py",
                    "status": "modified",
                    "old_path": None,
                    "summary": "Adjusted Python logic.",
                }
            ],
            "validation": {
                "status": "passed",
                "commands": [["python", "-m", "pytest"]],
                "results": [
                    {
                        "command": ["python", "-m", "pytest"],
                        "status": "failed",
                        "exit_code": 1,
                        "summary": "pytest still fails",
                    }
                ],
            },
            "notes": ["validation evidence should block optimistic verify resume"],
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_total"] == 1
    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_result"]["verify_resume_status"] == (
        "verify_blocked"
    )
    assert (
        "validation_summary_conflicts_with_results"
        in fixture_result["actual"]["executor_result"]["warning_ids"]
    )


def test_typescript_benchmark_results_are_counted_in_summary() -> None:
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="ts_lint_failure",
                passed=True,
                failures=[],
                categories={
                    "detection": True,
                    "handoff": True,
                    "verify": None,
                    "artifact": None,
                },
                actual={},
                artifacts={},
            ),
            BenchmarkFixtureResult(
                name="ts_unchanged_candidate",
                passed=True,
                failures=[],
                categories={
                    "detection": None,
                    "handoff": None,
                    "verify": True,
                    "artifact": None,
                },
                actual={},
                artifacts={},
            ),
        ]
    )

    assert summary["fixtures_total"] == 2
    assert summary["category_rates"]["detection"] == {
        "passed": 1,
        "total": 1,
        "rate": 1.0,
    }
    assert summary["category_rates"]["handoff"] == {
        "passed": 1,
        "total": 1,
        "rate": 1.0,
    }
    assert summary["category_rates"]["verify"] == {
        "passed": 1,
        "total": 1,
        "rate": 1.0,
    }


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


def test_run_benchmark_executes_executor_dry_run_fixture(tmp_path: Path) -> None:
    fixture = tmp_path / "fixtures" / "executor_dry_run_repeated_partial_attention"
    repo = fixture / "repo"
    write_contract(
        repo, related_files=["src/app.py"], title="Dry-run benchmark fixture"
    )
    repo.joinpath("src").mkdir(parents=True, exist_ok=True)
    repo.joinpath("src", "app.py").write_text(
        "def answer() -> int:\n    return 42\n", encoding="utf-8"
    )
    write_config(repo, [])
    write_json(
        repo / ".qa-z" / "sessions" / "session-one" / "session.json",
        {
            "kind": "qa_z.repair_session",
            "schema_version": 1,
            "session_id": "session-one",
            "session_dir": ".qa-z/sessions/session-one",
            "baseline_run_dir": ".qa-z/runs/baseline",
            "baseline_fast_summary_path": ".qa-z/runs/baseline/fast/summary.json",
            "baseline_deep_summary_path": None,
            "handoff_dir": ".qa-z/sessions/session-one/handoff",
            "handoff_artifacts": {},
            "executor_guide_path": ".qa-z/sessions/session-one/executor_guide.md",
            "candidate_run_dir": None,
            "verify_dir": None,
            "verify_artifacts": {},
            "outcome_path": None,
            "summary_path": None,
            "provenance": {"repair_needed": True},
            "safety_artifacts": {},
            "executor_result_path": None,
            "executor_result_status": None,
            "executor_result_validation_status": None,
            "executor_result_bridge_id": None,
            "state": "waiting_for_external_repair",
            "created_at": "2026-04-16T00:00:00Z",
            "updated_at": "2026-04-16T00:00:00Z",
        },
    )
    write_json(
        repo
        / ".qa-z"
        / "sessions"
        / "session-one"
        / "executor_results"
        / "history.json",
        {
            "kind": "qa_z.executor_result_history",
            "schema_version": 1,
            "session_id": "session-one",
            "updated_at": "2026-04-16T00:00:00Z",
            "attempt_count": 2,
            "latest_attempt_id": "attempt-2",
            "attempts": [
                {
                    "attempt_id": "attempt-1",
                    "recorded_at": "2026-04-16T00:00:00Z",
                    "bridge_id": "bridge-one",
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
                    "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-1.json",
                    "ingest_artifact_path": ".qa-z/executor-results/attempt-1/ingest.json",
                    "ingest_report_path": ".qa-z/executor-results/attempt-1/ingest_report.md",
                    "freshness_status": "passed",
                    "freshness_reason": None,
                    "provenance_status": "passed",
                    "provenance_reason": None,
                },
                {
                    "attempt_id": "attempt-2",
                    "recorded_at": "2026-04-16T00:05:00Z",
                    "bridge_id": "bridge-one",
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
                    "attempt_path": ".qa-z/sessions/session-one/executor_results/attempts/attempt-2.json",
                    "ingest_artifact_path": ".qa-z/executor-results/attempt-2/ingest.json",
                    "ingest_report_path": ".qa-z/executor-results/attempt-2/ingest_report.md",
                    "freshness_status": "passed",
                    "freshness_reason": None,
                    "provenance_status": "passed",
                    "provenance_reason": None,
                },
            ],
        },
    )
    write_expected(
        fixture / "expected.json",
        {
            "name": "executor_dry_run_repeated_partial_attention",
            "run": {
                "executor_result_dry_run": {
                    "session_id": "session-one",
                }
            },
            "expect_executor_dry_run": {
                "verdict": "attention_required",
                "verdict_reason": "manual_retry_review_required",
                "evaluated_attempt_count": 2,
                "latest_result_status": "partial",
                "history_signals": ["repeated_partial_attempts"],
                "attention_rule_ids": ["retry_boundary_is_manual"],
                "attention_rule_count": 1,
                "clear_rule_count": 6,
                "blocked_rule_count": 0,
                "expected_recommendation": "inspect repeated partial attempts before another retry",
                "schema_version": 1,
            },
        },
    )

    summary = run_benchmark(
        fixtures_dir=tmp_path / "fixtures",
        results_dir=tmp_path / "results",
    )

    assert summary["fixtures_passed"] == 1
    fixture_result = summary["fixtures"][0]
    assert fixture_result["actual"]["executor_dry_run"]["verdict"] == (
        "attention_required"
    )
    assert (
        fixture_result["actual"]["executor_dry_run"]["verdict_reason"]
        == "manual_retry_review_required"
    )
    assert fixture_result["actual"]["executor_dry_run"]["history_signals"] == [
        "repeated_partial_attempts"
    ]
    assert fixture_result["actual"]["executor_dry_run"]["attention_rule_count"] == 1
    assert fixture_result["categories"]["policy"] is True


def test_committed_benchmark_corpus_has_initial_high_signal_set() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    names = {fixture.name for fixture in fixtures}

    assert len(names) >= 8
    assert {
        "py_type_error",
        "py_test_failure",
        "py_lint_failure",
        "semgrep_eval",
        "semgrep_shell_true",
        "semgrep_hardcoded_secret",
        "fast_and_deep_blocking",
        "unchanged_candidate",
        "improved_candidate",
        "regressed_candidate",
    } <= names


def test_committed_benchmark_corpus_has_typescript_fast_fixture_set() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    by_name = {fixture.name: fixture for fixture in fixtures}

    assert {
        "ts_lint_failure",
        "ts_type_error",
        "ts_test_failure",
        "ts_multiple_fast_failures",
        "ts_unchanged_candidate",
        "ts_regressed_candidate",
    } <= set(by_name)

    assert by_name["ts_lint_failure"].expectation.expect_fast[
        "blocking_failed_checks"
    ] == ["ts_lint"]
    assert by_name["ts_type_error"].expectation.expect_handoff[
        "validation_command_ids"
    ] == ["check:ts_type", "qa-z-fast"]
    assert (
        by_name["ts_unchanged_candidate"].expectation.expect_verify["verdict"]
        == "unchanged"
    )
    assert (
        by_name["ts_regressed_candidate"].expectation.expect_verify["verdict"]
        == "regressed"
    )


def test_committed_benchmark_corpus_has_deep_policy_fixture_set() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    by_name = {fixture.name: fixture for fixture in fixtures}

    assert {
        "deep_severity_threshold_warn_filtered",
        "deep_ignore_rule_suppressed",
        "deep_exclude_paths_skipped",
        "deep_grouped_findings_dedup",
        "deep_filtered_vs_blocking_counts",
        "deep_config_error_surface",
    } <= set(by_name)

    assert (
        by_name["deep_severity_threshold_warn_filtered"].expectation.expect_deep[
            "filtered_findings_count_min"
        ]
        == 1
    )
    assert by_name["deep_ignore_rule_suppressed"].expectation.expect_deep[
        "rule_ids_absent"
    ] == ["generic.secrets.security.detected-private-key"]
    assert by_name["deep_exclude_paths_skipped"].expectation.expect_deep[
        "filter_reasons"
    ] == {"excluded_path": 1}
    assert (
        by_name["deep_grouped_findings_dedup"].expectation.expect_deep[
            "grouped_findings_count"
        ]
        == 1
    )
    assert (
        by_name["deep_filtered_vs_blocking_counts"].expectation.expect_deep[
            "blocking_findings_count"
        ]
        == 1
    )
    assert (
        by_name["deep_config_error_surface"].expectation.expect_deep[
            "expect_config_error"
        ]
        is True
    )


def test_committed_benchmark_corpus_has_mixed_language_verification_fixture_set() -> (
    None
):
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    by_name = {fixture.name: fixture for fixture in fixtures}

    assert {
        "mixed_py_resolved_ts_regressed_candidate",
        "mixed_ts_resolved_py_regressed_candidate",
        "mixed_all_resolved_candidate",
        "mixed_partial_resolved_with_regression_candidate",
    } <= set(by_name)

    assert (
        by_name["mixed_py_resolved_ts_regressed_candidate"].expectation.expect_verify[
            "verdict"
        ]
        == "mixed"
    )
    assert (
        by_name["mixed_ts_resolved_py_regressed_candidate"].expectation.expect_verify[
            "verdict"
        ]
        == "mixed"
    )
    assert (
        by_name["mixed_all_resolved_candidate"].expectation.expect_verify["verdict"]
        == "improved"
    )
    assert (
        by_name[
            "mixed_partial_resolved_with_regression_candidate"
        ].expectation.expect_verify["blocking_before"]
        == 2
    )
    assert (
        by_name[
            "mixed_partial_resolved_with_regression_candidate"
        ].expectation.expect_verify["blocking_after"]
        == 2
    )


def test_committed_benchmark_corpus_has_mixed_surface_realism_fixture_set() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    by_name = {fixture.name: fixture for fixture in fixtures}

    assert {
        "mixed_fast_handoff_functional_worktree_cleanup",
        "mixed_fast_deep_handoff_dual_surface",
        "mixed_fast_deep_handoff_ts_lint_python_deep",
        "mixed_fast_deep_handoff_py_lint_ts_test_dual_deep",
        "mixed_docs_schema_sync_maintenance_candidate",
        "executor_result_partial_mixed_verify_candidate",
        "executor_result_no_op_with_justification_candidate",
        "mixed_cleanup_only_worktree_risk_candidate",
        "executor_result_future_timestamp_rejected",
        "executor_result_validation_conflict_blocked",
    } <= set(by_name)

    assert by_name["mixed_fast_handoff_functional_worktree_cleanup"].expectation.run[
        "repair_handoff"
    ]
    mixed_fast_deep = by_name["mixed_fast_deep_handoff_dual_surface"].expectation
    assert mixed_fast_deep.run == {
        "fast": True,
        "deep": True,
        "repair_handoff": True,
    }
    assert mixed_fast_deep.expect_fast["blocking_failed_checks"] == [
        "py_test",
        "ts_type",
    ]
    assert mixed_fast_deep.expect_deep["blocking_findings_min"] == 2
    assert mixed_fast_deep.expect_handoff["target_sources"] == [
        "fast_check",
        "deep_finding",
    ]
    assert "src/invoice.ts" in mixed_fast_deep.expect_handoff["affected_files"]
    mixed_fast_deep_ts_lint = by_name[
        "mixed_fast_deep_handoff_ts_lint_python_deep"
    ].expectation
    assert mixed_fast_deep_ts_lint.run == {
        "fast": True,
        "deep": True,
        "repair_handoff": True,
    }
    assert mixed_fast_deep_ts_lint.expect_fast["blocking_failed_checks"] == ["ts_lint"]
    assert mixed_fast_deep_ts_lint.expect_deep["rule_ids_present"] == [
        "python.lang.security.audit.eval"
    ]
    assert mixed_fast_deep_ts_lint.expect_handoff["target_sources"] == [
        "fast_check",
        "deep_finding",
    ]
    assert "src/app.py" in mixed_fast_deep_ts_lint.expect_handoff["affected_files"]
    assert "src/invoice.ts" in mixed_fast_deep_ts_lint.expect_handoff["affected_files"]
    mixed_fast_deep_py_lint_ts_test = by_name[
        "mixed_fast_deep_handoff_py_lint_ts_test_dual_deep"
    ].expectation
    assert mixed_fast_deep_py_lint_ts_test.run == {
        "fast": True,
        "deep": True,
        "repair_handoff": True,
    }
    assert mixed_fast_deep_py_lint_ts_test.expect_fast["blocking_failed_checks"] == [
        "py_lint",
        "ts_test",
    ]
    assert mixed_fast_deep_py_lint_ts_test.expect_deep["blocking_findings_min"] == 2
    assert mixed_fast_deep_py_lint_ts_test.expect_deep["rule_ids_present"] == [
        "python.lang.security.audit.eval",
        "generic.secrets.security.detected-password",
    ]
    assert mixed_fast_deep_py_lint_ts_test.expect_handoff["target_sources"] == [
        "fast_check",
        "deep_finding",
    ]
    assert (
        "src/app.py" in mixed_fast_deep_py_lint_ts_test.expect_handoff["affected_files"]
    )
    assert (
        "src/invoice.ts"
        in mixed_fast_deep_py_lint_ts_test.expect_handoff["affected_files"]
    )
    assert (
        "tests/invoice.test.ts"
        in mixed_fast_deep_py_lint_ts_test.expect_handoff["affected_files"]
    )
    assert (
        by_name[
            "mixed_docs_schema_sync_maintenance_candidate"
        ].expectation.expect_verify["verdict"]
        == "unchanged"
    )
    assert (
        by_name[
            "executor_result_partial_mixed_verify_candidate"
        ].expectation.expect_executor_result["expected_ingest_status"]
        == "accepted_partial"
    )
    assert (
        by_name[
            "executor_result_no_op_with_justification_candidate"
        ].expectation.expect_executor_result["expected_ingest_status"]
        == "accepted_no_op"
    )
    assert (
        by_name["mixed_cleanup_only_worktree_risk_candidate"].expectation.expect_verify[
            "remaining_issue_count_min"
        ]
        == 1
    )
    assert (
        by_name[
            "executor_result_future_timestamp_rejected"
        ].expectation.expect_executor_result["freshness_reason"]
        == "result_from_future"
    )
    assert by_name[
        "executor_result_validation_conflict_blocked"
    ].expectation.expect_executor_result["warning_ids_present"] == [
        "validation_summary_conflicts_with_results"
    ]


def test_committed_benchmark_corpus_has_executor_result_fixture_set() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    by_name = {fixture.name: fixture for fixture in fixtures}

    assert "executor_result_mixed_candidate_run" in by_name
    assert (
        by_name[
            "executor_result_mixed_candidate_run"
        ].expectation.expect_executor_result["verification_verdict"]
        == "mixed"
    )


def test_committed_benchmark_corpus_has_executor_bridge_action_context_fixture() -> (
    None
):
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    by_name = {fixture.name: fixture for fixture in fixtures}

    assert "executor_bridge_action_context_inputs" in by_name
    assert "executor_bridge_missing_action_context_inputs" in by_name
    expectation = by_name["executor_bridge_action_context_inputs"].expectation
    missing_expectation = by_name[
        "executor_bridge_missing_action_context_inputs"
    ].expectation

    assert expectation.run["executor_bridge"]["bridge_id"] == "bridge-context"
    assert expectation.expect_executor_bridge["action_context_count"] == 1
    assert expectation.expect_executor_bridge["action_context_paths"] == [
        ".qa-z/runs/candidate/verify/summary.json"
    ]
    assert (
        missing_expectation.expect_executor_bridge["action_context_missing_count"] == 1
    )
    assert (
        missing_expectation.expect_executor_bridge[
            "guide_mentions_missing_action_context"
        ]
        is True
    )
    assert expectation.expect_executor_bridge["stdout_mentions_action_context"] is True
    assert (
        missing_expectation.expect_executor_bridge["stdout_mentions_action_context"]
        is True
    )
    assert (
        missing_expectation.expect_executor_bridge[
            "stdout_mentions_missing_action_context"
        ]
        is True
    )


def test_committed_benchmark_corpus_has_executor_dry_run_fixture_set() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    by_name = {fixture.name: fixture for fixture in fixtures}

    assert {
        "executor_dry_run_clear_verified_completed",
        "executor_dry_run_repeated_partial_attention",
        "executor_dry_run_completed_verify_blocked",
        "executor_dry_run_validation_noop_operator_actions",
        "executor_dry_run_repeated_rejected_operator_actions",
        "executor_dry_run_repeated_noop_operator_actions",
        "executor_dry_run_blocked_mixed_history_operator_actions",
        "executor_dry_run_empty_history_operator_actions",
        "executor_dry_run_scope_validation_operator_actions",
        "executor_dry_run_missing_noop_explanation_operator_actions",
        "executor_dry_run_mixed_attention_operator_actions",
    } <= set(by_name)

    assert (
        by_name[
            "executor_dry_run_clear_verified_completed"
        ].expectation.expect_executor_dry_run["verdict"]
        == "clear"
    )
    assert (
        by_name[
            "executor_dry_run_clear_verified_completed"
        ].expectation.expect_executor_dry_run["verdict_reason"]
        == "history_clear"
    )
    assert (
        by_name[
            "executor_dry_run_clear_verified_completed"
        ].expectation.expect_executor_dry_run["expected_source"]
        == "materialized"
    )
    assert by_name[
        "executor_dry_run_repeated_partial_attention"
    ].expectation.expect_executor_dry_run["history_signals"] == [
        "repeated_partial_attempts"
    ]
    assert (
        by_name[
            "executor_dry_run_repeated_partial_attention"
        ].expectation.expect_executor_dry_run["attention_rule_count"]
        == 1
    )
    assert by_name[
        "executor_dry_run_completed_verify_blocked"
    ].expectation.expect_executor_dry_run["blocked_rule_ids"] == [
        "verification_required_for_completed"
    ]
    assert (
        by_name[
            "executor_dry_run_repeated_partial_attention"
        ].expectation.expect_executor_dry_run["expected_source"]
        == "materialized"
    )
    assert (
        by_name[
            "executor_dry_run_completed_verify_blocked"
        ].expectation.expect_executor_dry_run["verdict_reason"]
        == "completed_attempt_not_verification_clean"
    )
    assert (
        by_name[
            "executor_dry_run_completed_verify_blocked"
        ].expectation.expect_executor_dry_run["expected_source"]
        == "materialized"
    )
    assert by_name[
        "executor_dry_run_validation_noop_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "review_validation_conflict",
        "require_no_op_explanation",
    ]
    assert by_name[
        "executor_dry_run_validation_noop_operator_actions"
    ].expectation.expect_executor_dry_run["expected_recommendation"] == (
        "review executor validation conflict before another retry"
    )
    assert by_name[
        "executor_dry_run_repeated_rejected_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "inspect_rejected_results"
    ]
    assert by_name[
        "executor_dry_run_repeated_noop_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "inspect_no_op_pattern"
    ]
    assert by_name[
        "executor_dry_run_repeated_noop_operator_actions"
    ].expectation.expect_executor_dry_run["attention_rule_ids"] == [
        "retry_boundary_is_manual"
    ]
    assert by_name[
        "executor_dry_run_repeated_noop_operator_actions"
    ].expectation.expect_executor_dry_run["expected_recommendation"] == (
        "inspect repeated no-op outcomes before another retry"
    )
    assert by_name[
        "executor_dry_run_missing_noop_explanation_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "require_no_op_explanation"
    ]
    assert by_name[
        "executor_dry_run_blocked_mixed_history_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "resolve_verification_blockers",
        "review_validation_conflict",
        "inspect_partial_attempts",
    ]
    assert by_name[
        "executor_dry_run_empty_history_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "ingest_executor_result"
    ]
    assert by_name[
        "executor_dry_run_empty_history_operator_actions"
    ].expectation.expect_executor_dry_run["attention_rule_ids"] == [
        "executor_history_recorded"
    ]
    assert by_name[
        "executor_dry_run_scope_validation_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "inspect_scope_drift"
    ]
    assert by_name[
        "executor_dry_run_mixed_attention_operator_actions"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "review_validation_conflict",
        "require_no_op_explanation",
        "inspect_no_op_pattern",
    ]
    assert by_name[
        "executor_dry_run_mixed_attention_operator_actions"
    ].expectation.expect_executor_dry_run["operator_summary"] == (
        "Executor history has validation conflicts, no-op explanation gaps, and "
        "retry pressure; review all recommended actions before another retry."
    )


def test_committed_executor_dry_run_fixtures_pin_operator_action_residue() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    dry_run_fixtures = [
        fixture for fixture in fixtures if fixture.name.startswith("executor_dry_run_")
    ]

    assert dry_run_fixtures

    missing: list[str] = []
    for fixture in dry_run_fixtures:
        expected = fixture.expectation.expect_executor_dry_run
        for key in (
            "operator_decision",
            "operator_summary",
            "recommended_action_ids",
            "recommended_action_summaries",
        ):
            if not expected.get(key):
                missing.append(f"{fixture.name}:{key}")

    assert missing == []


def test_committed_executor_dry_run_fixtures_pin_complete_rule_buckets() -> None:
    fixtures = discover_fixtures(Path("benchmarks") / "fixtures")
    dry_run_fixtures = [
        fixture for fixture in fixtures if fixture.name.startswith("executor_dry_run_")
    ]

    assert dry_run_fixtures

    expected_rule_ids = set(DRY_RUN_RULE_IDS)
    required_buckets = {
        "clear_rule_ids": "clear_rule_count",
        "attention_rule_ids": "attention_rule_count",
        "blocked_rule_ids": "blocked_rule_count",
    }

    missing: list[str] = []
    mismatched_counts: list[str] = []
    duplicate_ids: list[str] = []
    mismatched_rule_sets: list[str] = []

    for fixture in dry_run_fixtures:
        expected = fixture.expectation.expect_executor_dry_run
        observed_rule_ids: set[str] = set()
        for bucket_key, count_key in required_buckets.items():
            if bucket_key not in expected:
                missing.append(f"{fixture.name}:{bucket_key}")
                continue
            bucket = expected[bucket_key]
            if len(bucket) != len(set(bucket)):
                duplicate_ids.append(f"{fixture.name}:{bucket_key}")
            if len(bucket) != expected[count_key]:
                mismatched_counts.append(
                    f"{fixture.name}:{bucket_key}:{len(bucket)}!={expected[count_key]}"
                )
            observed_rule_ids.update(bucket)
        if observed_rule_ids != expected_rule_ids:
            mismatched_rule_sets.append(f"{fixture.name}:{sorted(observed_rule_ids)}")

    assert missing == []
    assert duplicate_ids == []
    assert mismatched_counts == []
    assert mismatched_rule_sets == []
