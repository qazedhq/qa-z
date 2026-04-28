from __future__ import annotations

from types import SimpleNamespace
from typing import cast

import qa_z.verification_summary_counts as counts_module


def test_count_blocking_checks_counts_failed_and_error_statuses() -> None:
    summary = SimpleNamespace(
        checks=[
            SimpleNamespace(status="passed"),
            SimpleNamespace(status="failed"),
            SimpleNamespace(status="error"),
            SimpleNamespace(status="skipped"),
        ]
    )

    assert (
        counts_module.count_blocking_checks(cast(counts_module.RunSummary, summary))
        == 2
    )


def test_count_deep_findings_prefers_extracted_findings_before_raw_counts(
    monkeypatch,
) -> None:
    summary = SimpleNamespace(
        checks=[SimpleNamespace(findings_count=4)],
    )
    monkeypatch.setattr(
        counts_module,
        "extract_deep_findings",
        lambda summary: [
            SimpleNamespace(blocking=True),
            SimpleNamespace(blocking=False),
        ],
    )

    typed_summary = cast(counts_module.RunSummary, summary)

    assert counts_module.count_blocking_deep_findings(typed_summary) == 1
    assert counts_module.count_deep_findings(typed_summary) == 2


def test_count_blocking_deep_findings_falls_back_to_summary_counts(monkeypatch) -> None:
    summary = SimpleNamespace(
        checks=[
            SimpleNamespace(findings_count=3, blocking_findings_count=2),
            SimpleNamespace(findings_count=1, blocking_findings_count=1),
        ]
    )
    monkeypatch.setattr(counts_module, "extract_deep_findings", lambda summary: [])

    assert (
        counts_module.count_blocking_deep_findings(
            cast(counts_module.RunSummary, summary)
        )
        == 3
    )
