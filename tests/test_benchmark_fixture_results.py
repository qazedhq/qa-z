from __future__ import annotations

from pathlib import Path

from qa_z.benchmark_contracts import BenchmarkExpectation, BenchmarkFixture
import qa_z.benchmark_fixture_results as results_module


class _ArtifactExpectationStub:
    def __init__(self, *, expect_artifacts: bool) -> None:
        self.expect_artifacts = expect_artifacts


def test_collect_artifact_actual_populates_summary_when_enabled(monkeypatch) -> None:
    actual: dict[str, object] = {}
    monkeypatch.setattr(
        results_module.benchmark_module,
        "summarize_artifact_actual",
        lambda workspace: {"files": [workspace.name]},
    )

    results_module.collect_artifact_actual(
        expectation=_ArtifactExpectationStub(expect_artifacts=True),
        workspace=Path("repo"),
        actual=actual,
    )

    assert actual == {"artifact": {"files": ["repo"]}}


def test_build_fixture_result_compares_failures_and_categories(monkeypatch) -> None:
    fixture = BenchmarkFixture(
        name="fixture-one",
        path=Path("fixture-one"),
        repo_path=Path("fixture-one"),
        expectation=BenchmarkExpectation(name="fixture-one"),
    )
    failures = ["execution error: boom"]
    monkeypatch.setattr(
        results_module.benchmark_module,
        "compare_expected",
        lambda actual, expectation: ["mismatch: expected check"],
    )
    monkeypatch.setattr(
        results_module.benchmark_module,
        "categorize_result",
        lambda failures, expectation: {"policy": False},
    )

    result = results_module.build_fixture_result(
        fixture=fixture,
        actual={"fast": {"status": "failed"}},
        artifacts={"workspace": "work/repo"},
        failures=failures,
    )

    assert failures == ["execution error: boom", "mismatch: expected check"]
    assert result.name == "fixture-one"
    assert result.passed is False
    assert result.categories == {"policy": False}
    assert result.actual == {"fast": {"status": "failed"}}
    assert result.artifacts == {"workspace": "work/repo"}


def test_record_execution_error_appends_prefixed_message() -> None:
    failures: list[str] = []

    results_module.record_execution_error(failures, ValueError("broken fixture"))

    assert failures == ["execution error: broken fixture"]
