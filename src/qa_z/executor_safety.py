"""Explicit pre-live executor safety package artifacts for QA-Z."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path

EXECUTOR_SAFETY_KIND = "qa_z.executor_safety"
EXECUTOR_SAFETY_SCHEMA_VERSION = 1
EXECUTOR_SAFETY_PACKAGE_ID = "pre_live_executor_safety_v1"
EXECUTOR_SAFETY_RULE_IDS = (
    "no_op_requires_explanation",
    "retry_boundary_is_manual",
    "mutation_scope_limited",
    "unrelated_refactors_prohibited",
    "verification_required_for_completed",
    "outcome_classification_must_be_honest",
)


def executor_safety_package() -> dict[str, Any]:
    """Return the stable pre-live executor safety package."""
    return {
        "kind": EXECUTOR_SAFETY_KIND,
        "schema_version": EXECUTOR_SAFETY_SCHEMA_VERSION,
        "package_id": EXECUTOR_SAFETY_PACKAGE_ID,
        "status": "pre_live_only",
        "summary": (
            "Freeze local executor safety policy before any live executor "
            "integration is attempted."
        ),
        "rules": [
            {
                "id": "no_op_requires_explanation",
                "category": "no_op_safeguard",
                "requirement": (
                    "No-op and not-applicable outcomes require explicit explanation "
                    "and must not be treated as silent success."
                ),
                "enforced_by": [
                    "executor-result ingest warnings",
                    "executor-result backlog implications",
                ],
            },
            {
                "id": "retry_boundary_is_manual",
                "category": "retry_boundary",
                "requirement": (
                    "QA-Z does not auto-retry, auto-redispatch, or silently replay an "
                    "external executor after rejected, partial, or failed outcomes."
                ),
                "enforced_by": [
                    "repair-session guidance",
                    "executor-bridge guidance",
                    "operator follow-up only",
                ],
            },
            {
                "id": "mutation_scope_limited",
                "category": "mutation_scope",
                "requirement": (
                    "External edits must stay within the selected repair-session and "
                    "bridge scope."
                ),
                "enforced_by": [
                    "repair handoff affected_files",
                    "executor-result scope validation",
                ],
            },
            {
                "id": "unrelated_refactors_prohibited",
                "category": "scope_control",
                "requirement": (
                    "External executors must not broaden scope or bundle unrelated "
                    "refactors with the requested repair."
                ),
                "enforced_by": [
                    "repair-session guide",
                    "executor-bridge non-goals",
                ],
            },
            {
                "id": "verification_required_for_completed",
                "category": "verification_gate",
                "requirement": (
                    "A completed result is not merge-ready until deterministic QA-Z "
                    "verification has passed or attached approved evidence."
                ),
                "enforced_by": [
                    "repair-session verify flow",
                    "executor-result verify-resume gating",
                ],
            },
            {
                "id": "outcome_classification_must_be_honest",
                "category": "outcome_classification",
                "requirement": (
                    "Executor outcomes must be classified honestly as completed, "
                    "partial, failed, no_op, or not_applicable, with partial work "
                    "preserved rather than disguised."
                ),
                "enforced_by": [
                    "qa_z.executor_result schema",
                    "executor-result ingest status handling",
                ],
            },
        ],
        "non_goals": [
            "no live Codex or Claude API execution from QA-Z",
            "no remote orchestration, queues, schedulers, or daemons",
            "no automatic code editing, commit, push, or GitHub bot behavior",
        ],
        "enforcement_points": {
            "repair_session": [
                "session-local safety artifacts",
                "executor guide references the safety package",
            ],
            "executor_bridge": [
                "bridge copies and summarizes the safety package",
                "bridge guides reference the same contract",
            ],
            "executor_result_ingest": [
                "scope validation",
                "freshness validation",
                "no-op safeguards",
                "verify-resume gating",
                "outcome classification",
            ],
        },
    }


def render_executor_safety_markdown(payload: dict[str, Any] | None = None) -> str:
    """Render the human-readable safety package companion."""
    package = payload or executor_safety_package()
    lines = [
        "# QA-Z Pre-Live Executor Safety Package",
        "",
        f"- Package id: `{package['package_id']}`",
        f"- Status: `{package['status']}`",
        f"- Summary: {package['summary']}",
        "",
        "## Rules",
        "",
    ]
    for rule in package.get("rules", []):
        if not isinstance(rule, dict):
            continue
        lines.append(
            f"- `{rule.get('id', 'unknown')}`: {rule.get('requirement', '').strip()}"
        )
    lines.extend(["", "## Non-Goals", ""])
    for item in package.get("non_goals", []):
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"


def write_executor_safety_artifacts(*, root: Path, output_dir: Path) -> dict[str, str]:
    """Write the stable safety package JSON and Markdown artifacts."""
    payload = executor_safety_package()
    json_path = output_dir / "executor_safety.json"
    markdown_path = output_dir / "executor_safety.md"
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(render_executor_safety_markdown(payload), encoding="utf-8")
    return {
        "policy_json": format_path(json_path, root),
        "policy_markdown": format_path(markdown_path, root),
    }
