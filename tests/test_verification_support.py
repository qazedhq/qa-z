"""Behavior tests for verification support helpers."""

from __future__ import annotations

from qa_z.runners.models import CheckResult
from qa_z.verification_support import (
    coerce_positive_int,
    fast_delta_message,
    first_nonempty,
    normalize_message,
    normalize_path,
)


def _check(status: str) -> CheckResult:
    return CheckResult(
        id="py_test",
        tool="pytest",
        command=["pytest"],
        kind="test",
        status=status,
        exit_code=1 if status == "failed" else 0,
        duration_ms=1,
    )


def test_fast_delta_message_describes_one_sided_checks() -> None:
    assert fast_delta_message("skipped_or_not_comparable", None, _check("failed")) == (
        "Check exists in only one run and cannot be compared directly."
    )


def test_normalizers_keep_paths_messages_and_positive_ints_stable() -> None:
    assert normalize_path("src\\qa_z\\verification.py ") == "src/qa_z/verification.py"
    assert normalize_message("  Mixed\tCase  message ") == "mixed case message"
    assert first_nonempty(None, " ", "value", "later") == "value"
    assert coerce_positive_int("7") == 7
    assert coerce_positive_int("0") is None
