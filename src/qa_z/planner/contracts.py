"""Contract drafting helpers for QA-Z."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from qa_z.config import get_nested


def slugify(value: str) -> str:
    """Create a filesystem-friendly slug from a title."""
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower())
    slug = normalized.strip("-")
    return slug or "qa-contract"


def format_section_list(items: Iterable[str], fallback: str) -> str:
    """Render bullet lines with a fallback sentence."""
    materialized = [item for item in items if item]
    if not materialized:
        return f"- {fallback}"
    return "\n".join(f"- {item}" for item in materialized)


def load_source_text(path: Path | None) -> str | None:
    """Read source text when a source file is provided."""
    if path is None:
        return None
    return path.read_text(encoding="utf-8").strip() or None


def excerpt_text(text: str | None, max_lines: int = 6) -> str:
    """Create a compact excerpt block for a context source."""
    if not text:
        return "_No source provided._"
    lines = [line.rstrip() for line in text.splitlines() if line.strip()]
    excerpt = lines[:max_lines]
    if len(lines) > max_lines:
        excerpt.append("...")
    return "\n".join(excerpt)


def infer_risk_edges(combined_text: str) -> list[str]:
    """Infer risk edges from title and source context."""
    lowered = combined_text.lower()
    inferred: list[str] = []

    if any(
        keyword in lowered
        for keyword in ("auth", "authorization", "permission", "login")
    ):
        inferred.append(
            "Authentication and authorization paths need regression coverage."
        )
    if any(
        keyword in lowered for keyword in ("billing", "payment", "checkout", "invoice")
    ):
        inferred.append(
            "Billing and checkout flows should preserve access controls and money movement safety."
        )
    if any(keyword in lowered for keyword in ("migration", "schema", "database")):
        inferred.append(
            "Schema and data-shape changes should include rollback and compatibility review."
        )
    if any(keyword in lowered for keyword in ("api", "endpoint", "route")):
        inferred.append(
            "Public API and route behavior should stay backward compatible unless the contract says otherwise."
        )
    if not inferred:
        inferred.append(
            "High-impact user paths and changed files should receive at least one negative-case check."
        )

    return inferred


def infer_negative_cases(combined_text: str) -> list[str]:
    """Infer useful negative cases from available context."""
    lowered = combined_text.lower()
    cases = [
        "Reject invalid or incomplete input for the changed behavior.",
        "Preserve existing behavior for unchanged happy-path flows.",
    ]
    if any(
        keyword in lowered for keyword in ("auth", "billing", "payment", "checkout")
    ):
        cases.append(
            "Verify unauthorized users cannot access privileged billing or checkout behavior."
        )
    return cases


def collect_checks(config: dict) -> tuple[list[str], list[str]]:
    """Normalize fast and deep checks from config."""
    explicit_fast = get_nested(config, "fast", "checks", default=None)
    fast_source = (
        explicit_fast
        if explicit_fast is not None
        else get_nested(config, "checks", "fast", default=[])
    )
    fast = normalize_check_names(list(fast_source or []))
    deep = list(get_nested(config, "checks", "deep", default=[]) or [])
    return fast, [str(item) for item in deep]


def normalize_check_names(items: Iterable[object]) -> list[str]:
    """Normalize configured check names from strings or explicit check mappings."""
    names: list[str] = []
    for item in items:
        if isinstance(item, dict):
            if item.get("enabled", True) is False:
                continue
            check_id = item.get("id")
            if check_id:
                names.append(str(check_id))
        elif item:
            names.append(str(item))
    return names


def render_contract(
    title: str,
    config: dict,
    issue_text: str | None = None,
    spec_text: str | None = None,
    diff_text: str | None = None,
) -> str:
    """Render a QA contract draft as markdown."""
    languages = [
        str(item)
        for item in get_nested(config, "project", "languages", default=[]) or []
    ]
    fast_checks, deep_checks = collect_checks(config)
    combined_text = "\n".join(
        part
        for part in (title, issue_text or "", spec_text or "", diff_text or "")
        if part
    )
    source_names = [
        name
        for name, text in (
            ("issue", issue_text),
            ("spec", spec_text),
            ("diff", diff_text),
        )
        if text
    ]

    lines = [
        f"# QA Contract: {title}",
        "",
        "## Contract Summary",
        "",
        "This draft was generated by `qa-z plan`.",
        "",
        format_section_list(
            [
                f"Title: {title}",
                f"Languages: {', '.join(languages)}" if languages else "",
                f"Context sources: {', '.join(source_names)}"
                if source_names
                else "Context sources: none provided",
            ],
            fallback="No contract summary available.",
        ),
        "",
        "## Scope",
        "",
        format_section_list(
            [
                f"Implement or verify the change described by: {title}.",
                "Keep the contract aligned with the provided issue, spec, and diff context.",
                "Limit QA scope to the changed behavior and the adjacent regression surface.",
            ],
            fallback="Define the intended scope of this change.",
        ),
        "",
        "## Assumptions",
        "",
        format_section_list(
            [
                "The repository's configured fast checks are trustworthy merge gates.",
                "Human review is still required for high-risk or ambiguous changes.",
                "This draft should be refined if the issue, spec, or diff reveals missing constraints.",
            ],
            fallback="List the assumptions that make this change safe to merge.",
        ),
        "",
        "## Invariants",
        "",
        format_section_list(
            [
                "Existing passing behavior outside the target change should remain stable.",
                "The implementation should preserve security boundaries, validation, and error handling.",
                "Any new logic should be backed by deterministic tests before merge.",
            ],
            fallback="List the conditions that must remain true after the change.",
        ),
        "",
        "## Risk Edges",
        "",
        format_section_list(
            infer_risk_edges(combined_text),
            fallback="Identify risky edges for this change.",
        ),
        "",
        "## Negative Cases",
        "",
        format_section_list(
            infer_negative_cases(combined_text),
            fallback="List failure modes that should be tested.",
        ),
        "",
        "## Acceptance Checks",
        "",
        format_section_list(
            [
                f"Run fast checks: {', '.join(fast_checks)}." if fast_checks else "",
                "Review the change against this contract before merge.",
                "Escalate to deeper checks if critical paths or security-sensitive code changed.",
            ],
            fallback="Describe the deterministic checks required before merge.",
        ),
        "",
        "## Suggested Checks",
        "",
        "### Fast",
        "",
        format_section_list(fast_checks, fallback="No fast checks configured."),
        "",
        "### Deep",
        "",
        format_section_list(deep_checks, fallback="No deep checks configured."),
        "",
        "## Source Excerpts",
        "",
        "### Issue",
        "",
        excerpt_text(issue_text),
        "",
        "### Spec",
        "",
        excerpt_text(spec_text),
        "",
        "### Diff",
        "",
        excerpt_text(diff_text),
    ]
    return "\n".join(lines).strip() + "\n"


def plan_contract(
    root: Path,
    config: dict,
    title: str,
    slug: str | None = None,
    issue_path: Path | None = None,
    spec_path: Path | None = None,
    diff_path: Path | None = None,
    overwrite: bool = False,
) -> tuple[Path, bool]:
    """Write a contract draft and report whether it was newly created."""
    output_dir = Path(
        str(get_nested(config, "contracts", "output_dir", default="qa/contracts"))
    )
    if not output_dir.is_absolute():
        output_dir = root / output_dir

    contract_path = output_dir / f"{slug or slugify(title)}.md"
    contract_path.parent.mkdir(parents=True, exist_ok=True)

    if contract_path.exists() and not overwrite:
        return contract_path, False

    issue_text = load_source_text(issue_path)
    spec_text = load_source_text(spec_path)
    diff_text = load_source_text(diff_path)
    content = render_contract(
        title, config, issue_text=issue_text, spec_text=spec_text, diff_text=diff_text
    )
    contract_path.write_text(content, encoding="utf-8")
    return contract_path, True
