"""Architecture tests for self-improvement discovery registry seams."""

from __future__ import annotations

import ast
from pathlib import Path

import qa_z.self_improvement_registry as self_improvement_registry_module
import qa_z.self_improvement_stage_groups as self_improvement_stage_groups_module


def _registry_lambda_count() -> int:
    source = Path(self_improvement_registry_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(self_improvement_registry_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return sum(1 for node in ast.walk(tree) if isinstance(node, ast.Lambda))


def test_stage_group_modules_export_group_lists() -> None:
    assert self_improvement_stage_groups_module.BASELINE_DISCOVERY_STAGES
    assert self_improvement_stage_groups_module.EXECUTION_DISCOVERY_STAGES
    assert self_improvement_stage_groups_module.EXECUTION_CONTRACT_DISCOVERY_STAGES
    assert self_improvement_stage_groups_module.SURFACE_DISCOVERY_STAGES
    assert self_improvement_stage_groups_module.WORKTREE_DISCOVERY_STAGES
    assert self_improvement_stage_groups_module.LOOP_HEALTH_DISCOVERY_STAGES


def test_registry_module_keeps_stage_lambdas_out_of_top_level_registry() -> None:
    assert _registry_lambda_count() == 0
