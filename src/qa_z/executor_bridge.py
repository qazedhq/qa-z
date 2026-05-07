"""External executor bridge packages for QA-Z repair sessions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

EXECUTOR_BRIDGE_KIND = "qa_z.executor_bridge"
EXECUTOR_BRIDGE_SCHEMA_VERSION = 1

DEFAULT_NON_GOALS = [
    "do not broaden scope",
    "do not perform unrelated refactors",
    "do not weaken deterministic checks",
    "do not call Codex or Claude APIs from QA-Z",
    "do not commit, push, create branches, or post GitHub comments",
]

DEFAULT_SAFETY_CONSTRAINTS = [
    "Use only the packaged QA-Z evidence and linked handoff artifacts.",
    "Keep edits focused on the selected repair-session objective.",
    "Record partial completion honestly if validation cannot pass.",
    "Return control to QA-Z through repair-session verification.",
]


class ExecutorBridgeError(ValueError):
    """Raised when a bridge package cannot be created from available evidence."""


@dataclass(frozen=True)
class ExecutorBridgePaths:
    """Paths written for one executor bridge package."""

    bridge_dir: Path
    manifest_path: Path
    executor_guide_path: Path
    codex_path: Path
    claude_path: Path
    result_template_path: Path


from qa_z.executor_bridge_context import (  # noqa: E402
    bridge_action_context_inputs,
    bridge_missing_action_context_inputs,
    context_source_label,
    copy_input,
    path_is_within,
    resolve_path,
    safe_context_input_name,
)
from qa_z.executor_bridge_guides import (  # noqa: E402
    bridge_placeholder_summary_guidance,
    render_executor_specific_guide,
)
from qa_z.executor_bridge_loop import (  # noqa: E402
    load_loop_outcome,
    read_json_object,
    repair_session_action,
    resolve_loop_outcome_path,
)
from qa_z.executor_bridge_package import (  # noqa: E402
    bridge_manifest,
    create_executor_bridge,
)
from qa_z.executor_bridge_render import (  # noqa: E402
    render_bridge_stdout,
    render_executor_bridge_guide,
)
from qa_z.executor_bridge_summary import (  # noqa: E402
    bridge_evidence_summary,
    bridge_safety_package_summary,
    bridge_safety_rule_count,
)
from qa_z.executor_bridge_support import (  # noqa: E402
    bridge_output_policy,
    bridge_output_warnings,
    default_bridge_id,
    ensure_session_exists,
    format_command,
    normalize_bridge_id,
    resolve_bridge_dir,
    slugify,
    utc_now,
    write_json,
)

__all__ = [
    "EXECUTOR_BRIDGE_KIND",
    "EXECUTOR_BRIDGE_SCHEMA_VERSION",
    "DEFAULT_NON_GOALS",
    "DEFAULT_SAFETY_CONSTRAINTS",
    "ExecutorBridgeError",
    "ExecutorBridgePaths",
    "create_executor_bridge",
    "bridge_manifest",
    "render_executor_bridge_guide",
    "render_bridge_stdout",
    "load_loop_outcome",
    "resolve_loop_outcome_path",
    "repair_session_action",
    "read_json_object",
    "write_json",
    "normalize_bridge_id",
    "default_bridge_id",
    "slugify",
    "format_command",
    "bridge_output_policy",
    "bridge_output_warnings",
    "resolve_bridge_dir",
    "ensure_session_exists",
    "utc_now",
    "resolve_path",
    "path_is_within",
    "context_source_label",
    "safe_context_input_name",
    "bridge_action_context_inputs",
    "bridge_missing_action_context_inputs",
    "copy_input",
    "bridge_evidence_summary",
    "bridge_safety_package_summary",
    "bridge_safety_rule_count",
    "bridge_placeholder_summary_guidance",
    "render_executor_specific_guide",
]
