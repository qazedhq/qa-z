"""Expectation comparison helpers for benchmark fixtures."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from qa_z import benchmark_compare_support as compare_support
from qa_z import benchmark_expectation_keys as expectation_keys
from qa_z.benchmark_helpers import coerce_mapping

if TYPE_CHECKING:
    from qa_z.benchmark import BenchmarkExpectation


compare_absent_list = compare_support.compare_absent_list
compare_expected_list = compare_support.compare_expected_list
compare_maximum = compare_support.compare_maximum
compare_minimum = compare_support.compare_minimum
expectation_actual_key = expectation_keys.expectation_actual_key
has_policy_expectation = expectation_keys.has_policy_expectation

SECTION_EXPECTATION_FIELDS = (
    ("fast", "expect_fast"),
    ("deep", "expect_deep"),
    ("handoff", "expect_handoff"),
    ("verify", "expect_verify"),
    ("executor_bridge", "expect_executor_bridge"),
    ("executor_result", "expect_executor_result"),
    ("executor_dry_run", "expect_executor_dry_run"),
    ("artifact", "expect_artifacts"),
)


def compare_expected(
    actual: dict[str, Any], expectation: "BenchmarkExpectation"
) -> list[str]:
    """Compare actual benchmark observations against expected outcomes."""
    failures: list[str] = []
    for section, field_name in SECTION_EXPECTATION_FIELDS:
        failures.extend(
            compare_section(
                section,
                coerce_mapping(actual.get(section)),
                getattr(expectation, field_name),
            )
        )
    return failures


def compare_section(
    section: str, actual: dict[str, Any], expected: dict[str, Any]
) -> list[str]:
    """Compare one expected-results section with tolerant list matching."""
    if not expected:
        return []
    if not actual:
        return [f"{section} expected results but no actual section was produced"]

    failures: list[str] = []
    for key, expected_value in expected.items():
        actual_key = expectation_actual_key(key)
        if actual_key not in actual:
            failures.append(f"{section}.{actual_key} missing from actual results")
            continue
        actual_value = actual[actual_key]
        if key.endswith("_min"):
            failures.extend(
                compare_minimum(section, actual_key, actual_value, expected_value)
            )
        elif key.endswith("_max"):
            failures.extend(
                compare_maximum(section, actual_key, actual_value, expected_value)
            )
        elif key.endswith("_present"):
            failures.extend(
                compare_expected_list(section, actual_key, actual_value, expected_value)
            )
        elif key.endswith("_absent"):
            failures.extend(
                compare_absent_list(section, actual_key, actual_value, expected_value)
            )
        elif isinstance(expected_value, list):
            failures.extend(
                compare_expected_list(section, actual_key, actual_value, expected_value)
            )
        elif actual_value != expected_value:
            failures.append(
                f"{section}.{key} expected {expected_value!r} but got {actual_value!r}"
            )
    return failures
