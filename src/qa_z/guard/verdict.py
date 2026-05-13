"""Guard verdict model and persistence helpers."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class GuardVerdict:
    """Machine-readable result of `qa-z guard`."""

    status: str
    reasons: list[str]
    fast: dict[str, Any]
    deep: dict[str, Any]
    risk: dict[str, Any]
    repair: dict[str, Any]
    artifacts: dict[str, str]
    adapter: str = "codex"
    title: str | None = None
    schema_version: int = 1
    kind: str = "qa_z.guard_verdict"
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "kind": self.kind,
            "schema_version": self.schema_version,
            "status": self.status,
            "title": self.title,
            "adapter": self.adapter,
            "reasons": list(self.reasons),
            "fast": dict(self.fast),
            "deep": dict(self.deep),
            "risk": dict(self.risk),
            "repair": dict(self.repair),
            "artifacts": dict(self.artifacts),
        }
        data.update(self.extra)
        return data


def write_verdict_artifacts(
    verdict: GuardVerdict, output_dir: Path
) -> tuple[Path, Path]:
    """Write JSON and Markdown verdict artifacts."""
    try:
        output_dir.mkdir(parents=True, exist_ok=True)
        json_path = output_dir / "verdict.json"
        markdown_path = output_dir / "verdict.md"
        write_guard_verdict_artifact(
            json_path,
            json.dumps(verdict.to_dict(), indent=2, sort_keys=True) + "\n",
            "json",
        )
        write_guard_verdict_artifact(
            markdown_path,
            render_verdict_markdown(verdict),
            "markdown",
        )
        return json_path, markdown_path
    except OSError as exc:
        raise OSError(
            f"could not write guard verdict artifacts to {output_dir}: {exc}"
        ) from exc


def write_guard_verdict_artifact(path: Path, text: str, label: str) -> None:
    """Write one guard verdict artifact with path-aware failures."""
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise OSError(
            f"could not write guard verdict {label} artifact {path}: {exc}"
        ) from exc


def render_verdict_markdown(verdict: GuardVerdict) -> str:
    """Render a compact Markdown verdict."""
    current_truth = verdict.extra.get("current_truth")
    lines = [
        "# QA-Z Guard Verdict",
        "",
        f"- Status: `{verdict.status}`",
        f"- Fast: `{verdict.fast.get('status')}`",
        f"- Deep: `{verdict.deep.get('status', 'not_run')}`",
        f"- Risk: {', '.join(verdict.risk.get('categories', [])) or 'none'}",
    ]
    if isinstance(current_truth, dict) and current_truth.get("status"):
        lines.append(f"- Current truth: `{current_truth['status']}`")
        source = current_truth.get("source_self_inspection")
        if source:
            lines.append(f"- Current truth source: `{source}`")
        refresh_commands = current_truth.get("source_self_inspection_refresh_commands")
        if isinstance(refresh_commands, list):
            for command in refresh_commands:
                if isinstance(command, str) and command.strip():
                    lines.append(f"- Current truth refresh: `{command.strip()}`")
    lines.extend(["", "## Reasons", ""])
    lines.extend(f"- {reason}" for reason in verdict.reasons)
    return "\n".join(lines).rstrip() + "\n"
