"""Shared list and numeric comparison helpers for benchmark expectations."""

from __future__ import annotations

from qa_z.benchmark_helpers import coerce_number


def compare_absent_list(
    section: str, key: str, actual_value: object, expected_value: object
) -> list[str]:
    """Assert a list of values is absent from an actual list."""
    if not isinstance(expected_value, list):
        return [f"{section}.{key} expected an absence list but got {expected_value!r}"]
    if not isinstance(actual_value, list):
        return [f"{section}.{key} expected a list but got {actual_value!r}"]
    actual_set = {str(item) for item in actual_value}
    present = [str(item) for item in expected_value if str(item) in actual_set]
    if present:
        return [
            f"{section}.{key} expected values absent but found: "
            f"{', '.join(sorted(present))}"
        ]
    return []


def compare_expected_list(
    section: str, key: str, actual_value: object, expected_value: object
) -> list[str]:
    """Compare lists using expected-subset semantics."""
    if not isinstance(expected_value, list):
        return [f"{section}.{key} expected a list contract but got {expected_value!r}"]
    if not isinstance(actual_value, list):
        return [f"{section}.{key} expected a list but got {actual_value!r}"]
    actual_set = {str(item) for item in actual_value}
    missing = [str(item) for item in expected_value if str(item) not in actual_set]
    if missing:
        return [
            f"{section}.{key} missing expected values: {', '.join(sorted(missing))}"
        ]
    return []


def compare_minimum(
    section: str, key: str, actual_value: object, expected_value: object
) -> list[str]:
    """Compare a numeric minimum threshold."""
    actual_number = coerce_number(actual_value)
    expected_number = coerce_number(expected_value)
    if actual_number is None or expected_number is None:
        return [f"{section}.{key} expected numeric minimum comparison"]
    if actual_number < expected_number:
        return [
            f"{section}.{key} expected at least {expected_number:g} but got {actual_number:g}"
        ]
    return []


def compare_maximum(
    section: str, key: str, actual_value: object, expected_value: object
) -> list[str]:
    """Compare a numeric maximum threshold."""
    actual_number = coerce_number(actual_value)
    expected_number = coerce_number(expected_value)
    if actual_number is None or expected_number is None:
        return [f"{section}.{key} expected numeric maximum comparison"]
    if actual_number > expected_number:
        return [
            f"{section}.{key} expected at most {expected_number:g} but got {actual_number:g}"
        ]
    return []
