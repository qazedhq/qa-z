from __future__ import annotations

import qa_z.benchmark_report_details as report_details_module


def test_render_deep_warning_lines_includes_warning_provenance() -> None:
    lines = report_details_module.render_deep_warning_lines(
        {
            "scan_quality_warning_count": 1,
            "scan_quality_warning_types": ["Fixpoint timeout"],
            "scan_quality_warning_paths": ["src/app.py"],
            "scan_quality_check_ids": ["sg_scan"],
        }
    )

    assert lines == [
        "- Deep scan warnings: 1",
        "- Warning types: Fixpoint timeout",
        "- Warning paths: src/app.py",
        "- Warning checks: sg_scan",
    ]


def test_render_deep_warning_lines_falls_back_to_raw_scan_warning_fields() -> None:
    lines = report_details_module.render_deep_warning_lines(
        {
            "scan_warning_count": 2,
            "scan_warning_types": ["Timeout", "Fixpoint timeout"],
            "scan_warning_paths": ["src/worker.py", "src/app.py"],
        }
    )

    assert lines == [
        "- Deep scan warnings: 2",
        "- Warning types: Timeout, Fixpoint timeout",
        "- Warning paths: src/worker.py, src/app.py",
    ]


def test_render_artifact_lines_sorts_non_blank_entries() -> None:
    lines = report_details_module.render_artifact_lines(
        {
            "workspace": "work/repo",
            "": "",
            "deep_summary": "work/repo/.qa-z/runs/deep/summary.json",
        }
    )

    assert lines == [
        "- Artifact deep_summary: work/repo/.qa-z/runs/deep/summary.json",
        "- Artifact workspace: work/repo",
    ]
