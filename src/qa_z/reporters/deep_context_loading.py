"""Thin public wrappers for deep-context loading seams."""

from __future__ import annotations

from typing import TYPE_CHECKING

from qa_z.artifacts import RunSource
from qa_z.runners.models import RunSummary

if TYPE_CHECKING:
    from qa_z.reporters.deep_context import DeepContext


def load_sibling_deep_summary(run_source: RunSource) -> RunSummary | None:
    """Load ``deep/summary.json`` beside a fast run when it exists."""
    from qa_z.reporters import deep_context as deep_context_module

    return deep_context_module._load_sibling_deep_summary_impl(run_source)


def build_deep_context(summary: RunSummary | None) -> DeepContext | None:
    """Build a compact deep context, returning ``None`` when no deep run exists."""
    from qa_z.reporters import deep_context as deep_context_module

    return deep_context_module._build_deep_context_impl(summary)
