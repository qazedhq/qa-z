"""Local evidence summary navigator for QA-Z run artifacts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from qa_z.artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    RunSource,
    fast_runs_dir,
    format_path,
    latest_run_manifest_path,
    load_run_summary,
    resolve_manifest_run_source,
    resolve_run_source,
)
from qa_z.reporters.deep_context import build_deep_context, load_sibling_deep_summary
from qa_z.runners.models import CheckResult, RunSummary

SUMMARY_SCHEMA_VERSION = 1


def build_evidence_summary(
    *,
    root: Path,
    config: dict[str, Any],
    from_run: str | None = "latest",
) -> dict[str, Any]:
    """Build a stable local summary over one QA-Z run directory."""
    warnings: list[str] = []
    try:
        run_source = resolve_summary_run_source(
            root=root,
            config=config,
            from_run=from_run,
            warnings=warnings,
        )
    except (ArtifactSourceNotFound, ArtifactLoadError, FileNotFoundError) as exc:
        return missing_run_summary(root=root, from_run=from_run, message=str(exc))

    try:
        fast_summary = load_run_summary(run_source.summary_path)
    except ArtifactLoadError as exc:
        return missing_run_summary(
            root=root,
            from_run=from_run,
            message=f"Could not load fast summary: {exc}",
            status="failed",
            verdict="error",
        )

    deep_summary = None
    try:
        deep_summary = load_sibling_deep_summary(run_source)
    except ArtifactLoadError as exc:
        warnings.append(f"Deep summary could not be loaded: {exc}")

    deep_path = run_source.run_dir / "deep" / "summary.json"
    if deep_summary is None:
        warnings.append(
            "Deep summary is missing; deep checks may not have run for this evidence."
        )

    guard_verdict = load_optional_json(run_source.run_dir / "guard" / "verdict.json")
    verify_summary = load_optional_json(run_source.run_dir / "verify" / "summary.json")
    repair_prompt_path = run_source.run_dir / "repair" / "prompt.md"
    verify_report_path = run_source.run_dir / "verify" / "report.md"

    verdict = infer_verdict(
        fast_summary=fast_summary,
        deep_summary=deep_summary,
        guard_verdict=guard_verdict,
    )
    status = infer_status(
        fast_summary=fast_summary,
        deep_summary=deep_summary,
        guard_verdict=guard_verdict,
        warnings=warnings,
    )

    evidence = {
        "fast_summary": evidence_entry(
            run_source.summary_path,
            root,
            exists=True,
            status=fast_summary.status,
        ),
        "deep_summary": evidence_entry(
            deep_path,
            root,
            exists=deep_path.is_file(),
            status=deep_summary.status if deep_summary else "missing",
        ),
        "review_packet": evidence_entry(
            run_source.run_dir / "review" / "review.md",
            root,
            exists=(run_source.run_dir / "review" / "review.md").is_file(),
        ),
        "github_summary": evidence_entry(
            run_source.run_dir / "guard" / "github-summary.md",
            root,
            exists=(run_source.run_dir / "guard" / "github-summary.md").is_file(),
        ),
        "guard_verdict": evidence_entry(
            run_source.run_dir / "guard" / "verdict.json",
            root,
            exists=(run_source.run_dir / "guard" / "verdict.json").is_file(),
            status=string_value(guard_verdict, "status") if guard_verdict else None,
        ),
    }
    repair_prompt = evidence_entry(
        repair_prompt_path,
        root,
        exists=repair_prompt_path.is_file(),
    )
    verify_report = evidence_entry(
        verify_report_path,
        root,
        exists=verify_report_path.is_file(),
        status=string_value(verify_summary, "verdict") if verify_summary else None,
    )
    top_findings = collect_top_findings(
        fast_summary=fast_summary,
        deep_summary=deep_summary,
        limit=5,
    )
    next_actions = build_next_actions(
        verdict=verdict,
        deep_summary=deep_summary,
        repair_prompt_exists=repair_prompt_path.is_file(),
        verify_report_exists=verify_report_path.is_file(),
    )

    return {
        "kind": "qa_z.evidence_summary",
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "status": status,
        "verdict": verdict,
        "run_dir": format_path(run_source.run_dir, root),
        "evidence": evidence,
        "top_findings": top_findings,
        "repair_prompt": repair_prompt,
        "verify_report": verify_report,
        "next_actions": next_actions,
        "warnings": unique_nonempty(warnings),
    }


def resolve_summary_run_source(
    *,
    root: Path,
    config: dict[str, Any],
    from_run: str | None,
    warnings: list[str],
) -> RunSource:
    """Resolve a run source while surfacing stale latest-manifest warnings."""
    if from_run not in (None, "", "latest"):
        return resolve_run_source(root, config, from_run)

    runs_dir = fast_runs_dir(root, config)
    if not runs_dir.exists():
        raise ArtifactSourceNotFound(f"No run directory found at {runs_dir}")

    manifest_path = latest_run_manifest_path(root, config)
    if manifest_path.is_file():
        try:
            manifest_source = resolve_manifest_run_source(manifest_path, root)
        except ArtifactLoadError as exc:
            warnings.append(f"latest-run.json could not be read: {exc}")
        else:
            if manifest_source is not None:
                return manifest_source
            warnings.append(
                "latest-run.json points to a missing run; using newest fast "
                "summary found instead."
            )

    summaries = list(runs_dir.glob("*/fast/summary.json"))
    if not summaries:
        raise ArtifactSourceNotFound(f"No fast summary artifacts found in {runs_dir}")
    summary_path = max(
        summaries,
        key=lambda path: (path.stat().st_mtime, path.parent.parent.name),
    )
    return RunSource(
        run_dir=summary_path.parent.parent,
        fast_dir=summary_path.parent,
        summary_path=summary_path,
    )


def missing_run_summary(
    *,
    root: Path,
    from_run: str | None,
    message: str,
    status: str = "missing",
    verdict: str = "no_run",
) -> dict[str, Any]:
    """Return a stable summary payload when evidence cannot be resolved."""
    label = from_run or "latest"
    return {
        "kind": "qa_z.evidence_summary",
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "status": status,
        "verdict": verdict,
        "run_dir": None,
        "evidence": {
            "fast_summary": missing_entry(),
            "deep_summary": missing_entry(),
            "review_packet": missing_entry(),
            "github_summary": missing_entry(),
            "guard_verdict": missing_entry(),
        },
        "top_findings": [],
        "repair_prompt": missing_entry(),
        "verify_report": missing_entry(),
        "next_actions": [
            "qa-z guard --adapter codex --deep auto",
            "qa-z demo auth-bug",
        ],
        "warnings": [
            f"No QA-Z run evidence found for {label}. {message}",
            f"Run artifacts are expected under {format_path(root / '.qa-z' / 'runs', root)}.",
        ],
    }


def infer_status(
    *,
    fast_summary: RunSummary,
    deep_summary: RunSummary | None,
    guard_verdict: dict[str, Any] | None,
    warnings: list[str],
) -> str:
    """Infer summary status from artifact completeness and run outcomes."""
    guard_status = string_value(guard_verdict, "status") if guard_verdict else None
    if guard_status == "error" or fast_summary.status == "error":
        return "failed"
    if deep_summary is not None and deep_summary.status == "error":
        return "failed"
    if warnings:
        return "warning"
    if fast_summary.status == "failed" or (
        deep_summary is not None and deep_summary.status == "failed"
    ):
        return "failed"
    if deep_summary is not None and deep_blocking_count(deep_summary) > 0:
        return "failed"
    if guard_status == "do_not_merge":
        return "failed"
    if guard_status == "needs_review":
        return "warning"
    if fast_summary.status in {"unsupported", "warning"}:
        return "warning"
    return "passed"


def infer_verdict(
    *,
    fast_summary: RunSummary,
    deep_summary: RunSummary | None,
    guard_verdict: dict[str, Any] | None,
) -> str:
    """Infer a user-facing verdict, preferring guard verdict artifacts."""
    guard_status = string_value(guard_verdict, "status") if guard_verdict else None
    if guard_status:
        return guard_status
    if fast_summary.status == "error" or (
        deep_summary is not None and deep_summary.status == "error"
    ):
        return "error"
    if fast_summary.status == "failed":
        return "do_not_merge"
    if deep_summary is not None and deep_summary.status == "failed":
        return "do_not_merge"
    if deep_summary is not None and deep_blocking_count(deep_summary) > 0:
        return "do_not_merge"
    if fast_summary.status == "unsupported":
        return "needs_review"
    return "merge_ok"


def collect_top_findings(
    *,
    fast_summary: RunSummary,
    deep_summary: RunSummary | None,
    limit: int,
) -> list[dict[str, Any]]:
    """Collect the most useful fast/deep risks for first-read output."""
    findings: list[dict[str, Any]] = []
    for check in fast_summary.checks:
        if check.status not in {"failed", "error", "warning"}:
            continue
        findings.append(fast_check_finding(check))
        if len(findings) >= limit:
            return findings

    deep_context = build_deep_context(deep_summary)
    if deep_context is not None:
        for finding in deep_context.grouped_findings or deep_context.findings:
            findings.append(deep_check_finding(finding))
            if len(findings) >= limit:
                break
    return findings


def fast_check_finding(check: CheckResult) -> dict[str, Any]:
    """Render a failed fast check as a compact finding."""
    message = (
        check.message
        or tail_summary(check.stdout_tail)
        or tail_summary(check.stderr_tail)
        or f"{check.id} reported {check.status}."
    )
    return {
        "source": "fast",
        "id": check.id,
        "status": check.status,
        "message": first_line(message),
        "tool": check.tool,
        "path": check.target_paths[0] if check.target_paths else None,
    }


def deep_check_finding(finding: dict[str, Any]) -> dict[str, Any]:
    """Render a deep finding as a compact finding."""
    line = finding.get("line", finding.get("representative_line"))
    return {
        "source": "deep",
        "id": str(finding.get("rule_id") or "deep_finding"),
        "status": str(finding.get("severity") or "finding").lower(),
        "message": first_line(str(finding.get("message") or "Deep finding reported.")),
        "path": finding.get("path"),
        "line": line,
        "count": finding.get("count"),
    }


def build_next_actions(
    *,
    verdict: str,
    deep_summary: RunSummary | None,
    repair_prompt_exists: bool,
    verify_report_exists: bool,
) -> list[str]:
    """Build deterministic next CLI commands for the current evidence state."""
    actions: list[str] = []
    if deep_summary is None:
        actions.append("qa-z deep --from-run latest")
    if (
        verdict in {"do_not_merge", "error", "needs_review"}
        and not repair_prompt_exists
    ):
        actions.append("qa-z repair-prompt --from-run latest --adapter codex")
    if repair_prompt_exists and not verify_report_exists:
        actions.append("qa-z verify --baseline-run latest --rerun")
    if verify_report_exists:
        actions.append("qa-z review --from-run latest")
    if not actions:
        actions.append("qa-z github-summary --from-run latest")
    return actions


def evidence_entry(
    path: Path,
    root: Path,
    *,
    exists: bool,
    status: str | None = None,
) -> dict[str, Any]:
    """Render a path-bearing evidence entry."""
    entry: dict[str, Any] = {
        "path": format_path(path, root),
        "exists": exists,
    }
    if status is not None:
        entry["status"] = status
    return entry


def missing_entry() -> dict[str, Any]:
    """Return a stable missing evidence entry."""
    return {"path": None, "exists": False}


def load_optional_json(path: Path) -> dict[str, Any] | None:
    """Load optional JSON object artifacts without failing the summary command."""
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def deep_blocking_count(summary: RunSummary) -> int:
    """Return deep blocking count from check summaries."""
    return sum(int(check.blocking_findings_count or 0) for check in summary.checks)


def string_value(data: dict[str, Any] | None, key: str) -> str | None:
    """Return a stripped string field from a JSON object."""
    if not data:
        return None
    value = data.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def first_line(text: str) -> str:
    """Return one readable line from a possibly multi-line message."""
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def tail_summary(text: str) -> str:
    """Return the last useful line from command output."""
    for line in reversed(text.splitlines()):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


def unique_nonempty(values: list[str]) -> list[str]:
    """Return stable, unique, non-empty strings."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if not cleaned or cleaned in seen:
            continue
        result.append(cleaned)
        seen.add(cleaned)
    return result
