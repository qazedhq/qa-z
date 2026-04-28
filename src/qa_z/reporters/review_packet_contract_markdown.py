"""Markdown parsing helpers for review packets."""

from __future__ import annotations

import re


def extract_section(document: str, heading: str) -> str:
    """Extract a markdown section body by H2 heading."""
    pattern = rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, document, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return match.group("body").strip()


def extract_subsection(document: str, heading: str) -> str:
    """Extract a markdown subsection body by H3 heading."""
    pattern = rf"^### {re.escape(heading)}\n(?P<body>.*?)(?=^### |^## |\Z)"
    match = re.search(pattern, document, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return match.group("body").strip()


def bulletize(text: str, fallback: str) -> str:
    """Normalize text blocks into bullet lists."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return f"- {fallback}"
    bullets = [line if line.startswith("- ") else f"- {line}" for line in lines]
    return "\n".join(bullets)


def extract_bullet_or_lines(section: str) -> list[str]:
    """Normalize a markdown section into a JSON list."""
    items = []
    for line in section.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(("- ", "* ")):
            stripped = stripped[2:].strip()
        items.append(stripped)
    return items
