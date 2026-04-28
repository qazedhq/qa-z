"""Expectation-key helpers for benchmark comparison and summary routing."""

from __future__ import annotations

from typing import Any


POLICY_EXPECTATION_KEYS = {
    "blocking_findings_count",
    "blocking_findings_min",
    "blocking_findings_count_min",
    "blocking_findings_count_max",
    "filtered_findings_count",
    "filtered_findings_count_min",
    "filtered_findings_count_max",
    "grouped_findings_count",
    "grouped_findings_count_min",
    "grouped_findings_count_max",
    "grouped_findings_min",
    "findings_count",
    "findings_count_min",
    "findings_count_max",
    "rule_ids_present",
    "rule_ids_absent",
    "scan_warning_count",
    "scan_warning_count_min",
    "scan_warning_count_max",
    "scan_warning_types_present",
    "scan_warning_types_absent",
    "scan_warning_paths_present",
    "scan_warning_paths_absent",
    "scan_quality_status",
    "scan_quality_warning_count",
    "scan_quality_warning_count_min",
    "scan_quality_warning_types_present",
    "scan_quality_warning_paths_present",
    "scan_quality_check_ids_present",
    "filter_reasons",
    "error_types",
    "config_error",
    "expect_config_error",
    "policy",
}


def expectation_actual_key(key: str) -> str:
    """Return the actual key for additive expectation names."""
    if key == "expect_config_error":
        return "config_error"
    if key == "expect_status":
        return "status"
    if key == "expected_source":
        return "summary_source"
    if key == "expected_recommendation":
        return "next_recommendation"
    if key == "expected_ingest_status":
        return "ingest_status"
    if key in {"grouped_findings_min", "grouped_findings_max"}:
        return "grouped_findings_count"
    if key.endswith("_present"):
        return key[: -len("_present")]
    if key.endswith("_absent"):
        return key[: -len("_absent")]
    if key.endswith("_min"):
        return key[: -len("_min")]
    if key.endswith("_max"):
        return key[: -len("_max")]
    return key


def has_policy_expectation(expect_deep: dict[str, Any]) -> bool:
    """Return whether deep expectations assert policy behavior."""
    return any(key in POLICY_EXPECTATION_KEYS for key in expect_deep)
