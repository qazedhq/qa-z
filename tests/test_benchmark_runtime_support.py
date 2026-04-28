from __future__ import annotations

from pathlib import Path

import pytest

from qa_z.benchmark_contracts import BenchmarkExpectation, BenchmarkFixture
import qa_z.benchmark_runtime_support as support_module


def _fixture(name: str) -> BenchmarkFixture:
    return BenchmarkFixture(
        name=name,
        path=Path(name) / "fixture",
        repo_path=Path(name),
        expectation=BenchmarkExpectation(name=name),
    )


def test_select_requested_fixtures_filters_known_names() -> None:
    fixtures = [_fixture("one"), _fixture("two")]

    selected = support_module.select_requested_fixtures(fixtures, ["two"])

    assert [fixture.name for fixture in selected] == ["two"]


def test_select_requested_fixtures_rejects_missing_names() -> None:
    fixtures = [_fixture("one")]

    with pytest.raises(support_module.benchmark_module.BenchmarkError) as exc_info:
        support_module.select_requested_fixtures(fixtures, ["missing"])

    assert "unknown benchmark fixtures requested: missing" in str(exc_info.value)


def test_prepare_work_dir_resets_results_work_tree(monkeypatch, tmp_path: Path) -> None:
    calls: list[Path] = []
    monkeypatch.setattr(
        support_module.benchmark_module,
        "reset_directory",
        lambda path: calls.append(path),
    )

    work_dir = support_module.prepare_work_dir(tmp_path)

    assert work_dir == tmp_path / "work"
    assert calls == [tmp_path / "work"]


def test_run_fixture_batch_executes_each_fixture(monkeypatch, tmp_path: Path) -> None:
    fixtures = [_fixture("one"), _fixture("two")]
    calls: list[tuple[str, Path, Path]] = []

    def _run_fixture(fixture, *, work_dir: Path, results_dir: Path):
        calls.append((fixture.name, work_dir, results_dir))
        return fixture.name

    monkeypatch.setattr(support_module.benchmark_module, "run_fixture", _run_fixture)

    results = support_module.run_fixture_batch(
        fixtures, work_dir=tmp_path / "work", results_dir=tmp_path / "results"
    )

    assert results == ["one", "two"]
    assert calls == [
        ("one", tmp_path / "work", tmp_path / "results"),
        ("two", tmp_path / "work", tmp_path / "results"),
    ]
