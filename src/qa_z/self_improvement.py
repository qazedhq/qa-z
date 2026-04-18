"""Artifact-driven self-inspection and backlog selection for QA-Z."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SELF_INSPECTION_KIND = "qa_z.self_inspection"
BACKLOG_KIND = "qa_z.improvement_backlog"
SELECTED_TASKS_KIND = "qa_z.selected_tasks"
LOOP_HISTORY_KIND = "qa_z.loop_history_entry"

SELF_INSPECTION_SCHEMA_VERSION = 1
BACKLOG_SCHEMA_VERSION = 1
SELECTED_TASKS_SCHEMA_VERSION = 1
LOOP_HISTORY_SCHEMA_VERSION = 1

BENCHMARK_SUMMARY_PATH = Path("benchmarks/results/summary.json")
LATEST_LOOP_DIR = Path(".qa-z/loops/latest")
BACKLOG_PATH = Path(".qa-z/improvement/backlog.json")
LOOP_HISTORY_PATH = Path(".qa-z/loops/history.jsonl")


@dataclass(frozen=True)
class BacklogCandidate:
    """A deterministic improvement candidate derived from local artifacts."""

    id: str
    title: str
    category: str
    recommendation: str
    evidence: list[dict[str, Any]]
    signals: dict[str, Any]
    impact: int = 3
    likelihood: int = 3
    confidence: int = 3
    repair_cost: int = 2


@dataclass(frozen=True)
class SelfInspectionArtifactPaths:
    """Files written by ``qa-z self-inspect``."""

    self_inspection_path: Path
    backlog_path: Path


@dataclass(frozen=True)
class SelectionArtifactPaths:
    """Files written by ``qa-z select-next``."""

    selected_tasks_path: Path
    loop_plan_path: Path
    history_path: Path


def run_self_inspection(
    *, root: Path, loop_id: str | None = None, generated_at: str | None = None
) -> SelfInspectionArtifactPaths:
    """Inspect deterministic artifacts and merge findings into a backlog."""
    project_root = root.resolve()
    generated = generated_at or utc_now()
    current_loop = loop_id or default_loop_id(generated)
    candidates = discover_candidates(project_root)
    existing_backlog = load_backlog(project_root)
    backlog = merge_backlog(
        existing_backlog,
        candidates,
        generated_at=generated,
    )

    latest_dir = project_root / LATEST_LOOP_DIR
    latest_dir.mkdir(parents=True, exist_ok=True)
    backlog_path = project_root / BACKLOG_PATH
    backlog_path.parent.mkdir(parents=True, exist_ok=True)

    report = {
        "kind": SELF_INSPECTION_KIND,
        "schema_version": SELF_INSPECTION_SCHEMA_VERSION,
        "generated_at": generated,
        "loop_id": current_loop,
        "artifact_only": True,
        "candidates_total": len(candidates),
        "candidates": [candidate_json(candidate) for candidate in candidates],
        "evidence_sources": evidence_sources(candidates),
        "backlog_path": BACKLOG_PATH.as_posix(),
        "summary": {
            "open_backlog_items": len(open_backlog_items(backlog)),
            "new_or_reobserved_candidates": len(candidates),
        },
    }

    self_inspection_path = latest_dir / "self_inspect.json"
    write_json(self_inspection_path, report)
    write_json(backlog_path, backlog)
    return SelfInspectionArtifactPaths(
        self_inspection_path=self_inspection_path,
        backlog_path=backlog_path,
    )


def select_next_tasks(
    *,
    root: Path,
    count: int = 1,
    loop_id: str | None = None,
    generated_at: str | None = None,
) -> SelectionArtifactPaths:
    """Select the highest-priority open backlog items and write loop artifacts."""
    project_root = root.resolve()
    generated = generated_at or utc_now()
    current_loop = loop_id or default_loop_id(generated)
    limit = max(1, min(int_value(count, default=1), 3))
    backlog = load_backlog(project_root)
    ranked = sorted(
        open_backlog_items(backlog),
        key=lambda item: (
            -int_value(item.get("priority_score"), default=0),
            str(item.get("category") or ""),
            str(item.get("id") or ""),
        ),
    )
    selected = [
        selected_task_json(item, index + 1) for index, item in enumerate(ranked[:limit])
    ]

    latest_dir = project_root / LATEST_LOOP_DIR
    latest_dir.mkdir(parents=True, exist_ok=True)
    history_path = project_root / LOOP_HISTORY_PATH
    history_path.parent.mkdir(parents=True, exist_ok=True)

    selected_payload = {
        "kind": SELECTED_TASKS_KIND,
        "schema_version": SELECTED_TASKS_SCHEMA_VERSION,
        "generated_at": generated,
        "loop_id": current_loop,
        "selection_limit": limit,
        "selected_count": len(selected),
        "selected_tasks": selected,
        "artifact_only": True,
    }
    selected_path = latest_dir / "selected_tasks.json"
    loop_plan_path = latest_dir / "loop_plan.md"
    write_json(selected_path, selected_payload)
    loop_plan_path.write_text(
        render_loop_plan(selected_payload, root=project_root), encoding="utf-8"
    )

    history_entry = {
        "kind": LOOP_HISTORY_KIND,
        "schema_version": LOOP_HISTORY_SCHEMA_VERSION,
        "generated_at": generated,
        "loop_id": current_loop,
        "selected_task_ids": [task["id"] for task in selected],
        "selected_categories": [task["category"] for task in selected],
        "evidence_used": evidence_paths(selected),
        "selected_tasks_path": (LATEST_LOOP_DIR / "selected_tasks.json").as_posix(),
        "loop_plan_path": (LATEST_LOOP_DIR / "loop_plan.md").as_posix(),
    }
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(history_entry, sort_keys=True) + "\n")

    return SelectionArtifactPaths(
        selected_tasks_path=selected_path,
        loop_plan_path=loop_plan_path,
        history_path=history_path,
    )


def discover_candidates(root: Path) -> list[BacklogCandidate]:
    """Discover improvement candidates from deterministic local evidence."""
    candidates: list[BacklogCandidate] = []
    candidates.extend(discover_benchmark_candidates(root))
    candidates.extend(discover_verification_candidates(root))
    candidates.extend(discover_artifact_consistency_candidates(root))
    candidates.extend(discover_docs_drift_candidates(root))
    return unique_candidates(candidates)


def discover_benchmark_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates for failed benchmark summary evidence."""
    summary_path = root / BENCHMARK_SUMMARY_PATH
    summary = read_json_object(summary_path)
    if summary is None:
        return []

    failed_fixtures = [str(name) for name in summary.get("failed_fixtures") or []]
    fixture_details = {
        str(fixture.get("name")): fixture
        for fixture in summary.get("fixtures", [])
        if isinstance(fixture, dict) and fixture.get("name")
    }
    if not failed_fixtures:
        failed_fixtures = [
            name
            for name, fixture in fixture_details.items()
            if fixture.get("passed") is False
        ]

    snapshot = benchmark_summary_snapshot(summary)
    candidates = []
    for fixture_name in failed_fixtures:
        fixture = fixture_details.get(fixture_name, {})
        failures = [str(value) for value in fixture.get("failures", [])]
        categories = [str(value) for value in fixture.get("categories", [])]
        failure_summary = (
            "; ".join(failures[:2])
            or "benchmark expectation did not match observed artifacts"
        )
        candidates.append(
            BacklogCandidate(
                id=f"benchmark-fixture-{slugify(fixture_name)}",
                title=f"Repair benchmark fixture {fixture_name}",
                category="benchmark_failure",
                recommendation="add_benchmark_fixture",
                evidence=[
                    {
                        "source": "benchmark_summary",
                        "path": BENCHMARK_SUMMARY_PATH.as_posix(),
                        "summary": f"{fixture_name}: {failure_summary}",
                        "snapshot": snapshot,
                        "categories": categories,
                    }
                ],
                signals={
                    "failed_benchmark_fixture": True,
                    "fixture": fixture_name,
                    "snapshot": snapshot,
                },
                impact=4,
                likelihood=4,
                confidence=4,
                repair_cost=2,
            )
        )
    failed_count = int_value(summary.get("fixtures_failed"), default=0)
    if failed_count > 0 and not candidates:
        candidates.append(
            BacklogCandidate(
                id="benchmark-summary-failures",
                title="Repair failing benchmark summary evidence",
                category="benchmark_failure",
                recommendation="add_benchmark_fixture",
                evidence=[
                    {
                        "source": "benchmark_summary",
                        "path": BENCHMARK_SUMMARY_PATH.as_posix(),
                        "summary": f"{failed_count} benchmark fixture(s) failed without per-fixture names",
                        "snapshot": snapshot,
                    }
                ],
                signals={
                    "benchmark_summary_failure": True,
                    "failed_count": failed_count,
                    "snapshot": snapshot,
                },
                impact=4,
                likelihood=4,
                confidence=3,
                repair_cost=2,
            )
        )
    return candidates


def discover_verification_candidates(root: Path) -> list[BacklogCandidate]:
    """Create candidates from regressed or incomplete verification artifacts."""
    candidates: list[BacklogCandidate] = []
    for summary_path in sorted(
        (root / ".qa-z" / "runs").glob("**/verify/summary.json")
    ):
        summary = read_json_object(summary_path)
        if summary is None:
            continue
        verdict = str(summary.get("verdict") or "")
        if verdict not in {"mixed", "regressed", "unchanged", "verification_failed"}:
            continue
        regression_count = int_value(summary.get("regression_count"), default=0)
        new_issue_count = int_value(summary.get("new_issue_count"), default=0)
        remaining_count = int_value(summary.get("remaining_issue_count"), default=0)
        if (
            verdict == "unchanged"
            and regression_count + new_issue_count + remaining_count == 0
        ):
            continue
        relative_path = relative_to_root(summary_path, root)
        run_id = verification_run_id(summary_path, root)
        candidates.append(
            BacklogCandidate(
                id=f"verification-{slugify(run_id)}-{slugify(verdict)}",
                title=f"Repair verification {verdict} evidence for {run_id}",
                category="verification_regression",
                recommendation="repair_verification_regression",
                evidence=[
                    {
                        "source": "verify_summary",
                        "path": relative_path,
                        "summary": (
                            f"verdict={verdict}; remaining={remaining_count}; "
                            f"new={new_issue_count}; regressions={regression_count}"
                        ),
                    }
                ],
                signals={
                    "verification_regression": verdict in {"mixed", "regressed"}
                    or regression_count > 0,
                    "verdict": verdict,
                    "remaining_issue_count": remaining_count,
                    "new_issue_count": new_issue_count,
                    "regression_count": regression_count,
                },
                impact=4 if verdict in {"mixed", "regressed"} else 3,
                likelihood=4,
                confidence=4,
                repair_cost=3,
            )
        )
    return candidates


def discover_artifact_consistency_candidates(root: Path) -> list[BacklogCandidate]:
    """Detect narrow docs/schema mismatches around self-improvement artifacts."""
    schema_path = root / "docs" / "artifact-schema-v1.md"
    readme_path = root / "README.md"
    schema_text = read_text(schema_path)
    readme_text = read_text(readme_path)
    if not schema_text or not readme_text:
        return []
    readme_mentions = "self-inspect" in readme_text and "select-next" in readme_text
    schema_mentions = (
        "self_inspect.json" in schema_text and "selected_tasks.json" in schema_text
    )
    if readme_mentions == schema_mentions:
        return []
    return [
        BacklogCandidate(
            id="self-improvement-artifact-docs-drift",
            title="Sync self-improvement command docs with artifact schema",
            category="artifact_schema_gap",
            recommendation="sync_contract_and_docs",
            evidence=[
                {
                    "source": "artifact_schema",
                    "path": "docs/artifact-schema-v1.md",
                    "summary": "README and artifact schema disagree on self-improvement artifacts",
                }
            ],
            signals={"artifact_schema_gap": True},
            impact=3,
            likelihood=3,
            confidence=3,
            repair_cost=2,
        )
    ]


def discover_docs_drift_candidates(root: Path) -> list[BacklogCandidate]:
    """Detect implemented CLI commands that are missing from public README text."""
    cli_path = root / "src" / "qa_z" / "cli.py"
    readme_path = root / "README.md"
    cli_text = read_text(cli_path)
    readme_text = read_text(readme_path)
    if not cli_text or not readme_text:
        return []
    if "self-inspect" in cli_text and "self-inspect" not in readme_text:
        return [
            BacklogCandidate(
                id="readme-self-improvement-command-drift",
                title="Document self-improvement CLI commands in README",
                category="docs_drift",
                recommendation="sync_contract_and_docs",
                evidence=[
                    {
                        "source": "readme",
                        "path": "README.md",
                        "summary": "CLI has self-improvement commands not documented in README",
                    }
                ],
                signals={"docs_drift": True},
                impact=3,
                likelihood=3,
                confidence=3,
                repair_cost=1,
            )
        ]
    return []


def merge_backlog(
    existing_backlog: dict[str, Any],
    candidates: list[BacklogCandidate],
    *,
    generated_at: str,
) -> dict[str, Any]:
    """Merge observed candidates into a stable backlog document."""
    existing_items = {
        str(item.get("id")): item
        for item in existing_backlog.get("items", [])
        if isinstance(item, dict) and item.get("id")
    }
    observed_ids = {candidate.id for candidate in candidates}
    items: list[dict[str, Any]] = []

    for candidate in candidates:
        old_item = existing_items.get(candidate.id)
        recurrence = 1
        first_seen = generated_at
        status = "open"
        if old_item:
            recurrence = int_value(old_item.get("recurrence_count"), default=1) + 1
            first_seen = str(old_item.get("first_seen_at") or generated_at)
            old_status = str(old_item.get("status") or "open")
            status = old_status if old_status == "in_progress" else "open"
        item = backlog_item_from_candidate(
            candidate,
            generated_at=generated_at,
            first_seen_at=first_seen,
            recurrence_count=recurrence,
            status=status,
            old_item=old_item,
        )
        items.append(item)

    for item_id, old_item in existing_items.items():
        if item_id in observed_ids:
            continue
        stale = dict(old_item)
        status = str(stale.get("status") or "open")
        if status in {"open", "selected"}:
            stale["status"] = "closed"
            stale["closed_at"] = generated_at
            stale["closure_reason"] = "not_reobserved"
        items.append(stale)

    items.sort(
        key=lambda item: (
            str(item.get("status") == "closed"),
            -int_value(item.get("priority_score"), default=0),
            str(item.get("category") or ""),
            str(item.get("id") or ""),
        )
    )
    return {
        "kind": BACKLOG_KIND,
        "schema_version": BACKLOG_SCHEMA_VERSION,
        "generated_at": generated_at,
        "items": items,
        "summary": {
            "total_items": len(items),
            "open_items": len([item for item in items if item.get("status") == "open"]),
            "closed_items": len(
                [item for item in items if item.get("status") == "closed"]
            ),
        },
    }


def backlog_item_from_candidate(
    candidate: BacklogCandidate,
    *,
    generated_at: str,
    first_seen_at: str,
    recurrence_count: int,
    status: str,
    old_item: dict[str, Any] | None,
) -> dict[str, Any]:
    """Render a candidate as a backlog item."""
    priority_score = score_candidate(
        candidate, old_item=old_item, recurrence_count=recurrence_count
    )
    return {
        "id": candidate.id,
        "title": candidate.title,
        "category": candidate.category,
        "recommendation": candidate.recommendation,
        "status": status,
        "first_seen_at": first_seen_at,
        "last_seen_at": generated_at,
        "recurrence_count": recurrence_count,
        "priority_score": priority_score,
        "priority_components": {
            "impact": candidate.impact,
            "likelihood": candidate.likelihood,
            "confidence": candidate.confidence,
            "repair_cost": candidate.repair_cost,
            "recurrence_count": recurrence_count,
        },
        "signals": dict(candidate.signals),
        "evidence": list(candidate.evidence),
    }


def score_candidate(
    candidate: BacklogCandidate,
    *,
    old_item: dict[str, Any] | None = None,
    recurrence_count: int | None = None,
) -> int:
    """Score a candidate using grounded impact, likelihood, confidence, and cost."""
    score = candidate.impact * candidate.likelihood * candidate.confidence
    score -= candidate.repair_cost
    signals = candidate.signals
    if signals.get("verification_regression"):
        score += 25
    if signals.get("failed_benchmark_fixture"):
        score += 20
    if signals.get("benchmark_summary_failure"):
        score += 18
    if signals.get("artifact_schema_gap"):
        score += 10
    if signals.get("docs_drift"):
        score += 8
    recurrence = recurrence_count
    if recurrence is None and old_item is not None:
        recurrence = int_value(old_item.get("recurrence_count"), default=1)
    if recurrence is None:
        recurrence = int_value(signals.get("recurrence_count"), default=1)
    if recurrence > 1:
        score += min((recurrence - 1) * 3, 15)
    return score


def candidate_json(candidate: BacklogCandidate) -> dict[str, Any]:
    """Render a candidate for the self-inspection report."""
    return {
        "id": candidate.id,
        "title": candidate.title,
        "category": candidate.category,
        "recommendation": candidate.recommendation,
        "priority_score": score_candidate(candidate),
        "priority_components": {
            "impact": candidate.impact,
            "likelihood": candidate.likelihood,
            "confidence": candidate.confidence,
            "repair_cost": candidate.repair_cost,
        },
        "signals": dict(candidate.signals),
        "evidence": list(candidate.evidence),
    }


def selected_task_json(item: dict[str, Any], rank: int) -> dict[str, Any]:
    """Render a backlog item in selected-task artifact shape."""
    task = {
        "rank": rank,
        "id": str(item.get("id") or ""),
        "title": str(item.get("title") or "Untitled backlog item"),
        "category": str(item.get("category") or "unknown"),
        "recommendation": str(item.get("recommendation") or "inspect_evidence"),
        "priority_score": int_value(item.get("priority_score"), default=0),
        "recurrence_count": int_value(item.get("recurrence_count"), default=1),
        "evidence": list(item.get("evidence") or []),
        "signals": dict(item.get("signals") or {}),
    }
    task["action_hint"] = selected_task_action_hint(task)
    task["validation_command"] = selected_task_validation_command(task)
    task["compact_evidence"] = compact_backlog_evidence_summary(task)
    return task


def render_loop_plan(selected_payload: dict[str, Any], *, root: Path) -> str:
    """Render a Markdown loop plan from selected tasks."""
    lines = [
        "# QA-Z Loop Plan",
        "",
        f"Loop: {selected_payload.get('loop_id')}",
        "",
        "This plan is artifact-only. It prepares deterministic next work and does not edit code autonomously.",
        "",
    ]
    selected = list(selected_payload.get("selected_tasks") or [])
    if not selected:
        lines.extend(
            [
                "## Selected Tasks",
                "",
                "No open backlog items were available.",
            ]
        )
        return "\n".join(lines).rstrip() + "\n"

    lines.append("## Selected Tasks")
    lines.append("")
    for task in selected:
        evidence = compact_backlog_evidence_summary(task)
        lines.extend(
            [
                f"### {task.get('rank')}. {task.get('title')}",
                "",
                f"- Backlog id: `{task.get('id')}`",
                f"- Category: `{task.get('category')}`",
                f"- Recommendation: `{task.get('recommendation')}`",
                f"- Priority score: {task.get('priority_score')}",
                f"- Action: {selected_task_action_hint(task)}",
                f"- Validation: `{selected_task_validation_command(task)}`",
                f"- Evidence: {evidence}",
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"


def selected_task_action_hint(task: dict[str, Any]) -> str:
    """Return a compact action hint for human or agent planning."""
    recommendation = str(task.get("recommendation") or "")
    category = str(task.get("category") or "")
    if recommendation == "add_benchmark_fixture" or category == "benchmark_failure":
        return "repair the benchmark expectation or add deterministic fixture coverage"
    if (
        recommendation == "repair_verification_regression"
        or category == "verification_regression"
    ):
        return "inspect verification comparison evidence and repair the regressed check"
    if recommendation == "sync_contract_and_docs":
        return "sync the public docs and artifact schema with implemented behavior"
    return (
        "inspect the cited artifact evidence and make the smallest deterministic repair"
    )


def selected_task_validation_command(task: dict[str, Any]) -> str:
    """Return the strongest local validation command for a selected task."""
    recommendation = str(task.get("recommendation") or "")
    category = str(task.get("category") or "")
    if recommendation == "add_benchmark_fixture" or category == "benchmark_failure":
        return "python -m qa_z benchmark --json"
    if (
        recommendation == "repair_verification_regression"
        or category == "verification_regression"
    ):
        return "python -m pytest tests/test_self_improvement.py tests/test_cli.py -q"
    if recommendation == "sync_contract_and_docs":
        return "python -m pytest tests/test_artifact_schema.py tests/test_cli.py -q"
    return "python -m pytest"


def compact_backlog_evidence_summary(item: dict[str, Any]) -> str:
    """Return one readable evidence summary for CLI and loop-plan output."""
    evidence = list(item.get("evidence") or [])
    if not evidence:
        return "no evidence paths recorded"
    best = sorted(evidence, key=compact_evidence_priority)[0]
    return compact_evidence_entry(best)


def compact_evidence_priority(entry: dict[str, Any]) -> tuple[int, str]:
    """Rank evidence entries for concise display."""
    source = str(entry.get("source") or "")
    priorities = {
        "benchmark_summary": 0,
        "verify_summary": 1,
        "artifact_schema": 2,
        "readme": 3,
    }
    return (priorities.get(source, 20), str(entry.get("path") or ""))


def compact_evidence_entry(entry: dict[str, Any]) -> str:
    """Render a single evidence entry."""
    source = str(entry.get("source") or "artifact")
    path = str(entry.get("path") or "unknown path")
    summary = str(entry.get("summary") or entry.get("snapshot") or "evidence recorded")
    snapshot = str(entry.get("snapshot") or "")
    if snapshot and snapshot not in summary:
        summary = f"{summary}; {snapshot}"
    return f"{source} at {path}: {summary}"


def evidence_sources(candidates: list[BacklogCandidate]) -> list[dict[str, Any]]:
    """Return unique evidence source/path pairs from candidates."""
    seen: set[tuple[str, str]] = set()
    sources: list[dict[str, Any]] = []
    for candidate in candidates:
        for entry in candidate.evidence:
            key = (str(entry.get("source") or ""), str(entry.get("path") or ""))
            if key in seen:
                continue
            seen.add(key)
            sources.append({"source": key[0], "path": key[1]})
    return sources


def evidence_paths(items: list[dict[str, Any]]) -> list[str]:
    """Return unique evidence paths from selected task-like dictionaries."""
    paths: list[str] = []
    for item in items:
        for entry in item.get("evidence", []) or []:
            path = str(entry.get("path") or "")
            if path and path not in paths:
                paths.append(path)
    return paths


def load_backlog(root_or_path: Path) -> dict[str, Any]:
    """Load the backlog, returning a deterministic empty shape when absent."""
    path = root_or_path
    if path.is_dir() or not path.name.endswith(".json"):
        path = path / BACKLOG_PATH
    backlog = read_json_object(path)
    if backlog is None:
        return empty_backlog()
    items = backlog.get("items")
    if not isinstance(items, list):
        backlog["items"] = []
    return backlog


def empty_backlog() -> dict[str, Any]:
    """Return an empty backlog artifact."""
    return {
        "kind": BACKLOG_KIND,
        "schema_version": BACKLOG_SCHEMA_VERSION,
        "items": [],
        "summary": {"total_items": 0, "open_items": 0, "closed_items": 0},
    }


def open_backlog_items(backlog: dict[str, Any]) -> list[dict[str, Any]]:
    """Return open backlog items."""
    return [
        item
        for item in backlog.get("items", [])
        if isinstance(item, dict) and str(item.get("status") or "open") == "open"
    ]


def benchmark_summary_snapshot(summary: dict[str, Any]) -> str:
    """Return a compact benchmark snapshot from current or legacy summaries."""
    explicit = summary.get("snapshot")
    if explicit:
        return str(explicit)
    total = int_value(summary.get("fixtures_total"), default=0)
    passed = int_value(summary.get("fixtures_passed"), default=0)
    rate = summary.get("overall_rate")
    if rate is None and total:
        rate = round(passed / total, 4)
    if rate is None:
        rate = 0.0
    return f"{passed}/{total} fixtures, overall_rate {rate}"


def unique_candidates(candidates: list[BacklogCandidate]) -> list[BacklogCandidate]:
    """Deduplicate candidates by stable id."""
    seen: set[str] = set()
    unique: list[BacklogCandidate] = []
    for candidate in candidates:
        if candidate.id in seen:
            continue
        seen.add(candidate.id)
        unique.append(candidate)
    return unique


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write deterministic JSON with a trailing newline."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def read_json_object(path: Path) -> dict[str, Any] | None:
    """Read an optional JSON object, ignoring missing or malformed optional evidence."""
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return value if isinstance(value, dict) else None


def read_text(path: Path) -> str:
    """Read optional text evidence."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def relative_to_root(path: Path, root: Path) -> str:
    """Render a path relative to the repository root when possible."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def verification_run_id(summary_path: Path, root: Path) -> str:
    """Extract the run id from a verification summary path."""
    relative = summary_path.relative_to(root)
    parts = relative.parts
    if len(parts) >= 4 and parts[0] == ".qa-z" and parts[1] == "runs":
        return parts[2]
    return summary_path.parent.parent.name


def slugify(value: str) -> str:
    """Render a stable identifier fragment."""
    slug = re.sub(r"[^A-Za-z0-9]+", "-", value.strip().lower()).strip("-")
    return slug or "item"


def int_value(value: Any, *, default: int = 0) -> int:
    """Convert loosely typed artifact numbers to int."""
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def utc_now() -> str:
    """Return an ISO-8601 UTC timestamp without microseconds."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def default_loop_id(generated_at: str) -> str:
    """Return a stable loop id derived from a timestamp-like string."""
    safe = re.sub(r"[^0-9A-Za-z]+", "", generated_at.replace("+00:00", "Z"))
    return f"loop-{safe[:15] or 'local'}"
