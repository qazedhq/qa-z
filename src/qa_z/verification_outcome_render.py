"""Render helpers for verification outcomes."""

from __future__ import annotations

import json

from qa_z.verification_models import VerificationComparison


def comparison_json(comparison: VerificationComparison) -> str:
    return json.dumps(comparison.to_dict(), indent=2, sort_keys=True) + "\n"
