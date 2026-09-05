"""Focused tests for benchmark runtime orchestration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from qa_z.benchmark import BenchmarkError
from qa_z.benchmark import run_benchmark
from qa_z.cli import main


def test_run_benchmark_rejects_locked_results_dir(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / ".benchmark.lock").write_text(
        "pid=12345\nstarted_at=2026-04-21T00:00:00Z\n",
        encoding="utf-8",
    )

    with pytest.raises(BenchmarkError) as exc_info:
        run_benchmark(fixtures_dir=fixtures_dir, results_dir=results_dir)

    message = str(exc_info.value)
    assert "results directory is already in use" in message
    assert "lock details: pid=12345; started_at=2026-04-21T00:00:00Z" in message


def test_run_benchmark_rejects_live_lock_before_resetting_work_dir(
    tmp_path: Path,
) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    results_dir = tmp_path / "results"
    work_dir = results_dir / "work"
    work_dir.mkdir(parents=True)
    sentinel = work_dir / "existing.txt"
    sentinel.write_text("keep me\n", encoding="utf-8")

    results_dir.mkdir(exist_ok=True)
    (results_dir / ".benchmark.lock").write_text("existing run\n", encoding="utf-8")

    with pytest.raises(BenchmarkError, match="results directory is already in use"):
        run_benchmark(fixtures_dir=fixtures_dir, results_dir=results_dir)

    assert sentinel.read_text(encoding="utf-8") == "keep me\n"
    assert not (results_dir / "summary.json").exists()


def test_run_benchmark_rejects_unknown_requested_fixture_names(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixture_dir = fixtures_dir / "clean_fast"
    fixture_dir.mkdir(parents=True)
    (fixture_dir / "expected.json").write_text(
        json.dumps(
            {
                "name": "clean_fast",
                "run": {"fast": True},
                "expect_fast": {"status": "passed"},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(BenchmarkError) as exc_info:
        run_benchmark(
            fixtures_dir=fixtures_dir,
            results_dir=tmp_path / "results",
            fixture_names=["missing_fixture"],
        )

    assert "unknown benchmark fixtures requested: missing_fixture" in str(
        exc_info.value
    )


def test_run_benchmark_removes_results_lock_after_success(tmp_path: Path) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    results_dir = tmp_path / "results"

    summary = run_benchmark(fixtures_dir=fixtures_dir, results_dir=results_dir)

    assert summary["fixtures_total"] == 0
    assert not (results_dir / ".benchmark.lock").exists()


def test_run_benchmark_reports_results_lock_cleanup_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    results_dir = tmp_path / "results"

    def fail_unlink(_path: Path) -> None:
        raise PermissionError("lock still held")

    monkeypatch.setattr("qa_z.benchmark_workspace.unlink_with_retries", fail_unlink)

    with pytest.raises(BenchmarkError) as exc_info:
        run_benchmark(fixtures_dir=fixtures_dir, results_dir=results_dir)

    message = str(exc_info.value)
    assert "Could not remove benchmark results lock" in message
    assert str(results_dir / ".benchmark.lock") in message
    assert "use a different --results-dir" in message
    assert (results_dir / "summary.json").exists()


def test_benchmark_cli_reports_locked_results_dir(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    (results_dir / ".benchmark.lock").write_text("existing run\n", encoding="utf-8")

    exit_code = main(
        [
            "benchmark",
            "--path",
            str(tmp_path),
            "--fixtures-dir",
            "fixtures",
            "--results-dir",
            "results",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output["kind"] == "qa_z.benchmark_error"
    assert output["error"] == "benchmark_error"
    assert output["exit_code"] == 2
    assert output["failure_kind"] == "benchmark_results_lock"
    assert output["failure_summary"] == (
        "benchmark results directory lock is present or could not be removed"
    )
    assert "qa-z benchmark: benchmark error:" in output["message"]
    assert "results directory is already in use" in output["message"]
    assert "use a different --results-dir" in output["message"]
    assert output["next_actions"] == [
        (
            "Use a different --results-dir for this run, or remove the stale "
            "lock only after confirming no benchmark is running."
        )
    ]
    assert output["next_commands"] == [
        "python -m qa_z benchmark --results-dir <different-results-dir> --json"
    ]


def test_benchmark_cli_json_reports_artifact_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    results_dir = tmp_path / "results"
    original_write_text = Path.write_text

    def fail_summary_write(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path == results_dir / "summary.json":
            raise OSError("disk full")
        return original_write_text(
            path, data, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "write_text", fail_summary_write)

    exit_code = main(
        [
            "benchmark",
            "--path",
            str(tmp_path),
            "--fixtures-dir",
            "fixtures",
            "--results-dir",
            "results",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.benchmark_error",
        "error": "artifact_write_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z benchmark: artifact error:" in output["message"]
    assert "could not write benchmark artifacts" in output["message"]
    assert "could not write benchmark summary artifact" in output["message"]
    assert str(results_dir / "summary.json") in output["message"]
    assert "disk full" in output["message"]
    assert not (results_dir / ".benchmark.lock").exists()


def test_benchmark_cli_json_reports_report_artifact_write_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()
    results_dir = tmp_path / "results"
    original_write_text = Path.write_text

    def fail_report_write(
        path: Path,
        data: str,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str | None = None,
    ) -> int:
        if path == results_dir / "report.md":
            raise OSError("disk full")
        return original_write_text(
            path, data, encoding=encoding, errors=errors, newline=newline
        )

    monkeypatch.setattr(Path, "write_text", fail_report_write)

    exit_code = main(
        [
            "benchmark",
            "--path",
            str(tmp_path),
            "--fixtures-dir",
            "fixtures",
            "--results-dir",
            "results",
            "--json",
        ]
    )
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 2
    assert output == {
        "kind": "qa_z.benchmark_error",
        "error": "artifact_write_error",
        "exit_code": 2,
        "message": output["message"],
    }
    assert "qa-z benchmark: artifact error:" in output["message"]
    assert "could not write benchmark artifacts" in output["message"]
    assert "could not write benchmark report artifact" in output["message"]
    assert str(results_dir / "report.md") in output["message"]
    assert "disk full" in output["message"]
    assert not (results_dir / ".benchmark.lock").exists()
