"""Freshness-sensitive self-inspection report tests."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.self_improvement import run_self_inspection
from tests.self_improvement_test_support import (
    stub_live_repository_signals,
    write_report,
)


NOW = "2026-04-15T00:00:00Z"


def test_self_inspection_skips_stale_dated_deferred_cleanup_report(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=1,
        untracked_count=0,
        staged_count=0,
        modified_paths=["README.md"],
        untracked_paths=[],
        runtime_artifact_paths=[],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-10

        Deferred cleanup once mentioned generated benchmark outputs and
        intentionally frozen evidence decisions.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="stale-cleanup-date")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" not in categories


def test_self_inspection_skips_deferred_cleanup_report_without_head_when_live_head_known(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=1,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md"],
        untracked_paths=["benchmarks/results/report.md"],
        runtime_artifact_paths=["benchmarks/results/report.md"],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-15
        Branch context: `codex/qa-z-bootstrap`

        Deferred cleanup once mentioned generated benchmark outputs and
        intentionally frozen evidence decisions.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="cleanup-needs-head")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" not in categories


def test_self_inspection_skips_stale_dated_integration_report(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=2,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["tests/test_cli.py"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Date: 2026-04-10

        Dirty worktree integration caveats need a commit split before release.
        """,
    )

    paths = run_self_inspection(
        root=tmp_path, now=NOW, loop_id="stale-integration-date"
    )
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "integration_gap" not in categories


def test_self_inspection_skips_branch_mismatched_integration_report(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        modified_count=2,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["tests/test_cli.py"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Date: 2026-04-15
        Branch: `feature/old-split`

        Dirty worktree integration caveats need a commit split before release.
        """,
    )

    paths = run_self_inspection(
        root=tmp_path, now=NOW, loop_id="branch-mismatch-integration"
    )
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "integration_gap" not in categories


def test_self_inspection_skips_head_mismatched_integration_report(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=2,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["tests/test_cli.py"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`
        Head: `abcdefabcdefabcdefabcdefabcdefabcdefabcd`

        Dirty worktree integration caveats need a commit split before release.
        """,
    )

    paths = run_self_inspection(
        root=tmp_path, now=NOW, loop_id="head-mismatch-integration"
    )
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "integration_gap" not in categories


def test_self_inspection_allows_head_matched_report_on_detached_checkout(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="HEAD",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=2,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["tests/test_cli.py"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`
        Head: `1234567890abcdef1234567890abcdef12345678`

        Dirty worktree integration caveats need a commit split before release.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="detached-head-fresh")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "integration_gap" in categories


def test_self_inspection_skips_stale_dated_commit_isolation_report(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=3,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["docs/reports/worktree-commit-plan.md"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Date: 2026-04-10

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation and `git add -p`.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="stale-isolation-date")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "commit_isolation_gap" not in categories


def test_self_inspection_skips_commit_isolation_report_without_head_when_live_head_known(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=2,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["docs/reports/worktree-commit-plan.md"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[],
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation and `git add -p`.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="commit-needs-head")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "commit_isolation_gap" not in categories


def test_self_inspection_allows_headless_cleanup_reports_without_live_head(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        modified_count=1,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md"],
        untracked_paths=["benchmarks/results/report.md"],
        runtime_artifact_paths=["benchmarks/results/report.md"],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-15
        Branch context: `codex/qa-z-bootstrap`

        Deferred cleanup once mentioned generated benchmark outputs and
        intentionally frozen evidence decisions.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="cleanup-no-live-head")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" in categories


def test_self_inspection_skips_branch_mismatched_cleanup_reports(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        modified_count=3,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["docs/reports/worktree-commit-plan.md"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-15
        Branch context: `feature/old-split`

        Deferred cleanup once mentioned generated benchmark outputs and
        intentionally frozen evidence decisions.
        """,
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Date: 2026-04-15
        Branch: `feature/old-split`

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation and `git add -p`.
        """,
    )

    paths = run_self_inspection(
        root=tmp_path, now=NOW, loop_id="branch-mismatch-cleanup"
    )
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" not in categories
    assert "commit_isolation_gap" not in categories


def test_self_inspection_skips_head_mismatched_cleanup_reports(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        current_branch="codex/qa-z-bootstrap",
        current_head="1234567890abcdef1234567890abcdef12345678",
        modified_count=3,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md", "src/qa_z/cli.py"],
        untracked_paths=["docs/reports/worktree-commit-plan.md"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Date: 2026-04-15
        Branch context: `codex/qa-z-bootstrap`
        Head: `abcdefabcdefabcdefabcdefabcdefabcdefabcd`

        Deferred cleanup once mentioned generated benchmark outputs and
        intentionally frozen evidence decisions.
        """,
    )
    write_report(
        tmp_path,
        "worktree-commit-plan.md",
        """
        # QA-Z Worktree Commit Plan

        Date: 2026-04-15
        Branch: `codex/qa-z-bootstrap`
        Head: `abcdefabcdefabcdefabcdefabcdefabcdefabcd`

        Commit order dependency remains. The corrected commit sequence still
        requires foundation-before-benchmark isolation and `git add -p`.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="head-mismatch-cleanup")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "deferred_cleanup_gap" not in categories
    assert "commit_isolation_gap" not in categories
