from __future__ import annotations

from pathlib import Path

from qa_z.runners.models import CheckResult, RunSummary
from qa_z.verification_models import VerificationRun


def check_result(
    check_id: str,
    status: str,
    *,
    kind: str = "test",
    exit_code: int | None = None,
    findings: list[dict[str, object]] | None = None,
    grouped_findings: list[dict[str, object]] | None = None,
    blocking_findings_count: int | None = None,
    policy: dict[str, object] | None = None,
) -> CheckResult:
    return CheckResult(
        id=check_id,
        tool=check_id,
        command=[check_id],
        kind=kind,
        status=status,
        exit_code=exit_code,
        duration_ms=1,
        findings_count=(
            len(findings or grouped_findings or [])
            if findings is not None or grouped_findings is not None
            else None
        ),
        blocking_findings_count=blocking_findings_count,
        filtered_findings_count=0 if findings is not None else None,
        findings=list(findings or []),
        grouped_findings=list(grouped_findings or []),
        policy=dict(policy or {}),
    )


def run_summary(mode: str, checks: list[CheckResult], *, run_id: str) -> RunSummary:
    failed = any(check.status in {"failed", "error"} for check in checks)
    return RunSummary(
        mode=mode,
        contract_path="qa/contracts/example.md",
        project_root=str(Path("/repo")),
        status="failed" if failed else "passed",
        started_at="2026-04-14T00:00:00Z",
        finished_at="2026-04-14T00:00:01Z",
        checks=checks,
        artifact_dir=f".qa-z/runs/{run_id}/{mode}",
        schema_version=2,
    )


def verification_run(
    run_id: str,
    *,
    fast_checks: list[CheckResult],
    deep_checks: list[CheckResult] | None = None,
) -> VerificationRun:
    return VerificationRun(
        run_id=run_id,
        run_dir=f".qa-z/runs/{run_id}",
        fast_summary=run_summary("fast", fast_checks, run_id=run_id),
        deep_summary=(
            run_summary("deep", deep_checks, run_id=run_id)
            if deep_checks is not None
            else None
        ),
    )


def count_only_deep_run(
    run_id: str, *, findings_count: int, blocking_findings_count: int
) -> VerificationRun:
    base_run = verification_run(run_id, fast_checks=[], deep_checks=[])
    deep_summary = RunSummary.from_dict(
        {
            "schema_version": 2,
            "mode": "deep",
            "contract_path": "qa/contracts/example.md",
            "project_root": "/repo",
            "status": "failed",
            "started_at": "2026-04-14T00:00:00Z",
            "finished_at": "2026-04-14T00:00:01Z",
            "artifact_dir": f".qa-z/runs/{run_id}/deep",
            "checks": [
                {
                    "id": "sg_scan",
                    "tool": "sg_scan",
                    "command": ["sg_scan"],
                    "kind": "static-analysis",
                    "status": "failed",
                    "exit_code": 1,
                    "duration_ms": 1,
                    "findings_count": findings_count,
                    "blocking_findings_count": blocking_findings_count,
                    "findings": [],
                    "grouped_findings": [],
                }
            ],
        }
    )
    return VerificationRun(
        run_id=run_id,
        run_dir=f".qa-z/runs/{run_id}",
        fast_summary=base_run.fast_summary,
        deep_summary=deep_summary,
    )


def finding(rule_id: str, path: str, line: int, message: str) -> dict[str, object]:
    return {
        "rule_id": rule_id,
        "severity": "ERROR",
        "path": path,
        "line": line,
        "message": message,
    }
