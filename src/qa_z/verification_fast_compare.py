"""Fast-check comparison helpers for verification."""

from __future__ import annotations

from qa_z.runners.models import CheckResult
from qa_z.verification_delta_models import FastCheckDelta, VerificationCategory
from qa_z.verification_summary_counts import is_blocking_check
from qa_z.verification_support import empty_categories, fast_delta_message

NON_BLOCKING_CHECK_STATUSES = {"passed", "warning"}
SKIPPED_CHECK_STATUSES = {"skipped", "unsupported"}


def compare_fast_checks(
    baseline_checks: list[CheckResult], candidate_checks: list[CheckResult]
) -> dict[VerificationCategory, list[FastCheckDelta]]:
    """Compare deterministic fast-check results."""
    categories = empty_categories(FastCheckDelta)
    baseline_by_id = {check.id: check for check in baseline_checks}
    candidate_by_id = {check.id: check for check in candidate_checks}
    check_ids = sorted(set(baseline_by_id) | set(candidate_by_id))

    for check_id in check_ids:
        baseline = baseline_by_id.get(check_id)
        candidate = candidate_by_id.get(check_id)
        classification = classify_fast_check(baseline, candidate)
        if classification is None:
            continue
        reference = candidate or baseline
        categories[classification].append(
            FastCheckDelta(
                id=check_id,
                classification=classification,
                baseline_status=baseline.status if baseline else None,
                candidate_status=candidate.status if candidate else None,
                baseline_exit_code=baseline.exit_code if baseline else None,
                candidate_exit_code=candidate.exit_code if candidate else None,
                kind=reference.kind if reference else None,
                message=fast_delta_message(classification, baseline, candidate),
            )
        )
    return categories


def classify_fast_check(
    baseline: CheckResult | None, candidate: CheckResult | None
) -> VerificationCategory | None:
    """Return the verification category for one fast check transition."""
    baseline_blocking = is_blocking_check(baseline)
    candidate_blocking = is_blocking_check(candidate)
    baseline_status = baseline.status if baseline else None
    candidate_status = candidate.status if candidate else None

    if baseline_blocking and candidate_status in NON_BLOCKING_CHECK_STATUSES:
        return "resolved"
    if baseline_blocking and candidate_blocking:
        return "still_failing"
    if baseline_status in NON_BLOCKING_CHECK_STATUSES and candidate_blocking:
        return "regressed"
    if baseline is None and candidate_blocking:
        return "newly_introduced"
    if baseline_blocking and (
        candidate is None or candidate_status in SKIPPED_CHECK_STATUSES
    ):
        return "skipped_or_not_comparable"
    if (
        baseline_status in SKIPPED_CHECK_STATUSES
        or candidate_status in SKIPPED_CHECK_STATUSES
    ):
        return "skipped_or_not_comparable"
    if baseline is None or candidate is None:
        return "skipped_or_not_comparable"
    return None
