"""Contract models for benchmark fixtures and results."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from qa_z.benchmark_helpers import coerce_mapping, string_list


@dataclass(frozen=True)
class BenchmarkExpectation:
    """Expected behavior contract loaded from a fixture expected.json."""

    name: str
    description: str = ""
    run: dict[str, Any] = field(default_factory=dict)
    expect_fast: dict[str, Any] = field(default_factory=dict)
    expect_deep: dict[str, Any] = field(default_factory=dict)
    expect_handoff: dict[str, Any] = field(default_factory=dict)
    expect_verify: dict[str, Any] = field(default_factory=dict)
    expect_executor_bridge: dict[str, Any] = field(default_factory=dict)
    expect_executor_result: dict[str, Any] = field(default_factory=dict)
    expect_executor_dry_run: dict[str, Any] = field(default_factory=dict)
    expect_artifacts: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "BenchmarkExpectation":
        """Load an expectation contract from JSON data."""
        name = str(data.get("name") or "").strip()
        if not name:
            raise ValueError("Benchmark expected.json must contain a non-empty name.")
        return cls(
            name=name,
            description=str(data.get("description") or "").strip(),
            run=coerce_mapping(data.get("run")),
            expect_fast=coerce_mapping(data.get("expect_fast")),
            expect_deep=coerce_mapping(data.get("expect_deep")),
            expect_handoff=coerce_mapping(data.get("expect_handoff")),
            expect_verify=coerce_mapping(data.get("expect_verify")),
            expect_executor_bridge=coerce_mapping(data.get("expect_executor_bridge")),
            expect_executor_result=coerce_mapping(data.get("expect_executor_result")),
            expect_executor_dry_run=coerce_mapping(data.get("expect_executor_dry_run")),
            expect_artifacts=coerce_mapping(data.get("expect_artifacts")),
        )

    def should_run_fast(self) -> bool:
        """Return whether this fixture needs a fast QA-Z run."""
        return (
            bool(self.run.get("fast"))
            or bool(self.expect_fast)
            or bool(self.expect_handoff)
        )

    def should_run_deep(self) -> bool:
        """Return whether this fixture needs a deep QA-Z run."""
        return bool(self.run.get("deep")) or bool(self.expect_deep)

    def should_run_handoff(self) -> bool:
        """Return whether this fixture needs repair handoff generation."""
        return bool(self.run.get("repair_handoff")) or bool(self.expect_handoff)

    def verify_config(self) -> dict[str, str] | None:
        """Return baseline/candidate run settings for verification, if requested."""
        configured = self.run.get("verify")
        if isinstance(configured, dict):
            return {
                "baseline_run": str(
                    configured.get("baseline_run") or ".qa-z/runs/baseline"
                ),
                "candidate_run": str(
                    configured.get("candidate_run") or ".qa-z/runs/candidate"
                ),
            }
        if configured or self.expect_verify:
            return {
                "baseline_run": ".qa-z/runs/baseline",
                "candidate_run": ".qa-z/runs/candidate",
            }
        return None

    def executor_bridge_config(self) -> dict[str, Any] | None:
        """Return repair-session bridge settings, if requested."""
        configured = self.run.get("executor_bridge")
        if isinstance(configured, dict):
            return {
                "baseline_run": str(
                    configured.get("baseline_run") or ".qa-z/runs/baseline"
                ),
                "session_id": str(
                    configured.get("session_id") or "benchmark-bridge-session"
                ),
                "bridge_id": str(configured.get("bridge_id") or "benchmark-bridge"),
                "loop_id": str(configured.get("loop_id") or "loop-benchmark-bridge"),
                "context_paths": string_list(configured.get("context_paths")),
            }
        if configured or self.expect_executor_bridge:
            return {
                "baseline_run": ".qa-z/runs/baseline",
                "session_id": "benchmark-bridge-session",
                "bridge_id": "benchmark-bridge",
                "loop_id": "loop-benchmark-bridge",
                "context_paths": [],
            }
        return None

    def executor_result_config(self) -> dict[str, str] | None:
        """Return session/bridge/result settings for executor-result ingest."""
        configured = self.run.get("executor_result")
        if isinstance(configured, dict):
            return {
                "baseline_run": str(
                    configured.get("baseline_run") or ".qa-z/runs/baseline"
                ),
                "session_id": str(configured.get("session_id") or "benchmark-session"),
                "bridge_id": str(configured.get("bridge_id") or "benchmark-bridge"),
                "result_path": str(
                    configured.get("result_path") or "external-result.json"
                ),
                "loop_id": str(configured.get("loop_id") or ""),
            }
        if self.expect_executor_result:
            return {
                "baseline_run": ".qa-z/runs/baseline",
                "session_id": "benchmark-session",
                "bridge_id": "benchmark-bridge",
                "result_path": "external-result.json",
                "loop_id": "",
            }
        return None

    def executor_result_dry_run_config(self) -> dict[str, str] | None:
        """Return session settings for executor-result dry-run."""
        configured = self.run.get("executor_result_dry_run")
        if isinstance(configured, dict):
            return {
                "session_id": str(
                    configured.get("session_id")
                    or configured.get("session")
                    or "benchmark-session"
                ),
            }
        if configured or self.expect_executor_dry_run:
            executor_result = self.run.get("executor_result")
            if isinstance(executor_result, dict):
                session_id = str(
                    executor_result.get("session_id") or "benchmark-session"
                )
            else:
                session_id = "benchmark-session"
            return {"session_id": session_id}
        return None


@dataclass(frozen=True)
class BenchmarkFixture:
    """One benchmark fixture and its expected outcome contract."""

    name: str
    path: Path
    repo_path: Path
    expectation: BenchmarkExpectation


@dataclass(frozen=True)
class BenchmarkFixtureResult:
    """Result for one benchmark fixture."""

    name: str
    passed: bool
    failures: list[str]
    categories: dict[str, bool | None]
    actual: dict[str, Any]
    artifacts: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        """Render this fixture result as JSON-safe data."""
        return {
            "name": self.name,
            "passed": self.passed,
            "failures": list(self.failures),
            "categories": dict(self.categories),
            "actual": self.actual,
            "artifacts": dict(self.artifacts),
        }


class BenchmarkError(RuntimeError):
    """Raised when benchmark execution cannot proceed."""
