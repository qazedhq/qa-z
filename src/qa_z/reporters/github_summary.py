"""GitHub Actions summary renderers for QA-Z artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path, load_run_summary, resolve_run_source
from qa_z.reporters.verification_publish import (
    build_publish_summary,
    publish_summary_json,
    render_publish_summary,
)

GITHUB_SUMMARY_KIND = "qa_z.github_summary"
GITHUB_SUMMARY_SCHEMA_VERSION = 1


def render_github_summary(
    *,
    root: Path,
    config: dict[str, Any] | None = None,
    from_run: str | None = None,
    from_verify: str | None = None,
    from_session: str | None = None,
) -> str:
    """Render compact Markdown for GitHub Actions job summaries."""
    selected = [value for value in (from_run, from_verify, from_session) if value]
    if len(selected) != 1:
        raise ValueError("Provide exactly one GitHub summary source.")

    if from_verify or from_session:
        summary = build_publish_summary(
            root=root,
            from_verify=from_verify,
            from_session=from_session,
        )
        return "## QA-Z Summary\n\n" + render_publish_summary(summary)

    run_source = resolve_run_source(root, config or {}, from_run)
    run_summary = load_run_summary(run_source.summary_path)
    lines = [
        "## QA-Z Summary",
        "",
        f"- Run: `{format_path(run_source.run_dir, root)}`",
        f"- Run mode: {run_summary.mode}",
        f"- Status: {run_summary.status}",
        f"- Summary: `{format_path(run_source.summary_path, root)}`",
    ]
    if run_summary.contract_path:
        lines.append(f"- Contract: `{run_summary.contract_path}`")
    totals = run_summary.totals
    lines.extend(
        [
            f"- Passed: {totals.get('passed', 0)}",
            f"- Failed: {totals.get('failed', 0)}",
            f"- Warnings: {totals.get('warning', 0)}",
            f"- Skipped: {totals.get('skipped', 0)}",
        ]
    )
    return "\n".join(lines) + "\n"


def github_summary_json(
    *,
    root: Path,
    config: dict[str, Any] | None = None,
    from_run: str | None = None,
    from_verify: str | None = None,
    from_session: str | None = None,
) -> str:
    """Render JSON for the selected GitHub summary source."""
    selected = [value for value in (from_run, from_verify, from_session) if value]
    if len(selected) != 1:
        raise ValueError("Provide exactly one GitHub summary source.")

    if from_verify or from_session:
        summary = build_publish_summary(
            root=root,
            from_verify=from_verify,
            from_session=from_session,
        )
        return publish_summary_json(summary)

    run_source = resolve_run_source(root, config or {}, from_run)
    run_summary = load_run_summary(run_source.summary_path)
    payload = {
        "kind": GITHUB_SUMMARY_KIND,
        "schema_version": GITHUB_SUMMARY_SCHEMA_VERSION,
        "source_type": "run",
        "source_path": format_path(run_source.summary_path, root),
        "run_dir": format_path(run_source.run_dir, root),
        "mode": run_summary.mode,
        "status": run_summary.status,
        "contract_path": run_summary.contract_path,
        "totals": dict(run_summary.totals),
    }
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"
