"""Tests for self-improvement live-repository and artifact-policy behavior."""

from __future__ import annotations

import json
from pathlib import Path

from qa_z.self_improvement import (
    collect_live_repository_signals,
    live_repository_summary,
    render_live_repository_summary,
    run_self_inspection,
    select_next_tasks,
)
from tests.self_improvement_test_support import (
    stub_live_repository_signals,
    write_generated_artifact_gitignore,
    write_generated_evidence_policy,
    write_report,
)


NOW = "2026-04-15T00:00:00Z"


def test_self_inspection_promotes_artifact_hygiene_and_evidence_freshness_gaps(
    tmp_path: Path, monkeypatch
) -> None:
    stub_live_repository_signals(
        monkeypatch,
        modified_count=4,
        untracked_count=2,
        staged_count=0,
        modified_paths=[".gitignore"],
        untracked_paths=["benchmarks/results/summary.json"],
        runtime_artifact_paths=[".qa-z/loops/latest/outcome.json"],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Runtime artifacts are still mixed with source-like areas and the generated
        benchmark outputs need a clearer cleanup policy.
        """,
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Frozen evidence versus runtime result storage is still ambiguous in the
        current worktree, especially for benchmark outputs.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="artifact-gap-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "artifact_hygiene_gap" in categories
    assert "evidence_freshness_gap" in categories
    hygiene = next(
        item
        for item in report["candidates"]
        if item["category"] == "artifact_hygiene_gap"
    )
    freshness = next(
        item
        for item in report["candidates"]
        if item["category"] == "evidence_freshness_gap"
    )
    assert hygiene["recommendation"] == "separate_runtime_from_source_artifacts"
    assert freshness["recommendation"] == "clarify_generated_vs_frozen_evidence_policy"


def test_generated_artifact_policy_snapshot_requires_policy_doc(
    tmp_path: Path,
) -> None:
    write_generated_artifact_gitignore(tmp_path)

    signals = collect_live_repository_signals(tmp_path)

    assert signals["generated_artifact_ignore_policy_explicit"] is True
    assert signals["generated_artifact_documented_policy_explicit"] is False
    assert signals["generated_artifact_policy_explicit"] is False
    assert signals["missing_generated_artifact_policy_rules"] == []
    assert (
        "generated-vs-frozen evidence policy document is missing"
        in signals["missing_generated_artifact_policy_terms"]
    )


def test_generated_artifact_policy_snapshot_requires_results_snapshot_ignore_rule(
    tmp_path: Path,
) -> None:
    (tmp_path / ".gitignore").write_text(
        "\n".join(
            [
                ".qa-z/",
                ".mypy_cache_safe/",
                ".ruff_cache_safe/",
                "%TEMP%/",
                "/tmp_*",
                "/benchmarks/minlock-*",
                "!benchmarks/fixtures/**/repo/.qa-z/",
                "!benchmarks/fixtures/**/repo/.qa-z/**",
                "benchmarks/results/work/",
                "benchmarks/results/summary.json",
                "benchmarks/results/report.md",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    write_generated_evidence_policy(tmp_path)

    signals = collect_live_repository_signals(tmp_path)

    assert signals["generated_artifact_ignore_policy_explicit"] is False
    assert signals["generated_artifact_policy_explicit"] is False
    assert signals["missing_generated_artifact_policy_rules"] == [
        "benchmarks/results-*"
    ]


def test_generated_artifact_policy_snapshot_requires_explicit_split_terms(
    tmp_path: Path,
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    policy_path = tmp_path / "docs" / "generated-vs-frozen-evidence-policy.md"
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(
        """
        # Generated Versus Frozen Evidence Policy

        Root `.qa-z/**` artifacts are local runtime state.
        `.mypy_cache_safe/**`, `.ruff_cache_safe/**`, literal `%TEMP%/**`,
        root `/tmp_*` scratch roots, and `/benchmarks/minlock-*` benchmark
        lock probes are runtime scratch trees.
        `benchmarks/results/work/**` is disposable benchmark scratch output.
        `benchmarks/results-*` is local by default unless intentionally frozen
        as evidence with surrounding documentation.
        `benchmarks/results/summary.json` and `benchmarks/results/report.md`
        are local by default and may be committed only as intentional frozen
        evidence with surrounding documentation.
        `benchmarks/fixtures/**/repo/.qa-z/**` is allowed as fixture-local
        deterministic benchmark input.
        """.strip()
        + "\n",
        encoding="utf-8",
    )

    signals = collect_live_repository_signals(tmp_path)

    assert signals["generated_artifact_policy_explicit"] is False
    assert any(
        "local-only runtime artifacts" in term
        for term in signals["missing_generated_artifact_policy_terms"]
    )
    assert any(
        "local-by-default benchmark evidence" in term
        for term in signals["missing_generated_artifact_policy_terms"]
    )


def test_live_repository_summary_counts_release_evidence_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    write_generated_evidence_policy(tmp_path)
    monkeypatch.setattr(
        "qa_z.live_repository.git_worktree_snapshot",
        lambda _root: {
            "modified_count": 1,
            "untracked_count": 2,
            "staged_count": 0,
            "modified_paths": ["dist/alpha-release-gate.l15.json"],
            "untracked_paths": [
                "dist/alpha-release-gate.l15.preflight.json",
                "README.md",
            ],
        },
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_branch",
        lambda _root: "codex/qa-z-bootstrap",
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_head",
        lambda _root: "1234567890abcdef1234567890abcdef12345678",
    )

    signals = collect_live_repository_signals(tmp_path)
    summary = live_repository_summary(signals)

    assert signals["release_evidence_paths"] == [
        "dist/alpha-release-gate.l15.json",
        "dist/alpha-release-gate.l15.preflight.json",
    ]
    assert signals["current_branch"] == "codex/qa-z-bootstrap"
    assert signals["current_head"] == "1234567890abcdef1234567890abcdef12345678"
    assert summary["release_evidence_count"] == 2
    assert summary["current_branch"] == "codex/qa-z-bootstrap"
    assert summary["current_head"] == "1234567890abcdef1234567890abcdef12345678"
    assert "release_evidence=2" in render_live_repository_summary(summary)
    assert "branch=codex/qa-z-bootstrap" in render_live_repository_summary(summary)
    assert (
        "head=1234567890abcdef1234567890abcdef12345678"
        in render_live_repository_summary(summary)
    )


def test_live_repository_treats_results_snapshot_roots_as_benchmark_results(
    tmp_path: Path, monkeypatch
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    write_generated_evidence_policy(tmp_path)
    snapshot_path = tmp_path / "benchmarks" / "results-l30-policy" / "summary.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "qa_z.live_repository.git_worktree_snapshot",
        lambda _root: {
            "modified_count": 0,
            "untracked_count": 1,
            "staged_count": 0,
            "modified_paths": [],
            "untracked_paths": ["benchmarks/results-l30-policy/summary.json"],
        },
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_branch",
        lambda _root: "codex/qa-z-bootstrap",
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_head",
        lambda _root: "1234567890abcdef1234567890abcdef12345678",
    )

    signals = collect_live_repository_signals(tmp_path)
    summary = live_repository_summary(signals)

    assert signals["runtime_artifact_paths"] == []
    assert signals["benchmark_result_paths"] == [
        "benchmarks/results-l30-policy/summary.json"
    ]
    assert summary["runtime_artifact_count"] == 0
    assert summary["benchmark_result_count"] == 1
    assert summary["dirty_benchmark_result_count"] == 1


def test_live_repository_treats_nested_results_files_as_benchmark_results(
    tmp_path: Path, monkeypatch
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    write_generated_evidence_policy(tmp_path)
    snapshot_path = tmp_path / "benchmarks" / "results" / "custom.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "qa_z.live_repository.git_worktree_snapshot",
        lambda _root: {
            "modified_count": 0,
            "untracked_count": 1,
            "staged_count": 0,
            "modified_paths": [],
            "untracked_paths": ["benchmarks/results/custom.json"],
        },
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_branch",
        lambda _root: "codex/qa-z-bootstrap",
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_head",
        lambda _root: "1234567890abcdef1234567890abcdef12345678",
    )

    signals = collect_live_repository_signals(tmp_path)
    summary = live_repository_summary(signals)

    assert signals["runtime_artifact_paths"] == []
    assert signals["benchmark_result_paths"] == ["benchmarks/results/custom.json"]
    assert summary["runtime_artifact_count"] == 0
    assert summary["benchmark_result_count"] == 1
    assert summary["dirty_benchmark_result_count"] == 1


def test_live_repository_summary_counts_dirty_benchmark_paths_in_benchmark_area(
    tmp_path: Path, monkeypatch
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    write_generated_evidence_policy(tmp_path)
    snapshot_path = tmp_path / "benchmarks" / "results-l32-policy" / "summary.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "qa_z.live_repository.git_worktree_snapshot",
        lambda _root: {
            "modified_count": 0,
            "untracked_count": 1,
            "staged_count": 0,
            "modified_paths": [],
            "untracked_paths": ["benchmarks/results-l32-policy/summary.json"],
        },
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_branch",
        lambda _root: "codex/qa-z-bootstrap",
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_head",
        lambda _root: "1234567890abcdef1234567890abcdef12345678",
    )

    signals = collect_live_repository_signals(tmp_path)
    summary = live_repository_summary(signals)

    assert summary["dirty_area_summary"] == "benchmark:1"


def test_self_inspection_skips_cleanup_gap_for_policy_explicit_results_snapshot_root(
    tmp_path: Path, monkeypatch
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    write_generated_evidence_policy(tmp_path)
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Generated benchmark snapshots are local by default under the generated
        versus frozen evidence policy and should not reopen cleanup work by
        themselves.
        """,
    )
    snapshot_path = tmp_path / "benchmarks" / "results-l30-policy" / "summary.json"
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    snapshot_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "qa_z.live_repository.git_worktree_snapshot",
        lambda _root: {
            "modified_count": 0,
            "untracked_count": 1,
            "staged_count": 0,
            "modified_paths": [],
            "untracked_paths": ["benchmarks/results-l30-policy/summary.json"],
        },
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_branch",
        lambda _root: "codex/qa-z-bootstrap",
    )
    monkeypatch.setattr(
        "qa_z.live_repository.git_current_head",
        lambda _root: "1234567890abcdef1234567890abcdef12345678",
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="snapshot-root-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "artifact_hygiene_gap" not in categories
    assert "runtime_artifact_cleanup_gap" not in categories
    assert "evidence_freshness_gap" not in categories


def test_render_live_repository_summary_marks_detached_head() -> None:
    summary = {
        "modified_count": 1,
        "untracked_count": 0,
        "staged_count": 0,
        "runtime_artifact_count": 0,
        "benchmark_result_count": 0,
        "dirty_benchmark_result_count": 0,
        "release_evidence_count": 0,
        "generated_artifact_policy_explicit": True,
        "current_branch": "HEAD",
        "current_head": "1234567890abcdef1234567890abcdef12345678",
        "dirty_area_summary": "source:1",
    }

    rendered = render_live_repository_summary(summary)

    assert "branch=detached" in rendered
    assert "branch=HEAD" not in rendered
    assert "head=1234567890abcdef1234567890abcdef12345678" in rendered


def test_self_inspection_promotes_policy_gap_when_doc_is_missing(
    tmp_path: Path,
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Generated versus frozen evidence policy still needs one explicit source
        of truth for benchmark outputs and runtime result storage.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="missing-policy-doc")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    candidate = next(
        item
        for item in report["candidates"]
        if item["category"] == "evidence_freshness_gap"
    )

    assert candidate["recommendation"] == "clarify_generated_vs_frozen_evidence_policy"
    assert any(
        entry["source"] == "generated_artifact_policy"
        and "policy document is missing" in entry["summary"]
        for entry in candidate["evidence"]
    )


def test_self_inspection_skips_stale_artifact_policy_gaps_when_gitignore_is_explicit(
    tmp_path: Path, monkeypatch
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    stub_live_repository_signals(
        monkeypatch,
        modified_count=1,
        untracked_count=1,
        staged_count=0,
        modified_paths=["README.md"],
        untracked_paths=["docs/reports/worktree-triage.md"],
        runtime_artifact_paths=[],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
        generated_artifact_policy_explicit=True,
    )
    write_report(
        tmp_path,
        "worktree-triage.md",
        """
        # QA-Z Worktree Triage

        Runtime artifacts are still mixed with source-like areas and the generated
        benchmark outputs need a clearer cleanup policy.
        """,
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Frozen evidence versus runtime result storage is still ambiguous in the
        current worktree, especially for benchmark outputs.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="explicit-ignore-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "artifact_hygiene_gap" not in categories
    assert "evidence_freshness_gap" not in categories
    assert "runtime_artifact_cleanup_gap" not in categories


def test_self_inspection_skips_policy_gaps_when_policy_doc_and_gitignore_are_explicit(
    tmp_path: Path,
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    write_generated_evidence_policy(tmp_path)
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        Frozen evidence versus runtime result storage was historically ambiguous
        in the current worktree, especially for benchmark outputs.
        """,
    )

    paths = run_self_inspection(root=tmp_path, now=NOW, loop_id="explicit-policy-loop")
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "artifact_hygiene_gap" not in categories
    assert "evidence_freshness_gap" not in categories
    assert "runtime_artifact_cleanup_gap" not in categories


def test_self_inspection_keeps_cleanup_work_but_skips_policy_gap_when_policy_is_explicit(
    tmp_path: Path, monkeypatch
) -> None:
    write_generated_artifact_gitignore(tmp_path)
    write_generated_evidence_policy(tmp_path)
    stub_live_repository_signals(
        monkeypatch,
        modified_count=0,
        untracked_count=2,
        staged_count=0,
        modified_paths=[],
        untracked_paths=[
            ".qa-z/loops/latest/outcome.json",
            "benchmarks/results-analysis/report.md",
        ],
        runtime_artifact_paths=[
            ".qa-z/loops/latest/outcome.json",
            "benchmarks/results-analysis/report.md",
        ],
        benchmark_result_paths=[
            "benchmarks/results/summary.json",
            "benchmarks/results/report.md",
        ],
        generated_artifact_policy_explicit=True,
    )
    write_report(
        tmp_path,
        "current-state-analysis.md",
        """
        # QA-Z Current State Analysis

        The generated versus frozen evidence policy is explicit, but local runtime
        artifacts still need cleanup before source integration.
        """,
    )

    paths = run_self_inspection(
        root=tmp_path, now=NOW, loop_id="explicit-runtime-artifacts"
    )
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    backlog = json.loads(paths.backlog_path.read_text(encoding="utf-8"))
    categories = {item["category"] for item in report["candidates"]}

    assert "artifact_hygiene_gap" in categories
    assert "runtime_artifact_cleanup_gap" in categories
    assert "evidence_freshness_gap" not in categories
    assert [item["id"] for item in backlog["items"][:2]] == [
        "runtime_artifact_cleanup_gap-generated-results",
        "artifact_hygiene_gap-runtime-source-separation",
    ]

    selected_paths = select_next_tasks(
        root=tmp_path,
        count=1,
        now=NOW,
        loop_id="explicit-runtime-artifacts-selection",
    )
    selected = json.loads(
        selected_paths.selected_tasks_path.read_text(encoding="utf-8")
    )
    assert [item["id"] for item in selected["selected_tasks"]] == [
        "runtime_artifact_cleanup_gap-generated-results"
    ]
