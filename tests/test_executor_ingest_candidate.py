"""Tests for executor-ingest rerun candidate helpers."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from qa_z.artifacts import RunSource
from qa_z.executor_ingest_candidate import (
    create_verify_candidate_run,
    resolve_deep_selection_mode,
    resolve_fast_selection_mode,
    write_verify_rerun_review_artifacts,
)
from qa_z.runners.models import CheckResult, RunSummary
from qa_z.verification import VerificationRun


def check_result(check_id: str, status: str, *, exit_code: int | None) -> CheckResult:
    """Build a compact check result for candidate-run tests."""
    return CheckResult(
        id=check_id,
        tool=check_id,
        command=[check_id],
        kind="test",
        status=status,
        exit_code=exit_code,
        duration_ms=1,
        stdout_tail="ok" if status == "passed" else "failed",
    )


def run_summary(
    root: Path,
    run_id: str,
    mode: str,
    *,
    status: str = "passed",
) -> RunSummary:
    """Build a deterministic run summary for candidate-run helpers."""
    return RunSummary(
        mode=mode,
        contract_path="qa/contracts/contract.md",
        project_root=str(root),
        status=status,
        started_at="2026-04-22T00:00:00Z",
        finished_at="2026-04-22T00:00:01Z",
        artifact_dir=f".qa-z/runs/{run_id}/{mode}",
        checks=[
            check_result("py_test", status, exit_code=0 if status == "passed" else 1)
        ],
        schema_version=2,
    )


def test_resolve_selection_modes_default_to_full_for_invalid_values() -> None:
    config = {
        "fast": {"selection": {"default_mode": "invalid"}},
        "deep": {"selection": {"default_mode": "smart"}},
    }

    assert resolve_fast_selection_mode(config) == "full"
    assert resolve_deep_selection_mode(config) == "smart"


def test_write_verify_rerun_review_artifacts_writes_review_bundle(
    tmp_path: Path,
) -> None:
    contract_path = tmp_path / "qa" / "contracts" / "contract.md"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text(
        (
            "---\n"
            "title: Candidate rerun contract\n"
            "summary: Preserve deterministic rerun evidence.\n"
            "acceptance_checks:\n"
            "  - Candidate review artifacts exist.\n"
            "---\n"
            "# Candidate rerun contract\n"
        ),
        encoding="utf-8",
    )
    run_dir = tmp_path / ".qa-z" / "runs" / "candidate"
    fast_dir = run_dir / "fast"
    fast_dir.mkdir(parents=True, exist_ok=True)
    summary = run_summary(tmp_path, "candidate", "fast", status="failed")
    deep_summary = run_summary(tmp_path, "candidate", "deep")
    run_source = RunSource(
        run_dir=run_dir,
        fast_dir=fast_dir,
        summary_path=fast_dir / "summary.json",
    )

    write_verify_rerun_review_artifacts(
        root=tmp_path,
        config={"contracts": {"output_dir": "qa/contracts"}},
        run_source=run_source,
        summary=summary,
        deep_summary=deep_summary,
    )

    review_markdown = (run_dir / "review" / "review.md").read_text(encoding="utf-8")
    review_json = (run_dir / "review" / "review.json").read_text(encoding="utf-8")

    assert "qa/contracts/contract.md" in review_markdown
    assert "## Run Verdict" in review_markdown
    assert '"title": "Candidate rerun contract"' in review_json
    assert '"dir": ".qa-z/runs/candidate"' in review_json


def test_create_verify_candidate_run_uses_selection_modes_and_review_bundle(
    tmp_path: Path, monkeypatch
) -> None:
    contract_path = tmp_path / "qa" / "contracts" / "contract.md"
    contract_path.parent.mkdir(parents=True, exist_ok=True)
    contract_path.write_text("# Candidate rerun contract\n", encoding="utf-8")
    rerun_output_dir = tmp_path / ".qa-z" / "sessions" / "session-one" / "candidate"
    fast_summary = run_summary(tmp_path, "candidate-rerun", "fast")
    fast_summary.artifact_dir = ".qa-z/sessions/session-one/candidate/fast"
    deep_summary = run_summary(tmp_path, "candidate-rerun", "deep")
    captured: dict[str, object] = {}

    def fake_run_fast(**kwargs):
        captured["fast_selection_mode"] = kwargs["selection_mode"]
        captured["fast_contract_path"] = kwargs["contract_path"]
        return SimpleNamespace(summary=fast_summary)

    def fake_run_deep(**kwargs):
        captured["deep_selection_mode"] = kwargs["selection_mode"]
        return SimpleNamespace(
            summary=deep_summary,
            resolution=SimpleNamespace(deep_dir=rerun_output_dir / "deep"),
        )

    def fake_write_review_artifacts(**kwargs):
        captured["review_run_dir"] = kwargs["run_source"].run_dir
        captured["review_summary"] = kwargs["summary"]
        captured["review_deep_summary"] = kwargs["deep_summary"]

    monkeypatch.setattr("qa_z.executor_ingest_candidate.run_fast", fake_run_fast)
    monkeypatch.setattr("qa_z.executor_ingest_candidate.run_deep", fake_run_deep)
    monkeypatch.setattr(
        "qa_z.executor_ingest_candidate.write_verify_rerun_review_artifacts",
        fake_write_review_artifacts,
    )
    monkeypatch.setattr(
        "qa_z.executor_ingest_candidate.write_sarif_artifact",
        lambda *args, **kwargs: None,
    )

    baseline = VerificationRun(
        run_id="baseline",
        run_dir=".qa-z/runs/baseline",
        fast_summary=run_summary(tmp_path, "baseline", "fast"),
        deep_summary=None,
    )
    config = {
        "contracts": {"output_dir": "qa/contracts"},
        "fast": {"selection": {"default_mode": "smart"}},
        "deep": {"selection": {"default_mode": "invalid"}},
    }

    candidate_run = create_verify_candidate_run(
        root=tmp_path,
        config=config,
        rerun_output_dir=rerun_output_dir,
        strict_no_tests=False,
        baseline=baseline,
    )

    assert candidate_run == ".qa-z/sessions/session-one/candidate"
    assert captured["fast_selection_mode"] == "smart"
    assert captured["deep_selection_mode"] == "full"
    assert captured["fast_contract_path"] == contract_path
    assert captured["review_run_dir"] == rerun_output_dir
    assert captured["review_summary"] == fast_summary
    assert captured["review_deep_summary"] == deep_summary
    assert (tmp_path / ".qa-z" / "runs" / "latest-run.json").read_text(encoding="utf-8")
