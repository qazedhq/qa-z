"""Scope-boundary tests for worktree commit plan release classification."""

from __future__ import annotations

from tests.worktree_commit_plan_test_support import load_plan_module


def test_commit_plan_treats_marketing_x_local_state_as_local_only_generated() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "!! marketing/x/.state/x_tokens.json",
            "!! marketing/x/logs/login.out.log",
            "?? marketing/x/config.local.json",
        ]
    )

    assert result["generated_artifact_paths"] == [
        "marketing/x/.state/",
        "marketing/x/logs/",
        "marketing/x/config.local.json",
    ]
    assert result["generated_local_only_paths"] == [
        "marketing/x/.state/",
        "marketing/x/logs/",
        "marketing/x/config.local.json",
    ]
    assert result["generated_local_by_default_paths"] == []
    assert result["product_decision_paths"] == []


def test_commit_plan_applies_alpha_scope_decisions_to_known_groups() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? .agents/skills/project-improvement-loop/SKILL.md",
            "?? .codex/config.toml",
            "?? .github/copilot-instructions.md",
            "?? docs/agent/agent-operating-manual.md",
            "?? .claude/agents/product-flow-auditor.md",
            "?? marketing/x/README.md",
            "?? marketing/x/scripts/qaz_x.py",
            "?? scripts/validate-agent-operating-model.py",
            "?? tests/test_x_automation.py",
        ]
    )
    release_scope_groups = {
        group["id"]: group for group in result["release_scope_decision_groups"]
    }

    assert result["product_decision_paths"] == []
    assert result["product_decision_groups"] == []
    assert result["attention_reasons"] == []
    assert result["summary"]["product_decision_path_count"] == 0
    assert result["summary"]["product_decision_group_count"] == 0
    assert result["summary"]["release_scope_decision_path_count"] == 9
    assert result["summary"]["release_scope_decision_group_count"] == 5
    assert result["summary"]["approved_alpha_support_path_count"] == 5
    assert result["summary"]["approved_alpha_support_group_count"] == 2
    assert result["summary"]["deferred_alpha_scope_path_count"] == 4
    assert result["summary"]["deferred_alpha_scope_group_count"] == 3
    assert result["approved_alpha_support_paths"] == [
        ".agents/skills/project-improvement-loop/SKILL.md",
        ".codex/config.toml",
        ".github/copilot-instructions.md",
        "docs/agent/agent-operating-manual.md",
        "scripts/validate-agent-operating-model.py",
    ]
    assert result["deferred_alpha_scope_paths"] == [
        ".claude/agents/product-flow-auditor.md",
        "marketing/x/README.md",
        "marketing/x/scripts/qaz_x.py",
        "tests/test_x_automation.py",
    ]
    assert release_scope_groups["codex_operating_model"]["release_scope"] == (
        "approved_alpha_support_scope"
    )
    assert release_scope_groups["operating_model_validator"]["release_scope"] == (
        "approved_alpha_support_scope"
    )
    assert release_scope_groups["marketing_x_surface"]["release_scope"] == (
        "deferred_out_of_alpha_scope"
    )
    assert release_scope_groups["marketing_x_tests"]["release_scope"] == (
        "deferred_out_of_alpha_scope"
    )
    assert release_scope_groups["claude_compatibility_mirror"]["release_scope"] == (
        "deferred_out_of_alpha_scope"
    )
    assert any("approved alpha support" in action for action in result["next_actions"])
    assert any("deferred out-of-alpha" in action for action in result["next_actions"])


def test_commit_plan_surfaces_marketing_and_operating_model_scope_decisions() -> None:
    module = load_plan_module()

    result = module.analyze_status_lines(
        [
            "?? .agents/skills/project-improvement-loop/SKILL.md",
            "?? .codex/config.toml",
            "?? .github/copilot-instructions.md",
            "?? docs/agent/agent-operating-manual.md",
            "?? marketing/x/README.md",
            "?? marketing/x/scripts/qaz_x.py",
            "?? scripts/validate-agent-operating-model.py",
            "?? tests/test_x_automation.py",
            " M src/qa_z/selection_context.py",
        ]
    )
    batches = {batch["id"]: batch for batch in result["batches"]}

    assert result["release_scope_decision_paths"] == [
        ".agents/skills/project-improvement-loop/SKILL.md",
        ".codex/config.toml",
        ".github/copilot-instructions.md",
        "docs/agent/agent-operating-manual.md",
        "marketing/x/README.md",
        "marketing/x/scripts/qaz_x.py",
        "scripts/validate-agent-operating-model.py",
        "tests/test_x_automation.py",
    ]
    assert result["approved_alpha_support_paths"] == [
        ".agents/skills/project-improvement-loop/SKILL.md",
        ".codex/config.toml",
        ".github/copilot-instructions.md",
        "docs/agent/agent-operating-manual.md",
        "scripts/validate-agent-operating-model.py",
    ]
    assert result["deferred_alpha_scope_paths"] == [
        "marketing/x/README.md",
        "marketing/x/scripts/qaz_x.py",
        "tests/test_x_automation.py",
    ]
    assert result["product_decision_paths"] == []
    assert result["unassigned_source_paths"] == []
    assert result["attention_reasons"] == []
    assert result["summary"]["product_decision_path_count"] == 0
    assert result["summary"]["product_decision_group_count"] == 0
    assert result["summary"]["release_scope_decision_path_count"] == 8
    assert result["summary"]["release_scope_decision_group_count"] == 4
    assert result["summary"]["approved_alpha_support_path_count"] == 5
    assert result["summary"]["approved_alpha_support_group_count"] == 2
    assert result["summary"]["deferred_alpha_scope_path_count"] == 3
    assert result["summary"]["deferred_alpha_scope_group_count"] == 2
    assert result["release_scope_decision_groups"] == [
        {
            "id": "codex_operating_model",
            "title": "Codex-native operating model",
            "ownership": "operating-model-owned",
            "release_scope": "approved_alpha_support_scope",
            "path_count": 4,
            "paths": [
                ".agents/skills/project-improvement-loop/SKILL.md",
                ".codex/config.toml",
                ".github/copilot-instructions.md",
                "docs/agent/agent-operating-manual.md",
            ],
            "next_action": (
                "Stage only after approving the operating-model surface as "
                "alpha-release support, separate from runtime QA-Z changes."
            ),
        },
        {
            "id": "marketing_x_surface",
            "title": "Marketing/X network automation",
            "ownership": "marketing/product-owned",
            "release_scope": "deferred_out_of_alpha_scope",
            "path_count": 2,
            "paths": [
                "marketing/x/README.md",
                "marketing/x/scripts/qaz_x.py",
            ],
            "next_action": (
                "Keep out of QA-Z alpha release unless a product owner approves "
                "the credential-gated marketing/network surface."
            ),
        },
        {
            "id": "operating_model_validator",
            "title": "Operating-model validator",
            "ownership": "operating-model-owned",
            "release_scope": "approved_alpha_support_scope",
            "path_count": 1,
            "paths": ["scripts/validate-agent-operating-model.py"],
            "next_action": (
                "Stage with the operating-model support batch after format and "
                "validator checks pass."
            ),
        },
        {
            "id": "marketing_x_tests",
            "title": "Marketing/X automation tests",
            "ownership": "marketing/product-owned",
            "release_scope": "deferred_out_of_alpha_scope",
            "path_count": 1,
            "paths": ["tests/test_x_automation.py"],
            "next_action": (
                "Stage with marketing/X only if that product surface is approved."
            ),
        },
    ]
    assert batches["self_inspection_backlog"]["changed_paths"] == [
        "src/qa_z/selection_context.py"
    ]
    assert any("approved alpha support" in action for action in result["next_actions"])
    assert any("deferred out-of-alpha" in action for action in result["next_actions"])
