from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import qa_z.benchmark_fixture_executor_phases as phases_module


class _ExecutorExpectationStub:
    def __init__(
        self,
        *,
        executor_bridge: dict[str, object] | None = None,
        executor_result: dict[str, object] | None = None,
        executor_dry_run: dict[str, object] | None = None,
    ) -> None:
        self._executor_bridge = executor_bridge
        self._executor_result = executor_result
        self._executor_dry_run = executor_dry_run

    def executor_bridge_config(self) -> dict[str, object] | None:
        return self._executor_bridge

    def executor_result_config(self) -> dict[str, object] | None:
        return self._executor_result

    def executor_result_dry_run_config(self) -> dict[str, object] | None:
        return self._executor_dry_run


def test_run_executor_bridge_phase_records_manifest_and_artifact(monkeypatch) -> None:
    actual: dict[str, object] = {}
    artifacts: dict[str, str] = {}
    expectation = _ExecutorExpectationStub(
        executor_bridge={
            "baseline_run": ".qa-z/runs/baseline",
            "session_id": "session-one",
            "bridge_id": "bridge-one",
            "loop_id": "L3",
            "context_paths": ["ctx.json"],
        }
    )

    monkeypatch.setattr(
        phases_module.benchmark_module,
        "execute_executor_bridge_fixture",
        lambda **kwargs: ({"bridge_id": "bridge-one"}, {"guide": "run this"}),
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "summarize_executor_bridge_actual",
        lambda **kwargs: {"guide": kwargs["guide"]["guide"]},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "format_path",
        lambda path, root: f"{root.name}:{path.name}",
    )

    phases_module.run_executor_bridge_phase(
        expectation=expectation,
        workspace=Path("repo"),
        config={},
        results_dir=Path("results"),
        actual=actual,
        artifacts=artifacts,
    )

    assert actual == {"executor_bridge": {"guide": "run this"}}
    assert artifacts == {"executor_bridge": "results:bridge.json"}


def test_run_executor_result_phase_records_verify_summary_when_triggered(
    monkeypatch,
) -> None:
    actual: dict[str, object] = {}
    artifacts: dict[str, str] = {}
    expectation = _ExecutorExpectationStub(
        executor_result={
            "baseline_run": ".qa-z/runs/baseline",
            "session_id": "session-one",
            "bridge_id": "bridge-one",
            "result_path": "result.json",
            "loop_id": "L4",
        }
    )

    monkeypatch.setattr(
        phases_module.benchmark_module,
        "execute_executor_result_fixture",
        lambda **kwargs: SimpleNamespace(
            summary={
                "verification_triggered": True,
                "verify_summary_path": ".qa-z/sessions/session-one/verify/summary.json",
                "result_status": "completed",
            }
        ),
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "summarize_executor_result_actual",
        lambda summary: {"result_status": str(summary["result_status"])},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "read_json_object",
        lambda path: {"verdict": "improved"},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "summarize_verify_summary_actual",
        lambda summary: {"verdict": str(summary["verdict"])},
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "format_path",
        lambda path, root: f"{root.name}:{path.name}",
    )

    phases_module.run_executor_result_phase(
        expectation=expectation,
        workspace=Path("repo"),
        config={},
        results_dir=Path("results"),
        actual=actual,
        artifacts=artifacts,
    )

    assert actual == {
        "executor_result": {"result_status": "completed"},
        "verify": {"verdict": "improved"},
    }
    assert artifacts == {"verify_summary": "results:summary.json"}


def test_run_executor_dry_run_phase_records_summary(monkeypatch) -> None:
    actual: dict[str, object] = {}
    artifacts: dict[str, str] = {}
    expectation = _ExecutorExpectationStub(
        executor_dry_run={"session_id": "session-dry-run"}
    )

    monkeypatch.setattr(
        phases_module.benchmark_module,
        "execute_executor_dry_run_fixture",
        lambda **kwargs: SimpleNamespace(summary={"status": "blocked"}),
    )
    monkeypatch.setattr(
        phases_module.benchmark_module,
        "summarize_executor_dry_run_actual",
        lambda summary: {"status": str(summary["status"])},
    )

    phases_module.run_executor_dry_run_phase(
        expectation=expectation,
        workspace=Path("repo"),
        actual=actual,
        artifacts=artifacts,
    )

    assert actual == {"executor_dry_run": {"status": "blocked"}}
    assert artifacts == {}
