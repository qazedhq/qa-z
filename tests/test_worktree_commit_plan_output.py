"""Output-focused tests for the worktree commit plan helper."""

from __future__ import annotations

from tests.worktree_commit_plan_test_support import load_plan_module


def test_commit_plan_human_output_prints_next_actions() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.l20.json",
            " M src/qa_z/new_surface.py",
        ]
    )

    output = module.render_human(result)

    assert "Generated at:" in output
    assert "Next actions:" in output
    assert "- Add unassigned source paths to an existing commit batch rule" in output


def test_commit_plan_human_output_prints_batch_rollup() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            " M src/qa_z/benchmark.py",
            " M README.md",
        ]
    )

    output = module.render_human(result)

    assert "Batches: changed=1, unchanged=10" in output


def test_commit_plan_human_output_prints_generated_policy_split() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.json",
            "!! benchmarks/results/report.md",
        ]
    )

    output = module.render_human(result)

    assert "Generated artifacts: 2 (files=0, dirs=2)" in output
    assert "Generated policy: local_only=1, local_by_default=1" in output
    assert "Local-only generated preview: dist/" in output
    assert "Local-by-default generated preview: benchmarks/results/" in output


def test_commit_plan_splits_generated_artifacts_by_policy_bucket() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.json",
            "?? .qa-z/runs/latest-run.json",
            "?? benchmarks/results-2026-04-23-refresh/",
            "?? benchmarks/results/report.md",
        ]
    )

    assert result["generated_artifact_paths"] == [
        "dist/",
        ".qa-z/",
        "benchmarks/results-2026-04-23-refresh/",
        "benchmarks/results/",
    ]
    assert result["generated_local_only_paths"] == ["dist/", ".qa-z/"]
    assert result["generated_local_by_default_paths"] == [
        "benchmarks/results-2026-04-23-refresh/",
        "benchmarks/results/",
    ]
    assert result["summary"]["generated_artifact_count"] == 4
    assert result["summary"]["generated_local_only_count"] == 2
    assert result["summary"]["generated_local_by_default_count"] == 2
    assert result["next_actions"] == [
        (
            "Keep local-only generated runtime artifacts out of staging and "
            "cleanup review unless a fixture/doc task explicitly freezes them."
        ),
        (
            "Decide whether local-by-default benchmark evidence stays local or "
            "is intentionally frozen with command/date context before staging "
            "those generated paths."
        ),
    ]


def test_commit_plan_human_output_prints_report_path_count() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            " M docs/reports/current-state-analysis.md",
            " M src/qa_z/benchmark.py",
        ]
    )

    output = module.render_human(result)

    assert "Report paths: 1" in output
    assert "Report preview: docs/reports/current-state-analysis.md" in output


def test_commit_plan_human_output_prints_shared_patch_add_preview() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            " M README.md",
            " M docs/reports/current-state-analysis.md",
            " M src/qa_z/benchmark.py",
        ]
    )

    output = module.render_human(result)

    assert "Shared patch-add paths: 2" in output
    assert (
        "Shared patch-add preview: README.md, docs/reports/current-state-analysis.md"
        in output
    )


def test_commit_plan_human_output_prints_cross_cutting_group_rollup() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            " M README.md",
            " M src/qa_z/commands/runtime.py",
            " M tests/test_runtime_commands.py",
            " M docs/reports/current-state-analysis.md",
        ]
    )

    output = module.render_human(result)

    assert "Cross-cutting groups: 4" in output
    assert "- public_docs_contract: 1 paths" in output
    assert "- command_router_spine: 1 paths" in output
    assert "- command_surface_tests: 1 paths" in output
    assert "- status_reports: 1 paths" in output
    assert "  patch command: git add --patch -- src/qa_z/commands/runtime.py" in output


def test_commit_plan_human_output_includes_active_strict_mode() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.json",
            " M README.md",
        ],
        fail_on_generated=True,
        fail_on_cross_cutting=True,
    )

    output = module.render_human(result)

    assert "Strict mode: fail_on_generated, fail_on_cross_cutting" in output


def test_commit_plan_human_output_includes_attention_reasons() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.json",
            " M README.md",
        ],
        fail_on_generated=True,
        fail_on_cross_cutting=True,
    )

    output = module.render_human(result)

    assert (
        "Attention reasons: generated_artifacts_present, cross_cutting_paths_present"
    ) in output


def test_commit_plan_human_output_deduplicates_attention_reasons() -> None:
    module = load_plan_module()
    payload = module.analyze_status_lines([" M README.md"], fail_on_cross_cutting=True)
    payload["attention_reasons"] = [
        "cross_cutting_paths_present",
        "cross_cutting_paths_present",
        "generated_artifacts_present",
    ]

    output = module.render_human(payload)

    assert (
        "Attention reasons: cross_cutting_paths_present, generated_artifacts_present"
        in output
    )
    assert "cross_cutting_paths_present, cross_cutting_paths_present" not in output


def test_commit_plan_human_output_deduplicates_next_actions() -> None:
    module = load_plan_module()
    payload = module.analyze_status_lines(["?? dist/alpha-release-gate.json"])
    repeated = "Review generated artifacts before staging."
    payload["next_actions"] = [repeated, repeated, "Run the strict staging audit."]

    output = module.render_human(payload)

    assert f"- {repeated}" in output
    assert output.count(f"- {repeated}") == 1
    assert "- Run the strict staging audit." in output


def test_commit_plan_human_output_prints_changed_batch_validation_commands() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            " M src/qa_z/benchmark.py",
            " M src/qa_z/self_improvement.py",
        ]
    )

    output = module.render_human(result)

    assert "- benchmark_coverage: 1 paths" in output
    assert "  include: src/qa_z/benchmark.py" in output
    assert "  stage command: git add -- src/qa_z/benchmark.py" in output
    assert "  validation: python -m pytest tests/test_benchmark.py -q" in output
    assert "  validation: python -m qa_z benchmark --json" in output
    assert "- self_inspection_backlog: 1 paths" in output
    assert (
        "  validation: python -m pytest tests/test_self_improvement.py tests/test_cli.py -q"
        in output
    )


def test_commit_plan_human_output_quotes_stage_command_paths_with_spaces() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [' M "benchmarks/fixtures/path with space/expected.json"']
    )

    output = module.render_human(result)

    assert (
        '  stage command: git add -- "benchmarks/fixtures/path with space/expected.json"'
        in output
    )


def test_commit_plan_human_output_prints_batch_filter_context() -> None:
    module = load_plan_module()
    result = module.analyze_status_lines(
        [
            "?? dist/alpha-release-gate.json",
            " M src/qa_z/benchmark.py",
        ],
        fail_on_generated=True,
    )
    filtered = module.filter_payload_for_batch(result, "benchmark_coverage")

    output = module.render_human(filtered)

    assert "Selected batch: benchmark_coverage (ready, 1 paths)" in output
    assert "Selected staging: include=1, patch_add=0, generated_excludes=1" in output
    assert "Global status: attention_required" in output
    assert "Global attention reasons: generated_artifacts_present" in output
