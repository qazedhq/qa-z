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
)
from qa_z.cli import main
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
