"""Architecture tests for benchmark seam modules."""

from __future__ import annotations

import ast
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.benchmark as benchmark_module
import qa_z.benchmark_contracts as benchmark_contracts_module
import qa_z.benchmark_discovery as benchmark_discovery_module
import qa_z.benchmark_fixture_runtime as benchmark_fixture_runtime_module
import qa_z.benchmark_reporting as benchmark_reporting_module
import qa_z.benchmark_runtime as benchmark_runtime_module


def _benchmark_function_names() -> set[str]:
    source = Path(benchmark_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(benchmark_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def _benchmark_class_names() -> set[str]:
    source = Path(benchmark_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(benchmark_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {node.name for node in module_body(tree) if isinstance(node, ast.ClassDef)}


def test_benchmark_contracts_module_exports_match_surface() -> None:
    assert (
        benchmark_contracts_module.BenchmarkExpectation
        is benchmark_module.BenchmarkExpectation
    )
    assert (
        benchmark_contracts_module.BenchmarkFixture is benchmark_module.BenchmarkFixture
    )
    assert (
        benchmark_contracts_module.BenchmarkFixtureResult
        is benchmark_module.BenchmarkFixtureResult
    )
    assert benchmark_contracts_module.BenchmarkError is benchmark_module.BenchmarkError


def test_benchmark_discovery_module_exports_match_surface() -> None:
    assert (
        benchmark_discovery_module.discover_fixtures
        is benchmark_module.discover_fixtures
    )
    assert (
        benchmark_discovery_module.load_fixture_expectation
        is benchmark_module.load_fixture_expectation
    )


def test_benchmark_runtime_module_exports_match_surface() -> None:
    assert benchmark_runtime_module.run_benchmark is benchmark_module.run_benchmark
    assert benchmark_runtime_module.run_fixture is benchmark_module.run_fixture


def test_benchmark_fixture_runtime_module_exports_match_surface() -> None:
    assert callable(benchmark_fixture_runtime_module.run_fixture)
    assert benchmark_module.run_fixture is benchmark_runtime_module.run_fixture


def test_benchmark_reporting_module_exports_match_surface() -> None:
    assert (
        benchmark_reporting_module.render_benchmark_report
        is benchmark_module.render_benchmark_report
    )
    assert (
        benchmark_reporting_module.write_benchmark_artifacts
        is benchmark_module.write_benchmark_artifacts
    )


def test_benchmark_module_keeps_public_defs_out_of_monolith() -> None:
    function_names = _benchmark_function_names()
    class_names = _benchmark_class_names()

    assert "discover_fixtures" not in function_names
    assert "load_fixture_expectation" not in function_names
    assert "_discover_fixtures_impl" not in function_names
    assert "_load_fixture_expectation_impl" not in function_names
    assert "run_benchmark" not in function_names
    assert "_run_benchmark_impl" not in function_names
    assert "run_fixture" not in function_names
    assert "render_benchmark_report" not in function_names
    assert "write_benchmark_artifacts" not in function_names
    assert "_render_benchmark_report_impl" not in function_names
    assert "_write_benchmark_artifacts_impl" not in function_names
    assert "BenchmarkExpectation" not in class_names
    assert "BenchmarkFixture" not in class_names
    assert "BenchmarkFixtureResult" not in class_names
    assert "BenchmarkError" not in class_names


def test_benchmark_module_surface_targets_split_compare_support() -> None:
    source = Path(benchmark_module.__file__).read_text(encoding="utf-8")

    assert "qa_z.benchmark_compare_support" in source
    assert "qa_z.benchmark_expectation_keys" in source
    assert "importlib.import_module" not in source
    assert "import importlib" not in source
