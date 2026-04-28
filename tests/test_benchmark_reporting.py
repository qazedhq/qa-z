from __future__ import annotations

from qa_z.benchmark import BenchmarkFixtureResult
from qa_z.benchmark import build_benchmark_summary
from qa_z.benchmark import render_benchmark_report


def test_render_benchmark_report_includes_failed_fixture_reasons() -> None:
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="handoff_case",
                passed=False,
                failures=[
                    "handoff.target_sources missing expected values: deep_finding"
                ],
                categories={"detection": None, "handoff": False, "verify": None},
                actual={},
                artifacts={},
            )
        ]
    )

    report = render_benchmark_report(summary)

    assert "# QA-Z Benchmark Report" in report
    assert "- Snapshot: 0/1 fixtures, overall_rate 0.0" in report
    assert "- Fixtures failed: 1" in report
    assert "handoff_case" in report
    assert "handoff.target_sources missing expected values: deep_finding" in report


def test_render_benchmark_report_includes_generated_policy_and_category_coverage() -> (
    None
):
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="handoff_case",
                passed=False,
                failures=[
                    "handoff.target_sources missing expected values: deep_finding"
                ],
                categories={
                    "detection": None,
                    "handoff": False,
                    "verify": None,
                    "artifact": None,
                    "policy": None,
                },
                actual={},
                artifacts={},
            )
        ]
    )

    report = render_benchmark_report(summary)

    assert "## Generated Output Policy" in report
    assert (
        "- `benchmarks/results/summary.json` and "
        "`benchmarks/results/report.md` are generated benchmark outputs."
    ) in report
    assert (
        "- They are local by default; commit them only as intentional frozen "
        "evidence with surrounding context."
    ) in report
    assert (
        "- Snapshot directories matching `benchmarks/results-*` are generated "
        "runtime artifacts unless intentionally frozen with surrounding context."
    ) in report
    assert "- `benchmarks/results/work/` is disposable scratch output." in report
    assert "- handoff: 0/1 (0.0, covered)" in report
    assert "- detection: 0/0 (0.0, not covered)" in report


def test_render_benchmark_report_includes_deep_warning_provenance() -> None:
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="deep_scan_warning_diagnostics",
                passed=True,
                failures=[],
                categories={"detection": True, "policy": True},
                actual={
                    "deep": {
                        "scan_quality_warning_count": 1,
                        "scan_quality_warning_types": ["Fixpoint timeout"],
                        "scan_quality_warning_paths": ["src/app.py"],
                        "scan_quality_check_ids": ["sg_scan"],
                    }
                },
                artifacts={},
            )
        ]
    )

    report = render_benchmark_report(summary)

    assert "- Deep scan warnings: 1" in report
    assert "- Warning types: Fixpoint timeout" in report
    assert "- Warning paths: src/app.py" in report
    assert "- Warning checks: sg_scan" in report


def test_render_benchmark_report_includes_raw_multi_source_warning_fallback() -> None:
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="deep_scan_warning_multi_source_diagnostics",
                passed=True,
                failures=[],
                categories={"detection": True, "policy": True},
                actual={
                    "deep": {
                        "scan_warning_count": 2,
                        "scan_warning_types": ["Timeout", "Fixpoint timeout"],
                        "scan_warning_paths": ["src/worker.py", "src/app.py"],
                    }
                },
                artifacts={},
            )
        ]
    )

    report = render_benchmark_report(summary)

    assert "- Deep scan warnings: 2" in report
    assert "- Warning types: Timeout, Fixpoint timeout" in report
    assert "- Warning paths: src/worker.py, src/app.py" in report


def test_render_benchmark_report_includes_artifact_paths() -> None:
    summary = build_benchmark_summary(
        [
            BenchmarkFixtureResult(
                name="deep_scan_warning_diagnostics",
                passed=True,
                failures=[],
                categories={"detection": True, "policy": True},
                actual={},
                artifacts={
                    "deep_summary": (
                        "work/deep_scan_warning_diagnostics/repo/.qa-z/runs/benchmark/deep/summary.json"
                    ),
                    "workspace": "work/deep_scan_warning_diagnostics/repo",
                },
            )
        ]
    )

    report = render_benchmark_report(summary)

    assert (
        "- Artifact deep_summary: "
        "work/deep_scan_warning_diagnostics/repo/.qa-z/runs/benchmark/deep/summary.json"
        in report
    )
    assert "- Artifact workspace: work/deep_scan_warning_diagnostics/repo" in report
