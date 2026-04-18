"""Reproducible benchmark corpus runner for QA-Z artifacts."""

from __future__ import annotations

import json
import os
import shutil
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator

from qa_z.artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_run_source,
    write_latest_run_manifest,
)
from qa_z.config import load_config
from qa_z.executor_bridge import create_executor_bridge, render_bridge_stdout
from qa_z.executor_dry_run import run_executor_result_dry_run
from qa_z.executor_ingest import (
    ExecutorResultIngestRejected,
    ingest_executor_result_artifact,
)
from qa_z.executor_result import write_json
from qa_z.repair_handoff import (
    RepairHandoffPacket,
    build_repair_handoff,
    write_repair_handoff_artifact,
)
from qa_z.repair_session import create_repair_session
from qa_z.reporters.deep_context import load_sibling_deep_summary
from qa_z.reporters.repair_prompt import build_repair_packet, write_repair_artifacts
from qa_z.reporters.run_summary import write_run_summary_artifacts
from qa_z.reporters.sarif import write_sarif_artifact
from qa_z.runners.deep import run_deep
from qa_z.runners.fast import run_fast
from qa_z.runners.models import RunSummary
from qa_z.verification import (
    VERIFY_SCHEMA_VERSION,
    compare_verification_runs,
    load_verification_run,
    write_verification_artifacts,
)

BENCHMARK_SUMMARY_KIND = "qa_z.benchmark_summary"
BENCHMARK_SCHEMA_VERSION = 1
DEFAULT_FIXTURES_DIR = Path("benchmarks") / "fixtures"
DEFAULT_RESULTS_DIR = Path("benchmarks") / "results"
CATEGORY_NAMES = ("detection", "handoff", "verify", "artifact", "policy")
POLICY_EXPECTATION_KEYS = {
    "blocking_findings_count",
    "blocking_findings_min",
    "blocking_findings_count_min",
    "blocking_findings_count_max",
    "filtered_findings_count",
    "filtered_findings_count_min",
    "filtered_findings_count_max",
    "grouped_findings_count",
    "grouped_findings_count_min",
    "grouped_findings_count_max",
    "grouped_findings_min",
    "findings_count",
    "findings_count_min",
    "findings_count_max",
    "rule_ids_present",
    "rule_ids_absent",
    "filter_reasons",
    "error_types",
    "config_error",
    "expect_config_error",
    "policy",
}


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
            }
        if self.expect_executor_result:
            return {
                "baseline_run": ".qa-z/runs/baseline",
                "session_id": "benchmark-session",
                "bridge_id": "benchmark-bridge",
                "result_path": "external-result.json",
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


def discover_fixtures(fixtures_dir: Path) -> list[BenchmarkFixture]:
    """Discover benchmark fixtures containing an expected.json contract."""
    if not fixtures_dir.exists():
        return []
    fixtures: list[BenchmarkFixture] = []
    for expected_path in sorted(fixtures_dir.glob("*/expected.json")):
        expectation = load_fixture_expectation(expected_path)
        fixture_dir = expected_path.parent
        fixtures.append(
            BenchmarkFixture(
                name=expectation.name,
                path=fixture_dir,
                repo_path=fixture_dir / "repo",
                expectation=expectation,
            )
        )
    return sorted(fixtures, key=lambda fixture: fixture.name)


def load_fixture_expectation(expected_path: Path) -> BenchmarkExpectation:
    """Load one expected.json contract."""
    try:
        data = json.loads(expected_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise BenchmarkError(f"Could not read {expected_path}") from exc
    except json.JSONDecodeError as exc:
        raise BenchmarkError(f"{expected_path} is not valid JSON") from exc
    if not isinstance(data, dict):
        raise BenchmarkError(f"{expected_path} must contain a JSON object.")
    try:
        return BenchmarkExpectation.from_dict(data)
    except ValueError as exc:
        raise BenchmarkError(f"{expected_path}: {exc}") from exc


def run_benchmark(
    *,
    fixtures_dir: Path = DEFAULT_FIXTURES_DIR,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    fixture_names: list[str] | None = None,
) -> dict[str, Any]:
    """Run benchmark fixtures, compare outputs, and write summary artifacts."""
    fixtures = discover_fixtures(fixtures_dir)
    if fixture_names:
        requested = set(fixture_names)
        fixtures = [fixture for fixture in fixtures if fixture.name in requested]
    results_dir.mkdir(parents=True, exist_ok=True)
    work_dir = results_dir / "work"
    reset_directory(work_dir)

    results = [
        run_fixture(fixture, work_dir=work_dir, results_dir=results_dir)
        for fixture in fixtures
    ]
    summary = build_benchmark_summary(results)
    write_benchmark_artifacts(summary, results_dir)
    return summary


def run_fixture(
    fixture: BenchmarkFixture, *, work_dir: Path, results_dir: Path
) -> BenchmarkFixtureResult:
    """Execute one benchmark fixture and compare it to its expectation."""
    actual: dict[str, Any] = {}
    artifacts: dict[str, str] = {}
    failures: list[str] = []
    workspace = prepare_workspace(fixture, work_dir)
    config = load_config(workspace)
    run_dir = workspace / ".qa-z" / "runs" / "benchmark"
    artifacts["workspace"] = format_path(workspace, results_dir)

    try:
        with fixture_path_environment(workspace):
            if fixture.expectation.should_run_fast():
                fast_summary = execute_fast_fixture(workspace, config, run_dir)
                actual["fast"] = summarize_fast_actual(fast_summary)
                artifacts["fast_summary"] = format_path(
                    run_dir / "fast" / "summary.json", results_dir
                )

            if fixture.expectation.should_run_deep():
                deep_summary = execute_deep_fixture(
                    workspace=workspace,
                    config=config,
                    run_dir=run_dir,
                    attach_to_fast=fixture.expectation.should_run_fast(),
                )
                actual["deep"] = summarize_deep_actual(deep_summary)
                artifacts["deep_summary"] = format_path(
                    run_dir / "deep" / "summary.json", results_dir
                )

            if fixture.expectation.should_run_handoff():
                handoff = execute_handoff_fixture(workspace, config, run_dir)
                actual["handoff"] = summarize_handoff_actual(handoff)
                artifacts["handoff"] = format_path(
                    run_dir / "repair" / "handoff.json", results_dir
                )

            verify_config = fixture.expectation.verify_config()
            if verify_config is not None:
                comparison = execute_verify_fixture(
                    workspace=workspace,
                    config=config,
                    baseline_run=verify_config["baseline_run"],
                    candidate_run=verify_config["candidate_run"],
                )
                actual["verify"] = summarize_verify_actual(comparison.to_dict())
                artifacts["verify_summary"] = format_path(
                    workspace
                    / str(verify_config["candidate_run"])
                    / "verify"
                    / "summary.json",
                    results_dir,
                )

            executor_bridge_config = fixture.expectation.executor_bridge_config()
            if executor_bridge_config is not None:
                bridge_manifest, bridge_guide = execute_executor_bridge_fixture(
                    workspace=workspace,
                    config=config,
                    baseline_run=str(executor_bridge_config["baseline_run"]),
                    session_id=str(executor_bridge_config["session_id"]),
                    bridge_id=str(executor_bridge_config["bridge_id"]),
                    loop_id=str(executor_bridge_config["loop_id"]),
                    context_paths=list(executor_bridge_config["context_paths"]),
                )
                actual["executor_bridge"] = summarize_executor_bridge_actual(
                    workspace=workspace,
                    manifest=bridge_manifest,
                    guide=bridge_guide,
                )
                artifacts["executor_bridge"] = format_path(
                    workspace
                    / ".qa-z"
                    / "executor"
                    / str(executor_bridge_config["bridge_id"])
                    / "bridge.json",
                    results_dir,
                )

            executor_result_config = fixture.expectation.executor_result_config()
            if executor_result_config is not None:
                outcome = execute_executor_result_fixture(
                    workspace=workspace,
                    config=config,
                    baseline_run=executor_result_config["baseline_run"],
                    session_id=executor_result_config["session_id"],
                    bridge_id=executor_result_config["bridge_id"],
                    result_path=executor_result_config["result_path"],
                )
                actual["executor_result"] = summarize_executor_result_actual(
                    outcome.summary
                )
                if outcome.summary.get(
                    "verification_triggered"
                ) and outcome.summary.get("verify_summary_path"):
                    verify_summary_path = workspace / str(
                        outcome.summary["verify_summary_path"]
                    )
                    verify_summary = read_json_object(verify_summary_path)
                    actual["verify"] = summarize_verify_summary_actual(verify_summary)
                    artifacts["verify_summary"] = format_path(
                        verify_summary_path, results_dir
                    )

            executor_dry_run_config = (
                fixture.expectation.executor_result_dry_run_config()
            )
            if executor_dry_run_config is not None:
                dry_run_outcome = execute_executor_dry_run_fixture(
                    workspace=workspace,
                    session_id=executor_dry_run_config["session_id"],
                )
                actual["executor_dry_run"] = summarize_executor_dry_run_actual(
                    dry_run_outcome.summary
                )

            if fixture.expectation.expect_artifacts:
                actual["artifact"] = summarize_artifact_actual(workspace)
    except (
        ArtifactLoadError,
        ArtifactSourceNotFound,
        BenchmarkError,
        FileNotFoundError,
        ValueError,
    ) as exc:
        failures.append(f"execution error: {exc}")

    failures.extend(compare_expected(actual, fixture.expectation))
    categories = categorize_result(failures, fixture.expectation)
    return BenchmarkFixtureResult(
        name=fixture.name,
        passed=not failures,
        failures=failures,
        categories=categories,
        actual=actual,
        artifacts=artifacts,
    )


def execute_fast_fixture(
    workspace: Path, config: dict[str, Any], run_dir: Path
) -> RunSummary:
    """Run the fast QA-Z path for one fixture."""
    fast_run = run_fast(
        root=workspace,
        config=config,
        output_dir=run_dir,
        selection_mode="full",
    )
    summary_path = write_run_summary_artifacts(fast_run.summary, run_dir / "fast")
    write_latest_run_manifest(workspace, config, run_dir)
    return load_run_summary(summary_path)


def execute_deep_fixture(
    *,
    workspace: Path,
    config: dict[str, Any],
    run_dir: Path,
    attach_to_fast: bool,
) -> RunSummary:
    """Run the deep QA-Z path for one fixture."""
    deep_run = run_deep(
        root=workspace,
        config=config,
        from_run=str(run_dir) if attach_to_fast else None,
        output_dir=None if attach_to_fast else run_dir,
        selection_mode="full",
    )
    summary_path = write_run_summary_artifacts(
        deep_run.summary, deep_run.resolution.deep_dir
    )
    write_sarif_artifact(
        deep_run.summary, deep_run.resolution.deep_dir / "results.sarif"
    )
    return load_run_summary(summary_path)


def execute_handoff_fixture(
    workspace: Path, config: dict[str, Any], run_dir: Path
) -> RepairHandoffPacket:
    """Generate repair packet and handoff artifacts for one fixture."""
    run_source = resolve_run_source(workspace, config, str(run_dir))
    summary = load_run_summary(run_source.summary_path)
    deep_summary = load_sibling_deep_summary(run_source)
    contract_path = resolve_contract_source(workspace, config, summary=summary)
    contract = load_contract_context(contract_path, workspace)
    packet = build_repair_packet(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=workspace,
        deep_summary=deep_summary,
    )
    handoff = build_repair_handoff(
        repair_packet=packet,
        summary=summary,
        run_source=run_source,
        root=workspace,
        deep_summary=deep_summary,
    )
    output_dir = run_dir / "repair"
    write_repair_artifacts(packet, output_dir)
    write_repair_handoff_artifact(handoff, output_dir)
    return handoff


def execute_verify_fixture(
    *,
    workspace: Path,
    config: dict[str, Any],
    baseline_run: str,
    candidate_run: str,
):
    """Compare pre-seeded baseline and candidate run artifacts."""
    baseline, _baseline_source = load_verification_run(
        root=workspace,
        config=config,
        from_run=baseline_run,
    )
    candidate, candidate_source = load_verification_run(
        root=workspace,
        config=config,
        from_run=candidate_run,
    )
    comparison = compare_verification_runs(baseline, candidate)
    write_verification_artifacts(comparison, candidate_source.run_dir / "verify")
    return comparison


def execute_executor_result_fixture(
    *,
    workspace: Path,
    config: dict[str, Any],
    baseline_run: str,
    session_id: str,
    bridge_id: str,
    result_path: str,
):
    """Create a repair session, package a bridge, and ingest a result."""
    fixed_now = "2026-04-16T00:00:00Z"
    create_repair_session(
        root=workspace,
        config=config,
        baseline_run=baseline_run,
        session_id=session_id,
    )
    session_manifest_path = (
        workspace / ".qa-z" / "sessions" / session_id / "session.json"
    )
    session_manifest = read_json_object(session_manifest_path)
    session_manifest["created_at"] = fixed_now
    session_manifest["updated_at"] = fixed_now
    write_json(session_manifest_path, session_manifest)
    create_executor_bridge(
        root=workspace,
        from_session=session_id,
        bridge_id=bridge_id,
        now=fixed_now,
    )
    try:
        return ingest_executor_result_artifact(
            root=workspace,
            config=config,
            result_path=workspace / result_path,
            now=fixed_now,
        )
    except ExecutorResultIngestRejected as exc:
        return exc.outcome


def execute_executor_bridge_fixture(
    *,
    workspace: Path,
    config: dict[str, Any],
    baseline_run: str,
    session_id: str,
    bridge_id: str,
    loop_id: str,
    context_paths: list[str],
) -> tuple[dict[str, Any], str]:
    """Create a loop-sourced executor bridge for one benchmark fixture."""
    fixed_now = "2026-04-16T00:00:00Z"
    create_repair_session(
        root=workspace,
        config=config,
        baseline_run=baseline_run,
        session_id=session_id,
    )
    session_manifest_path = (
        workspace / ".qa-z" / "sessions" / session_id / "session.json"
    )
    session_manifest = read_json_object(session_manifest_path)
    session_manifest["created_at"] = fixed_now
    session_manifest["updated_at"] = fixed_now
    write_json(session_manifest_path, session_manifest)
    loop_dir = workspace / ".qa-z" / "loops" / loop_id
    write_json(
        loop_dir / "outcome.json",
        {
            "kind": "qa_z.autonomy_outcome",
            "schema_version": 1,
            "loop_id": loop_id,
            "generated_at": fixed_now,
            "state": "completed",
            "selected_task_ids": ["verify_regression-candidate"],
            "actions_prepared": [
                {
                    "type": "repair_session",
                    "task_id": "verify_regression-candidate",
                    "session_id": session_id,
                    "session_dir": f".qa-z/sessions/{session_id}",
                    "context_paths": list(context_paths),
                }
            ],
            "next_recommendations": ["run external repair, then repair-session verify"],
            "artifacts": {"outcome": f".qa-z/loops/{loop_id}/outcome.json"},
        },
    )
    paths = create_executor_bridge(
        root=workspace,
        from_loop=loop_id,
        bridge_id=bridge_id,
        now=fixed_now,
    )
    return (
        read_json_object(paths.manifest_path),
        paths.executor_guide_path.read_text(encoding="utf-8"),
    )


def execute_executor_dry_run_fixture(*, workspace: Path, session_id: str):
    """Run executor-result dry-run for one seeded benchmark session."""
    return run_executor_result_dry_run(root=workspace, session_ref=session_id)


def compare_expected(
    actual: dict[str, Any], expectation: BenchmarkExpectation
) -> list[str]:
    """Compare actual benchmark observations against expected outcomes."""
    failures: list[str] = []
    failures.extend(
        compare_section(
            "fast", coerce_mapping(actual.get("fast")), expectation.expect_fast
        )
    )
    failures.extend(
        compare_section(
            "deep", coerce_mapping(actual.get("deep")), expectation.expect_deep
        )
    )
    failures.extend(
        compare_section(
            "handoff",
            coerce_mapping(actual.get("handoff")),
            expectation.expect_handoff,
        )
    )
    failures.extend(
        compare_section(
            "verify",
            coerce_mapping(actual.get("verify")),
            expectation.expect_verify,
        )
    )
    failures.extend(
        compare_section(
            "executor_bridge",
            coerce_mapping(actual.get("executor_bridge")),
            expectation.expect_executor_bridge,
        )
    )
    failures.extend(
        compare_section(
            "executor_result",
            coerce_mapping(actual.get("executor_result")),
            expectation.expect_executor_result,
        )
    )
    failures.extend(
        compare_section(
            "executor_dry_run",
            coerce_mapping(actual.get("executor_dry_run")),
            expectation.expect_executor_dry_run,
        )
    )
    failures.extend(
        compare_section(
            "artifact",
            coerce_mapping(actual.get("artifact")),
            expectation.expect_artifacts,
        )
    )
    return failures


def compare_section(
    section: str, actual: dict[str, Any], expected: dict[str, Any]
) -> list[str]:
    """Compare one expected-results section with tolerant list matching."""
    if not expected:
        return []
    if not actual:
        return [f"{section} expected results but no actual section was produced"]

    failures: list[str] = []
    for key, expected_value in expected.items():
        actual_key = expectation_actual_key(key)
        if actual_key not in actual:
            failures.append(f"{section}.{actual_key} missing from actual results")
            continue
        actual_value = actual[actual_key]
        if key.endswith("_min"):
            failures.extend(
                compare_minimum(section, actual_key, actual_value, expected_value)
            )
        elif key.endswith("_max"):
            failures.extend(
                compare_maximum(section, actual_key, actual_value, expected_value)
            )
        elif key.endswith("_present"):
            failures.extend(
                compare_expected_list(section, actual_key, actual_value, expected_value)
            )
        elif key.endswith("_absent"):
            failures.extend(
                compare_absent_list(section, actual_key, actual_value, expected_value)
            )
        elif isinstance(expected_value, list):
            failures.extend(
                compare_expected_list(section, actual_key, actual_value, expected_value)
            )
        elif actual_value != expected_value:
            failures.append(
                f"{section}.{key} expected {expected_value!r} but got {actual_value!r}"
            )
    return failures


def compare_absent_list(
    section: str, key: str, actual_value: object, expected_value: object
) -> list[str]:
    """Assert a list of values is absent from an actual list."""
    if not isinstance(expected_value, list):
        return [f"{section}.{key} expected an absence list but got {expected_value!r}"]
    if not isinstance(actual_value, list):
        return [f"{section}.{key} expected a list but got {actual_value!r}"]
    actual_set = {str(item) for item in actual_value}
    present = [str(item) for item in expected_value if str(item) in actual_set]
    if present:
        return [
            f"{section}.{key} expected values absent but found: "
            f"{', '.join(sorted(present))}"
        ]
    return []


def compare_expected_list(
    section: str, key: str, actual_value: object, expected_value: object
) -> list[str]:
    """Compare lists using expected-subset semantics."""
    if not isinstance(expected_value, list):
        return [f"{section}.{key} expected a list contract but got {expected_value!r}"]
    if not isinstance(actual_value, list):
        return [f"{section}.{key} expected a list but got {actual_value!r}"]
    actual_set = {str(item) for item in actual_value}
    missing = [str(item) for item in expected_value if str(item) not in actual_set]
    if missing:
        return [
            f"{section}.{key} missing expected values: {', '.join(sorted(missing))}"
        ]
    return []


def compare_minimum(
    section: str, key: str, actual_value: object, expected_value: object
) -> list[str]:
    """Compare a numeric minimum threshold."""
    actual_number = coerce_number(actual_value)
    expected_number = coerce_number(expected_value)
    if actual_number is None or expected_number is None:
        return [f"{section}.{key} expected numeric minimum comparison"]
    if actual_number < expected_number:
        return [
            f"{section}.{key} expected at least {expected_number:g} but got {actual_number:g}"
        ]
    return []


def compare_maximum(
    section: str, key: str, actual_value: object, expected_value: object
) -> list[str]:
    """Compare a numeric maximum threshold."""
    actual_number = coerce_number(actual_value)
    expected_number = coerce_number(expected_value)
    if actual_number is None or expected_number is None:
        return [f"{section}.{key} expected numeric maximum comparison"]
    if actual_number > expected_number:
        return [
            f"{section}.{key} expected at most {expected_number:g} but got {actual_number:g}"
        ]
    return []


def expectation_actual_key(key: str) -> str:
    """Return the actual key for additive expectation names."""
    if key == "expect_config_error":
        return "config_error"
    if key == "expect_status":
        return "status"
    if key == "expected_source":
        return "summary_source"
    if key == "expected_recommendation":
        return "next_recommendation"
    if key == "expected_ingest_status":
        return "ingest_status"
    if key in {"grouped_findings_min", "grouped_findings_max"}:
        return "grouped_findings_count"
    if key.endswith("_present"):
        return key[: -len("_present")]
    if key.endswith("_absent"):
        return key[: -len("_absent")]
    if key.endswith("_min"):
        return key[: -len("_min")]
    if key.endswith("_max"):
        return key[: -len("_max")]
    return key


def categorize_result(
    failures: list[str], expectation: BenchmarkExpectation
) -> dict[str, bool | None]:
    """Summarize pass/fail by benchmark concern."""
    return {
        "detection": category_status(
            failures,
            prefixes=("fast.", "deep."),
            applies=bool(expectation.expect_fast or expectation.expect_deep),
        ),
        "handoff": category_status(
            failures,
            prefixes=("handoff.",),
            applies=bool(expectation.expect_handoff),
        ),
        "verify": category_status(
            failures,
            prefixes=("verify.",),
            applies=bool(expectation.expect_verify),
        ),
        "artifact": category_status(
            failures,
            prefixes=("artifact.", "executor_bridge."),
            applies=bool(
                expectation.expect_artifacts or expectation.expect_executor_bridge
            ),
        ),
        "policy": category_status(
            failures,
            prefixes=("deep.", "executor_dry_run."),
            applies=bool(expectation.expect_executor_dry_run)
            or has_policy_expectation(expectation.expect_deep),
        ),
    }


def has_policy_expectation(expect_deep: dict[str, Any]) -> bool:
    """Return whether deep expectations assert policy behavior."""
    return any(key in POLICY_EXPECTATION_KEYS for key in expect_deep)


def category_status(
    failures: list[str], *, prefixes: tuple[str, ...], applies: bool
) -> bool | None:
    """Return category status, or None when no expectation covered it."""
    if not applies:
        return None
    return not any(failure.startswith(prefixes) for failure in failures)


def build_benchmark_summary(
    results: list[BenchmarkFixtureResult],
) -> dict[str, Any]:
    """Build aggregate benchmark summary data."""
    passed = sum(1 for result in results if result.passed)
    failed = len(results) - passed
    overall_rate = rate(passed, len(results))
    return {
        "kind": BENCHMARK_SUMMARY_KIND,
        "schema_version": BENCHMARK_SCHEMA_VERSION,
        "fixtures_total": len(results),
        "fixtures_passed": passed,
        "fixtures_failed": failed,
        "overall_rate": overall_rate,
        "snapshot": benchmark_snapshot(passed, len(results), overall_rate),
        "category_rates": {
            category: category_rate(results, category) for category in CATEGORY_NAMES
        },
        "failed_fixtures": [result.name for result in results if not result.passed],
        "fixtures": [result.to_dict() for result in results],
    }


def benchmark_snapshot(
    fixtures_passed: int, fixtures_total: int, overall_rate: float
) -> str:
    """Return the compact benchmark snapshot used by reports and docs."""
    return f"{fixtures_passed}/{fixtures_total} fixtures, overall_rate {overall_rate}"


def category_rate(
    results: list[BenchmarkFixtureResult], category: str
) -> dict[str, int | float]:
    """Calculate pass rate for one benchmark category."""
    applicable = [
        result.categories.get(category)
        for result in results
        if result.categories.get(category) is not None
    ]
    passed = sum(1 for item in applicable if item is True)
    total = len(applicable)
    return {"passed": passed, "total": total, "rate": rate(passed, total)}


def rate(passed: int, total: int) -> float:
    """Return a stable decimal pass rate."""
    if total == 0:
        return 0.0
    return round(passed / total, 4)


def category_coverage_label(category_summary: dict[str, int | float]) -> str:
    """Return whether a category has selected-fixture coverage."""
    return "covered" if int(category_summary["total"]) > 0 else "not covered"


def render_benchmark_report(summary: dict[str, Any]) -> str:
    """Render a human-readable benchmark report."""
    lines = [
        "# QA-Z Benchmark Report",
        "",
        f"- Snapshot: {summary['snapshot']}",
        f"- Fixtures run: {summary['fixtures_total']}",
        f"- Fixtures passed: {summary['fixtures_passed']}",
        f"- Fixtures failed: {summary['fixtures_failed']}",
        f"- Overall pass rate: {summary['overall_rate']}",
        "",
        "## Generated Output Policy",
        "",
        (
            "- `benchmarks/results/summary.json` and "
            "`benchmarks/results/report.md` are generated benchmark outputs."
        ),
        (
            "- They are local by default; commit them only as intentional frozen "
            "evidence with surrounding context."
        ),
        "- `benchmarks/results/work/` is disposable scratch output.",
        "",
        "## Category Rates",
        "",
    ]
    for category, category_summary in summary["category_rates"].items():
        coverage = category_coverage_label(category_summary)
        lines.append(
            "- "
            f"{category}: {category_summary['passed']}/"
            f"{category_summary['total']} "
            f"({category_summary['rate']}, {coverage})"
        )
    lines.extend(["", "## Fixture Results", ""])
    for fixture in summary["fixtures"]:
        status = "passed" if fixture["passed"] else "failed"
        lines.append(f"### {fixture['name']}")
        lines.append("")
        lines.append(f"- Status: {status}")
        failures = fixture.get("failures") or []
        if failures:
            lines.append("- Failures:")
            lines.extend(f"  - {failure}" for failure in failures)
        else:
            lines.append("- Failures: none")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def write_benchmark_artifacts(summary: dict[str, Any], results_dir: Path) -> None:
    """Write benchmark summary JSON and Markdown report artifacts."""
    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (results_dir / "report.md").write_text(
        render_benchmark_report(summary), encoding="utf-8"
    )


def summarize_fast_actual(summary: RunSummary) -> dict[str, Any]:
    """Return benchmark-relevant fast-run observations."""
    failed_checks = [
        check.id for check in summary.checks if check.status in {"failed", "error"}
    ]
    return {
        "status": summary.status,
        "schema_version": summary.schema_version,
        "failed_checks": failed_checks,
        "blocking_failed_checks": failed_checks,
        "passed_checks": [
            check.id for check in summary.checks if check.status == "passed"
        ],
        "warning_checks": [
            check.id for check in summary.checks if check.status == "warning"
        ],
        "totals": summary.totals,
    }


def summarize_deep_actual(summary: RunSummary) -> dict[str, Any]:
    """Return benchmark-relevant deep-run observations."""
    blocking = sum(check.blocking_findings_count or 0 for check in summary.checks)
    findings = sum(check.findings_count or 0 for check in summary.checks)
    filtered = sum(check.filtered_findings_count or 0 for check in summary.checks)
    grouped = sum(len(check.grouped_findings) for check in summary.checks)
    filter_reasons = aggregate_filter_reasons(summary.checks)
    error_types = unique_strings(
        [str(check.error_type or "") for check in summary.checks]
    )
    rule_ids = unique_strings(
        [
            str(finding.get("rule_id") or "")
            for check in summary.checks
            for finding in [*check.findings, *check.grouped_findings]
            if isinstance(finding, dict)
        ]
    )
    return {
        "status": summary.status,
        "schema_version": summary.schema_version,
        "findings": findings,
        "findings_count": findings,
        "blocking_findings": blocking,
        "blocking_findings_count": blocking,
        "filtered_findings_count": filtered,
        "grouped_findings_count": grouped,
        "filter_reasons": filter_reasons,
        "rule_ids": rule_ids,
        "error_types": error_types,
        "config_error": "semgrep_config_error" in error_types,
        "policy": dict(summary.policy),
    }


def summarize_handoff_actual(handoff: RepairHandoffPacket) -> dict[str, Any]:
    """Return benchmark-relevant repair handoff observations."""
    data = handoff.to_dict()
    repair = coerce_mapping(data.get("repair"))
    validation = coerce_mapping(data.get("validation"))
    targets = [
        dict(target) for target in repair.get("targets", []) if isinstance(target, dict)
    ]
    commands = [
        dict(command)
        for command in validation.get("commands", [])
        if isinstance(command, dict)
    ]
    return {
        "kind": data.get("kind"),
        "schema_version": data.get("schema_version"),
        "repair_needed": repair.get("repair_needed"),
        "target_ids": [str(target.get("id")) for target in targets],
        "target_sources": unique_strings(
            [str(target.get("source") or "") for target in targets]
        ),
        "affected_files": list(repair.get("affected_files") or []),
        "validation_command_ids": [str(command.get("id")) for command in commands],
    }


def summarize_verify_actual(comparison: dict[str, Any]) -> dict[str, Any]:
    """Return benchmark-relevant verification observations."""
    summary = coerce_mapping(comparison.get("summary"))
    return {
        "schema_version": VERIFY_SCHEMA_VERSION,
        "verdict": comparison.get("verdict"),
        "blocking_before": summary.get("blocking_before"),
        "blocking_after": summary.get("blocking_after"),
        "resolved_count": summary.get("resolved_count"),
        "remaining_issue_count": summary.get(
            "remaining_issue_count", summary.get("still_failing_count")
        ),
        "new_issue_count": summary.get("new_issue_count"),
        "regression_count": summary.get("regression_count"),
        "not_comparable_count": summary.get("not_comparable_count"),
    }


def summarize_verify_summary_actual(summary: dict[str, Any]) -> dict[str, Any]:
    """Return benchmark-relevant observations from verify/summary.json."""
    return {
        "schema_version": summary.get("schema_version", VERIFY_SCHEMA_VERSION),
        "verdict": summary.get("verdict"),
        "blocking_before": summary.get("blocking_before"),
        "blocking_after": summary.get("blocking_after"),
        "resolved_count": summary.get("resolved_count"),
        "remaining_issue_count": summary.get(
            "remaining_issue_count", summary.get("still_failing_count")
        ),
        "new_issue_count": summary.get("new_issue_count"),
        "regression_count": summary.get("regression_count"),
        "not_comparable_count": summary.get("not_comparable_count"),
    }


def summarize_executor_bridge_actual(
    *, workspace: Path, manifest: dict[str, Any], guide: str
) -> dict[str, Any]:
    """Return benchmark-relevant executor bridge packaging observations."""
    inputs = coerce_mapping(manifest.get("inputs"))
    context_items = inputs.get("action_context", [])
    if not isinstance(context_items, list):
        context_items = []
    action_context = [dict(item) for item in context_items if isinstance(item, dict)]
    copied_paths = [
        str(item.get("copied_path"))
        for item in action_context
        if str(item.get("copied_path") or "").strip()
    ]
    missing_items = inputs.get("action_context_missing", [])
    if not isinstance(missing_items, list):
        missing_items = []
    missing_context = [str(item) for item in missing_items if str(item).strip()]
    stdout = render_bridge_stdout(manifest)
    return {
        "kind": manifest.get("kind"),
        "schema_version": manifest.get("schema_version"),
        "bridge_id": manifest.get("bridge_id"),
        "source_loop_id": manifest.get("source_loop_id"),
        "source_session_id": manifest.get("source_session_id"),
        "prepared_action_type": manifest.get("prepared_action_type"),
        "action_context_count": len(action_context),
        "action_context_paths": [
            str(item.get("source_path"))
            for item in action_context
            if str(item.get("source_path") or "").strip()
        ],
        "action_context_copied_paths": copied_paths,
        "action_context_missing": missing_context,
        "action_context_missing_count": len(missing_context),
        "action_context_files_exist": all(
            (workspace / copied_path).is_file() for copied_path in copied_paths
        ),
        "guide_mentions_action_context": (
            "Action context" in guide
            and all(copied_path in guide for copied_path in copied_paths)
        ),
        "guide_mentions_missing_action_context": (
            "Action context missing" in guide
            and all(missing_path in guide for missing_path in missing_context)
        ),
        "stdout_mentions_action_context": (
            f"Action context inputs: {len(action_context)}" in stdout
        ),
        "stdout_mentions_missing_action_context": (
            "Missing action context:" in stdout
            and all(missing_path in stdout for missing_path in missing_context)
        ),
    }


def summarize_executor_result_actual(summary: dict[str, Any]) -> dict[str, Any]:
    """Return benchmark-relevant executor-result ingest observations."""
    backlog_implications = [
        dict(item)
        for item in summary.get("backlog_implications", [])
        if isinstance(item, dict)
    ]
    freshness_check = coerce_mapping(summary.get("freshness_check"))
    provenance_check = coerce_mapping(summary.get("provenance_check"))
    return {
        "kind": summary.get("kind"),
        "schema_version": summary.get("schema_version"),
        "bridge_id": summary.get("bridge_id"),
        "session_id": summary.get("session_id"),
        "result_status": summary.get("result_status"),
        "ingest_status": summary.get("ingest_status"),
        "session_state": summary.get("session_state"),
        "verification_hint": summary.get("verification_hint"),
        "verification_triggered": summary.get("verification_triggered"),
        "verification_verdict": summary.get("verification_verdict"),
        "verify_resume_status": summary.get("verify_resume_status"),
        "verify_summary_path": summary.get("verify_summary_path"),
        "freshness_status": freshness_check.get("status"),
        "freshness_reason": freshness_check.get("reason"),
        "provenance_status": provenance_check.get("status"),
        "provenance_reason": provenance_check.get("reason"),
        "warning_ids": list(summary.get("warnings") or []),
        "backlog_categories": unique_strings(
            [
                str(item.get("category") or "")
                for item in backlog_implications
                if str(item.get("category") or "").strip()
            ]
        ),
        "next_recommendation": summary.get("next_recommendation"),
    }


def summarize_executor_dry_run_actual(summary: dict[str, Any]) -> dict[str, Any]:
    """Return benchmark-relevant executor dry-run observations."""
    evaluations = [
        dict(item)
        for item in summary.get("rule_evaluations", [])
        if isinstance(item, dict)
    ]
    actions = [
        dict(item)
        for item in summary.get("recommended_actions", [])
        if isinstance(item, dict)
    ]

    def rule_ids(status: str) -> list[str]:
        return [
            str(item.get("id"))
            for item in evaluations
            if str(item.get("id") or "").strip()
            and str(item.get("status") or "").strip() == status
        ]

    counts = summary.get("rule_status_counts")
    rule_counts = counts if isinstance(counts, dict) else {}
    return {
        "kind": summary.get("kind"),
        "schema_version": summary.get("schema_version"),
        "session_id": summary.get("session_id"),
        "summary_source": summary.get("summary_source"),
        "evaluated_attempt_count": summary.get("evaluated_attempt_count"),
        "latest_attempt_id": summary.get("latest_attempt_id"),
        "latest_result_status": summary.get("latest_result_status"),
        "latest_ingest_status": summary.get("latest_ingest_status"),
        "verdict": summary.get("verdict"),
        "verdict_reason": summary.get("verdict_reason"),
        "operator_decision": summary.get("operator_decision"),
        "operator_summary": summary.get("operator_summary"),
        "recommended_action_ids": [
            str(item.get("id")) for item in actions if str(item.get("id") or "").strip()
        ],
        "recommended_action_summaries": [
            str(item.get("summary"))
            for item in actions
            if str(item.get("summary") or "").strip()
        ],
        "history_signals": [
            str(item)
            for item in summary.get("history_signals", [])
            if str(item).strip()
        ],
        "next_recommendation": summary.get("next_recommendation"),
        "clear_rule_count": int(rule_counts.get("clear", 0) or 0),
        "attention_rule_count": int(rule_counts.get("attention", 0) or 0),
        "blocked_rule_count": int(rule_counts.get("blocked", 0) or 0),
        "attention_rule_ids": rule_ids("attention"),
        "blocked_rule_ids": rule_ids("blocked"),
        "clear_rule_ids": rule_ids("clear"),
    }


def summarize_artifact_actual(workspace: Path) -> dict[str, Any]:
    """Return generated artifact files relative to the fixture workspace."""
    runs_dir = workspace / ".qa-z" / "runs"
    if not runs_dir.exists():
        return {"files": []}
    return {
        "files": sorted(
            path.relative_to(workspace).as_posix()
            for path in runs_dir.rglob("*")
            if path.is_file()
        )
    }


def prepare_workspace(fixture: BenchmarkFixture, work_dir: Path) -> Path:
    """Copy fixture repo data into an isolated benchmark workspace."""
    fixture_work_dir = work_dir / fixture.name
    reset_directory(fixture_work_dir)
    workspace = fixture_work_dir / "repo"
    if fixture.repo_path.exists():
        shutil.copytree(fixture.repo_path, workspace)
    else:
        workspace.mkdir(parents=True, exist_ok=True)
    install_support_files(fixture, workspace)
    return workspace


def install_support_files(fixture: BenchmarkFixture, workspace: Path) -> None:
    """Copy shared benchmark support scripts into the isolated workspace."""
    support_dir = fixture.path.parent.parent / "support"
    if not support_dir.exists():
        return

    script_dir = workspace / ".qa-z-benchmark"
    script_dir.mkdir(parents=True, exist_ok=True)
    for support_file in support_dir.glob("*.py"):
        shutil.copy2(support_file, script_dir / support_file.name)

    bin_dir = support_dir / "bin"
    if bin_dir.exists():
        target_bin = workspace / ".qa-z-benchmark-bin"
        shutil.copytree(bin_dir, target_bin, dirs_exist_ok=True)
        for helper in target_bin.iterdir():
            if helper.is_file():
                helper.chmod(helper.stat().st_mode | 0o755)


@contextmanager
def fixture_path_environment(workspace: Path) -> Iterator[None]:
    """Temporarily prepend fixture helper binaries to PATH."""
    bin_dir = workspace / ".qa-z-benchmark-bin"
    original_path = os.environ.get("PATH", "")
    if bin_dir.exists():
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{original_path}"
    try:
        yield
    finally:
        os.environ["PATH"] = original_path


def reset_directory(path: Path) -> None:
    """Remove and recreate a directory."""
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def format_path(path: Path, root: Path) -> str:
    """Return a slash-separated path relative to root when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def read_json_object(path: Path) -> dict[str, Any]:
    """Read an optional JSON object artifact."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data if isinstance(data, dict) else {}


def coerce_mapping(value: object) -> dict[str, Any]:
    """Return a dict copy for JSON-like mappings."""
    if isinstance(value, dict):
        return dict(value)
    return {}


def string_list(value: object) -> list[str]:
    """Return non-empty strings from a JSON-like list."""
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def coerce_number(value: object) -> float | None:
    """Coerce a JSON-like numeric value."""
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def aggregate_filter_reasons(checks: list[Any]) -> dict[str, int]:
    """Aggregate deep filter reasons across checks."""
    reasons: Counter[str] = Counter()
    for check in checks:
        for key, value in check.filter_reasons.items():
            reasons[str(key)] += int(value)
    return dict(sorted(reasons.items()))


def unique_strings(values: list[str]) -> list[str]:
    """Return unique non-empty strings in first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(normalized)
    return result
