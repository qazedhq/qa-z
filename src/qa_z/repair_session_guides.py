"""Guide helpers for external repair-session executors."""

from __future__ import annotations

from pathlib import Path

from qa_z.artifacts import resolve_path


def write_executor_guide(session: object, handoff: object, root: Path) -> Path:
    """Write a guide for an external human or agent executor."""
    path = resolve_path(root, str(getattr(session, "executor_guide_path")))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_executor_guide(session, handoff), encoding="utf-8")
    return path


def render_executor_guide(session: object, handoff: object) -> str:
    """Render the external executor guide Markdown."""
    lines = [
        "# QA-Z Repair Session Executor Guide",
        "",
        "This session packages deterministic QA-Z evidence for an external repair executor.",
        "It does not call Codex or Claude APIs, run remote jobs, schedule work, or edit code by itself.",
        "",
        "## Session",
        "",
        f"- Session id: `{getattr(session, 'session_id')}`",
        f"- State: `{getattr(session, 'state')}`",
        f"- Baseline run: `{getattr(session, 'baseline_run_dir')}`",
        f"- Handoff directory: `{getattr(session, 'handoff_dir')}`",
        "",
        "## Handoff Artifacts",
        "",
    ]
    for label, path in getattr(session, "handoff_artifacts").items():
        lines.append(f"- {label}: `{path}`")
    lines.extend(["", "## Repair Objectives", ""])
    targets = getattr(handoff, "targets")
    if not targets:
        lines.append("- No blocking repair targets were found in the baseline run.")
    for target in targets:
        location = f" at `{target.location}`" if target.location else ""
        lines.append(f"- `{target.id}`{location}: {target.objective}")
    lines.extend(["", "## Do Not Change", ""])
    for item in getattr(handoff, "non_goals"):
        lines.append(f"- {item}")
    lines.extend(
        [
            "- Do not weaken deterministic checks, tests, or configured gates.",
            "",
            "## Pre-Live Safety Package",
            "",
            f"- Policy JSON: `{getattr(session, 'safety_artifacts').get('policy_json', 'none')}`",
            f"- Policy Markdown: `{getattr(session, 'safety_artifacts').get('policy_markdown', 'none')}`",
            "- This package freezes the local executor safety boundary before any live executor work.",
            "",
            "## After Editing",
            "",
            "Run one of these local verification flows from the repository root:",
            "",
            "```bash",
            f"python -m qa_z repair-session verify --session {getattr(session, 'session_dir')} --rerun",
            "```",
            "",
            "or, if a candidate run already exists:",
            "",
            "```bash",
            (
                "python -m qa_z repair-session verify "
                f"--session {getattr(session, 'session_dir')} "
                "--candidate-run .qa-z/runs/<candidate>"
            ),
            "```",
            "",
            "The verify step writes session-local verification artifacts and an outcome summary.",
        ]
    )
    return "\n".join(lines).strip() + "\n"
