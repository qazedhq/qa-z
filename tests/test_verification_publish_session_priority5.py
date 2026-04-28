"""Priority 5 publish-summary regressions for executor dry-run residue."""

from __future__ import annotations

from pathlib import Path

from qa_z.reporters.verification_publish import (
    load_session_publish_summary,
    render_publish_summary_markdown,
)
from tests.verification_publish_test_support import (
    write_session_manifest,
    write_session_summary,
    write_validation_rejected_history,
    write_verify_artifacts,
)


def test_session_publish_summary_preserves_validation_rejected_attention_actions(
    tmp_path: Path,
) -> None:
    session_id = "session-validation-rejected"
    verify_dir = tmp_path / ".qa-z" / "sessions" / session_id / "verify"
    write_verify_artifacts(
        tmp_path,
        verify_dir,
        verdict="unchanged",
        blocking_after=1,
        resolved_count=0,
        regression_count=0,
        new_issue_count=0,
    )
    write_validation_rejected_history(tmp_path, session_id)
    write_session_summary(
        tmp_path,
        session_id,
        verdict="unchanged",
        blocking_before=1,
        blocking_after=1,
        resolved_count=0,
        remaining_issue_count=1,
        new_issue_count=0,
        regression_count=0,
        next_recommendation="continue repair",
    )
    write_session_manifest(tmp_path, session_id)

    summary = load_session_publish_summary(root=tmp_path, session=session_id)
    markdown = render_publish_summary_markdown(summary)
    actions = summary.executor_dry_run_recommended_actions or []

    assert summary.executor_dry_run_history_signals == [
        "repeated_partial_attempts",
        "repeated_rejected_attempts",
        "validation_conflict",
    ]
    assert summary.executor_dry_run_operator_decision == "review_validation_conflict"
    assert summary.executor_dry_run_operator_summary == (
        "Executor history has validation conflicts and retry pressure; review both "
        "recommended actions before another retry."
    )
    assert [action["id"] for action in actions] == [
        "review_validation_conflict",
        "inspect_rejected_results",
        "inspect_partial_attempts",
    ]
    assert "Action `review_validation_conflict`" in markdown
    assert "Action `inspect_rejected_results`" in markdown
