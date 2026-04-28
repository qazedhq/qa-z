from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import qa_z.benchmark_fixture_phases as phases_module


class _ExpectationStub:
    def __init__(
        self,
        *,
        run_fast: bool = False,
        run_deep: bool = False,
        run_handoff: bool = False,
        verify: dict[str, str] | None = None,
    ) -> None:
        self._run_fast = run_fast
        self._run_deep = run_deep
        self._run_handoff = run_handoff
        self._verify = verify

    def should_run_fast(self) -> bool:
        return self._run_fast

    def should_run_deep(self) -> bool:
        return self._run_deep

    def should_run_handoff(self) -> bool:
        return self._run_handoff

    def verify_config(self) -> dict[str, str] | None:
        return self._verify


def test_run_fast_phase_records_actual_and_artifact(monkeypatch) -> None:
    actual: dict[str, object] = {}
    artifacts: dict[str, str] = {}
    expectation = _ExpectationStub(run_fast=True)

    monkeypatch.setattr(
        phases_module.benchmark_module,
        "execute_fast_fixture",
        lambda workspace, config, run_dir: {"status": "failed"},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "summarize_fast_actual",
        lambda summary: {"status": str(summary["status"])},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "format_path",
        lambda path, root: f"{root.name}:{path.name}",
    )

    phases_module.run_fast_phase(
        expectation=expectation,
        workspace=Path("repo"),
        config={},
        run_dir=Path("run"),
        results_dir=Path("results"),
        actual=actual,
        artifacts=artifacts,
    )

    assert actual == {"fast": {"status": "failed"}}
    assert artifacts == {"fast_summary": "results:summary.json"}


def test_run_deep_phase_respects_fast_attachment(monkeypatch) -> None:
    actual: dict[str, object] = {}
    artifacts: dict[str, str] = {}
    expectation = _ExpectationStub(run_fast=True, run_deep=True)
    captured: dict[str, object] = {}

    def _execute_deep_fixture(*, workspace, config, run_dir, attach_to_fast):
        captured["attach_to_fast"] = attach_to_fast
        return {"status": "warning"}

    monkeypatch.setattr(
        phases_module.benchmark_module,
        "execute_deep_fixture",
        _execute_deep_fixture,
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "summarize_deep_actual",
        lambda summary: {"status": str(summary["status"])},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "format_path",
        lambda path, root: f"{root.name}:{path.name}",
    )

    phases_module.run_deep_phase(
        expectation=expectation,
        workspace=Path("repo"),
        config={},
        run_dir=Path("run"),
        results_dir=Path("results"),
        actual=actual,
        artifacts=artifacts,
    )

    assert captured == {"attach_to_fast": True}
    assert actual == {"deep": {"status": "warning"}}
    assert artifacts == {"deep_summary": "results:summary.json"}


def test_run_handoff_phase_records_handoff_payload(monkeypatch) -> None:
    actual: dict[str, object] = {}
    artifacts: dict[str, str] = {}
    expectation = _ExpectationStub(run_handoff=True)

    monkeypatch.setattr(
        phases_module.benchmark_module,
        "execute_handoff_fixture",
        lambda workspace, config, run_dir: {"repair_needed": True},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "summarize_handoff_actual",
        lambda handoff: {"repair_needed": bool(handoff["repair_needed"])},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "format_path",
        lambda path, root: f"{root.name}:{path.name}",
    )

    phases_module.run_handoff_phase(
        expectation=expectation,
        workspace=Path("repo"),
        config={},
        run_dir=Path("run"),
        results_dir=Path("results"),
        actual=actual,
        artifacts=artifacts,
    )

    assert actual == {"handoff": {"repair_needed": True}}
    assert artifacts == {"handoff": "results:handoff.json"}


def test_run_verify_phase_records_verification_summary(monkeypatch) -> None:
    actual: dict[str, object] = {}
    artifacts: dict[str, str] = {}
    expectation = _ExpectationStub(
        verify={
            "baseline_run": ".qa-z/runs/baseline",
            "candidate_run": ".qa-z/runs/candidate",
        }
    )

    monkeypatch.setattr(
        phases_module.benchmark_module,
        "execute_verify_fixture",
        lambda **kwargs: SimpleNamespace(
            to_dict=lambda: {"verdict": "improved", "blocking_before": 1}
        ),
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "summarize_verify_actual",
        lambda comparison: {"verdict": str(comparison["verdict"])},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "format_path",
        lambda path, root: f"{root.name}:{path.name}",
    )

    phases_module.run_verify_phase(
        expectation=expectation,
        workspace=Path("repo"),
        config={},
        results_dir=Path("results"),
        actual=actual,
        artifacts=artifacts,
    )

    assert actual == {"verify": {"verdict": "improved"}}
    assert artifacts == {"verify_summary": "results:summary.json"}
