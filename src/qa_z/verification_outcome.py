"""Verification outcome helpers and public seams."""

from __future__ import annotations

from qa_z.verification_outcome_render import comparison_json
from qa_z.verification_outcome_summary import (
    recommendation_for_verdict,
    verification_summary_dict,
    verify_exit_code,
)

__all__ = [
    "comparison_json",
    "recommendation_for_verdict",
    "verification_summary_dict",
    "verify_exit_code",
]
