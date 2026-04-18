"""Structured change-set helpers for QA-Z."""

from qa_z.diffing.models import ChangedFile, ChangeSet
from qa_z.diffing.parser import parse_unified_diff

__all__ = ["ChangedFile", "ChangeSet", "parse_unified_diff"]
