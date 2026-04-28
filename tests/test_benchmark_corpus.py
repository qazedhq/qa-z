from __future__ import annotations

from pathlib import Path

from qa_z.benchmark import (
    BenchmarkExpectation,
    BenchmarkFixtureResult,
    build_benchmark_summary,
    categorize_result,
    discover_fixtures,
)
from qa_z.executor_dry_run_logic import DRY_RUN_RULE_IDS


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


def test_categorize_result_counts_executor_result_only_expectations() -> None:
    expectation = BenchmarkExpectation.from_dict(
        {
            "name": "executor_result_only",
            "expect_executor_result": {
                "expected_ingest_status": "accepted_partial",
            },
        }
    )

    categories = categorize_result([], expectation)

    assert categories["detection"] is None
    assert categories["handoff"] is None
    assert categories["verify"] is None
    assert categories["artifact"] is None
    assert categories["policy"] is None
    assert categories["executor_result"] is True


def test_build_benchmark_summary_counts_executor_result_category() -> None:
    results = [
        BenchmarkFixtureResult(
            name="executor_result_case",
            passed=True,
            failures=[],
            categories={
                "detection": None,
                "handoff": None,
                "verify": None,
                "artifact": None,
                "policy": None,
                "executor_result": True,
            },
            actual={"executor_result": {"ingest_status": "accepted_partial"}},
            artifacts={},
        )
    ]

    summary = build_benchmark_summary(results)

    assert summary["category_rates"]["executor_result"] == {
        "passed": 1,
        "total": 1,
        "rate": 1.0,
    }


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
        "deep_scan_warning_diagnostics",
        "deep_scan_warning_multi_source_diagnostics",
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
    assert (
        by_name["deep_scan_warning_diagnostics"].expectation.expect_deep[
            "scan_warning_count"
        ]
        == 1
    )
    assert by_name["deep_scan_warning_diagnostics"].expectation.expect_deep[
        "scan_warning_types_present"
    ] == ["Fixpoint timeout"]
    assert (
        by_name["deep_scan_warning_diagnostics"].expectation.expect_deep[
            "scan_quality_status"
        ]
        == "warning"
    )
    assert (
        by_name["deep_scan_warning_multi_source_diagnostics"].expectation.expect_deep[
            "scan_warning_count"
        ]
        == 2
    )
    assert by_name[
        "deep_scan_warning_multi_source_diagnostics"
    ].expectation.expect_deep["scan_warning_types_present"] == [
        "Fixpoint timeout",
        "Timeout",
    ]
    assert by_name[
        "deep_scan_warning_multi_source_diagnostics"
    ].expectation.expect_deep["scan_warning_paths_present"] == [
        "src/app.py",
        "src/worker.py",
    ]
    assert (
        by_name["deep_scan_warning_multi_source_diagnostics"].expectation.expect_deep[
            "scan_quality_warning_count"
        ]
        == 2
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
        "mixed_fast_deep_scan_warning_fast_only",
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
    mixed_fast_deep_warning = by_name[
        "mixed_fast_deep_scan_warning_fast_only"
    ].expectation
    assert mixed_fast_deep_warning.run == {
        "fast": True,
        "deep": True,
        "repair_handoff": True,
    }
    assert mixed_fast_deep_warning.expect_fast["blocking_failed_checks"] == ["ts_lint"]
    assert mixed_fast_deep_warning.expect_deep["status"] == "passed"
    assert mixed_fast_deep_warning.expect_deep["scan_warning_count"] == 2
    assert mixed_fast_deep_warning.expect_deep["scan_quality_status"] == "warning"
    assert mixed_fast_deep_warning.expect_deep["scan_quality_warning_count"] == 2
    assert mixed_fast_deep_warning.expect_handoff["target_sources"] == ["fast_check"]
    assert mixed_fast_deep_warning.expect_handoff["validation_command_ids"] == [
        "check:ts_lint",
        "qa-z-fast",
    ]
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
    partial_expectation = by_name[
        "executor_result_partial_mixed_verify_candidate"
    ].expectation.expect_executor_result
    assert (
        partial_expectation["live_repository_current_branch"] == "codex/qa-z-bootstrap"
    )
    assert (
        partial_expectation["live_repository_current_head"]
        == "1234567890abcdef1234567890abcdef12345678"
    )
    assert partial_expectation["source_context_fields_recorded"] is True
    assert partial_expectation["live_repository_context_recorded"] is True
    assert partial_expectation["check_statuses_recorded"] is True
    assert partial_expectation["backlog_implications_recorded"] is True
    assert "stdout_mentions_source_context" not in partial_expectation


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
    assert expectation.expect_executor_bridge["action_context_count"] == 2
    assert expectation.expect_executor_bridge["action_context_paths"] == [
        ".qa-z/loops/loop-bridge-context/self_inspect.json",
        ".qa-z/runs/candidate/verify/summary.json",
    ]
    assert (
        expectation.expect_executor_bridge["live_repository_current_branch"]
        == "codex/qa-z-bootstrap"
    )
    assert (
        expectation.expect_executor_bridge["live_repository_current_head"]
        == "1234567890abcdef1234567890abcdef12345678"
    )
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
        "executor_dry_run_completed_verify_blocked"
    ].expectation.expect_executor_dry_run["history_signals"] == [
        "completed_verify_blocked",
        "validation_conflict",
    ]
    assert by_name[
        "executor_dry_run_completed_verify_blocked"
    ].expectation.expect_executor_dry_run["recommended_action_ids"] == [
        "resolve_verification_blockers",
        "review_validation_conflict",
    ]
    assert by_name[
        "executor_dry_run_completed_verify_blocked"
    ].expectation.expect_executor_dry_run["operator_summary"] == (
        "A completed executor attempt is still blocked by verification evidence; "
        "validation conflicts still need review before another retry."
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
        "inspect_rejected_results",
        "inspect_partial_attempts",
    ]
    assert by_name[
        "executor_dry_run_repeated_rejected_operator_actions"
    ].expectation.expect_executor_dry_run["history_signals"] == [
        "repeated_partial_attempts",
        "repeated_rejected_attempts",
    ]
    assert by_name[
        "executor_dry_run_repeated_rejected_operator_actions"
    ].expectation.expect_executor_dry_run["expected_recommendation"] == (
        "inspect repeated rejected executor results before another retry"
    )
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
        "executor_dry_run_blocked_mixed_history_operator_actions"
    ].expectation.expect_executor_dry_run["operator_summary"] == (
        "A completed executor attempt is still blocked by verification evidence; "
        "validation conflicts and retry pressure still need review before another "
        "retry."
    )
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
