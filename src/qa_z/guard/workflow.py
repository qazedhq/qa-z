"""Workflow implementation for `qa-z guard`."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from qa_z.adapters.claude import render_claude_handoff
from qa_z.adapters.codex import render_codex_handoff
from qa_z.artifacts import (
    RunSource,
    find_latest_contract,
    format_path,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_run_source,
    write_latest_run_manifest,
)
from qa_z.guard.risk_classifier import classify_change_risk, detect_changed_files
from qa_z.guard.verdict import GuardVerdict, write_verdict_artifacts
from qa_z.improvement_state import load_backlog
from qa_z.planner.contracts import plan_contract
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.github_summary import render_github_summary
from qa_z.reporters.repair_prompt import build_repair_packet, write_repair_artifacts
from qa_z.reporters.review_packet import (
    render_run_review_packet,
    run_review_packet_json,
    write_review_artifacts,
)
from qa_z.repair_handoff import (
    build_repair_handoff,
    write_repair_handoff_artifact,
)
from qa_z.reporters.run_summary import write_run_summary_artifacts
from qa_z.reporters.sarif import write_sarif_artifact
from qa_z.runners.deep import run_deep
from qa_z.runners.fast import run_fast
from qa_z.runners.models import RunSummary
from qa_z.selection_context import latest_self_inspection_selection_context


def run_guard(
    *,
    root: Path,
    config: dict[str, Any],
    title: str | None,
    slug: str | None,
    adapter: str,
    deep_mode: str,
    github_summary: bool,
    from_run: str | None = None,
) -> GuardVerdict:
    """Run a deterministic one-command QA guard workflow."""
    run_dir = root / ".qa-z" / "runs" / "latest"
    changed_files = detect_changed_files(root)
    risk = classify_change_risk(changed_files)

    if from_run:
        run_source = resolve_run_source(root, config, from_run)
        run_dir = run_source.run_dir
        fast_summary = load_run_summary(run_source.summary_path)
        fast_exit_code = 0 if fast_summary.status in {"passed", "unsupported"} else 1
        contract_path = resolve_contract_source(root, config, summary=fast_summary)
        deep_summary = load_sibling_deep_summary(run_source)
        deep_ran = deep_summary is not None
    else:
        contract_path = ensure_contract(root, config, title=title, slug=slug)
        fast_run = run_fast(
            root=root,
            config=config,
            contract_path=contract_path,
            output_dir=run_dir,
            selection_mode="smart",
        )
        fast_summary = fast_run.summary
        fast_exit_code = fast_run.exit_code
        fast_summary_path = write_run_summary_artifacts(fast_summary, run_dir / "fast")
        write_latest_run_manifest(root, config, run_dir)
        run_source = RunSource(
            run_dir=run_dir,
            fast_dir=run_dir / "fast",
            summary_path=fast_summary_path,
        )
        deep_summary = None
        deep_ran = should_run_deep(deep_mode, risk.categories)

    if should_run_deep(deep_mode, risk.categories) and deep_summary is None:
        deep_run = run_deep(
            root=root,
            config=config,
            from_run=str(run_source.run_dir),
            selection_mode="smart",
        )
        write_run_summary_artifacts(deep_run.summary, deep_run.resolution.deep_dir)
        write_sarif_artifact(
            deep_run.summary, deep_run.resolution.deep_dir / "results.sarif"
        )
        deep_summary = deep_run.summary
        deep_ran = True

    contract = load_contract_context(contract_path, root)
    review_markdown = render_run_review_packet(
        summary=fast_summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    review_json = run_review_packet_json(
        summary=fast_summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    review_dir = run_source.run_dir / "review"
    write_review_artifacts(review_markdown, review_json, review_dir)

    current_truth = guard_current_truth_context(root)
    status, reasons = decide_status(
        fast_summary, deep_summary, current_truth=current_truth
    )
    repair_written = False
    if status == "do_not_merge":
        repair_written = write_guard_repair(
            summary=fast_summary,
            run_source=run_source,
            contract=contract,
            root=root,
            deep_summary=deep_summary,
            output_dir=run_source.run_dir / "repair",
        )

    guard_dir = run_source.run_dir / "guard"
    if github_summary:
        summary_markdown = render_github_summary(
            summary=fast_summary,
            run_source=run_source,
            root=root,
            deep_summary=deep_summary,
        )
        guard_dir.mkdir(parents=True, exist_ok=True)
        (guard_dir / "github-summary.md").write_text(summary_markdown, encoding="utf-8")

    artifacts = {
        "run_dir": format_path(run_source.run_dir, root),
        "fast_summary": format_path(run_source.summary_path, root),
        "review": format_path(run_source.run_dir / "review" / "review.md", root),
        "verdict_json": format_path(guard_dir / "verdict.json", root),
        "verdict_md": format_path(guard_dir / "verdict.md", root),
    }
    if deep_summary is not None:
        artifacts["deep_summary"] = format_path(
            run_source.run_dir / "deep" / "summary.json", root
        )
    if repair_written:
        artifacts["repair"] = format_path(
            run_source.run_dir / "repair" / "prompt.md", root
        )

    verdict = GuardVerdict(
        status=status,
        title=title,
        adapter=adapter,
        reasons=reasons,
        fast={
            "status": fast_summary.status,
            "exit_code": fast_exit_code,
            "totals": fast_summary.totals,
        },
        deep={
            "ran": deep_ran,
            "status": deep_summary.status if deep_summary else "not_run",
            "blocking_findings_count": blocking_findings_count(deep_summary),
        },
        risk={
            "changed_files": risk.changed_files,
            "categories": risk.categories,
        },
        repair={"written": repair_written},
        artifacts=artifacts,
        extra={"current_truth": current_truth} if current_truth else {},
    )
    write_verdict_artifacts(verdict, guard_dir)
    return verdict


def ensure_contract(
    root: Path, config: dict[str, Any], *, title: str | None, slug: str | None
) -> Path:
    """Use the latest contract or create a minimal guard contract."""
    try:
        return find_latest_contract(root, config)
    except FileNotFoundError:
        contract_path, _created = plan_contract(
            root=root,
            config=config,
            title=title or "QA-Z Guard",
            slug=slug or "qa-z-guard",
            overwrite=True,
        )
        return contract_path


def should_run_deep(deep_mode: str, risk_categories: list[str]) -> bool:
    if deep_mode == "always":
        return True
    if deep_mode == "never":
        return False
    return bool(risk_categories)


def decide_status(
    fast_summary: RunSummary,
    deep_summary: RunSummary | None,
    *,
    current_truth: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if fast_summary.status == "unsupported":
        return "needs_review", [
            fast_summary.message or "No supported fast checks are configured."
        ]
    if fast_summary.status == "error":
        return "error", ["Fast checks could not complete."]
    if fast_summary.status == "failed":
        reasons.append("Fast checks failed.")
    if deep_summary is not None:
        if deep_summary.status == "error":
            return "error", ["Deep checks could not complete."]
        if deep_summary.status == "failed":
            reasons.append("Deep checks failed.")
        if blocking_findings_count(deep_summary) > 0:
            reasons.append("Deep checks reported blocking findings.")
    if reasons:
        return "do_not_merge", reasons
    if current_truth and current_truth.get("status") == "stale":
        return "needs_review", [
            "Current-truth self-inspection is stale for the improvement backlog."
        ]
    return "merge_ok", ["All required guard checks passed."]


def guard_current_truth_context(root: Path) -> dict[str, Any]:
    """Return guard-facing current-truth freshness context when available."""
    backlog = load_backlog(root)
    backlog_updated_at = str(backlog.get("updated_at") or "").strip()
    context = latest_self_inspection_selection_context(
        root,
        min_generated_at=backlog_updated_at or None,
    )
    if not context:
        return {}
    current_truth: dict[str, Any] = {
        "status": (
            "stale"
            if context.get("source_self_inspection_stale_for_backlog")
            else "fresh"
        )
    }
    for key in (
        "source_self_inspection",
        "source_self_inspection_loop_id",
        "source_self_inspection_generated_at",
        "source_self_inspection_stale_for_backlog",
        "source_self_inspection_refresh_commands",
    ):
        if key in context:
            current_truth[key] = context[key]
    return current_truth


def blocking_findings_count(summary: RunSummary | None) -> int:
    if summary is None:
        return 0
    return sum(int(check.blocking_findings_count or 0) for check in summary.checks)


def write_guard_repair(
    *,
    summary: RunSummary,
    run_source: RunSource,
    contract,
    root: Path,
    deep_summary: RunSummary | None,
    output_dir: Path,
) -> bool:
    packet = build_repair_packet(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    handoff = build_repair_handoff(
        repair_packet=packet,
        summary=summary,
        run_source=run_source,
        root=root,
        deep_summary=deep_summary,
    )
    write_repair_artifacts(packet, output_dir)
    write_repair_handoff_artifact(handoff, output_dir)
    (output_dir / "repair.json").write_text(
        (output_dir / "packet.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (output_dir / "codex.md").write_text(
        render_codex_handoff(handoff), encoding="utf-8"
    )
    (output_dir / "claude.md").write_text(
        render_claude_handoff(handoff), encoding="utf-8"
    )
    return True
