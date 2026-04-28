"""Tests for self-improvement discovery-pipeline contracts."""

from __future__ import annotations

from pathlib import Path

import qa_z.discovery_pipeline as discovery_pipeline_module
import qa_z.self_improvement as self_improvement_module


def test_discovery_pipeline_passes_accumulated_candidates_to_later_stages() -> None:
    seen: list[tuple[str, list[str], str | None, int]] = []

    def first_stage(root, backlog, candidates, live_signals, generated_at):
        seen.append(
            ("first", list(candidates), generated_at, live_signals["modified_count"])
        )
        return ["benchmark"]

    def second_stage(root, backlog, candidates, live_signals, generated_at):
        seen.append(
            ("second", list(candidates), generated_at, live_signals["modified_count"])
        )
        return ["repair"]

    stages = [
        discovery_pipeline_module.DiscoveryStage("benchmark", first_stage),
        discovery_pipeline_module.DiscoveryStage("repair", second_stage),
    ]

    result = discovery_pipeline_module.run_discovery_pipeline(
        root=Path("."),
        backlog={"items": []},
        live_signals={"modified_count": 2},
        generated_at="2026-04-15T00:00:00Z",
        stages=stages,
    )

    assert result == ["benchmark", "repair"]
    assert seen == [
        ("first", [], "2026-04-15T00:00:00Z", 2),
        ("second", ["benchmark"], "2026-04-15T00:00:00Z", 2),
    ]


def test_discovery_stage_names_pin_self_improvement_pipeline_order() -> None:
    assert self_improvement_module.DISCOVERY_STAGE_NAMES == (
        "benchmark",
        "verification",
        "session",
        "executor_result",
        "executor_ingest",
        "executor_history",
        "artifact_consistency",
        "docs_drift",
        "coverage_gap",
        "executor_contract",
        "worktree_risk",
        "deferred_cleanup",
        "commit_isolation",
        "artifact_hygiene",
        "runtime_artifact_cleanup",
        "evidence_freshness",
        "integration_gap",
        "empty_loop",
        "fallback_family_repeat",
        "backlog_reseeding",
    )
