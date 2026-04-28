"""Architecture tests for verification seam modules."""

from __future__ import annotations

import ast
import importlib
from pathlib import Path
from tests.ast_test_support import module_body

import qa_z.verification as verification_module
import qa_z.verification_artifacts as verification_artifacts_module
import qa_z.verification_compare as verification_compare_module
import qa_z.verification_fast_compare as verification_fast_compare_module
import qa_z.verification_delta_models as verification_delta_models_module
import qa_z.verification_finding_support as verification_finding_support_module
import qa_z.verification_models as verification_models_module
import qa_z.verification_outcome as verification_outcome_module
import qa_z.verification_run_models as verification_run_models_module


def _verification_function_names() -> set[str]:
    source = Path(verification_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(verification_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {
        node.name for node in module_body(tree) if isinstance(node, ast.FunctionDef)
    }


def _verification_class_names() -> set[str]:
    source = Path(verification_module.__file__).read_text(encoding="utf-8")
    tree = compile(
        source,
        str(verification_module.__file__),
        "exec",
        flags=ast.PyCF_ONLY_AST,
    )
    return {node.name for node in module_body(tree) if isinstance(node, ast.ClassDef)}


def test_verification_models_module_exports_match_surface() -> None:
    assert (
        verification_models_module.VerificationRun
        is verification_module.VerificationRun
    )
    assert (
        verification_models_module.VerificationComparison
        is verification_module.VerificationComparison
    )
    assert (
        verification_models_module.VerificationArtifactPaths
        is verification_module.VerificationArtifactPaths
    )


def test_verification_run_models_module_exports_match_surface() -> None:
    assert (
        verification_run_models_module.VerificationRun
        is verification_models_module.VerificationRun
    )
    assert (
        verification_run_models_module.VerificationComparison
        is verification_models_module.VerificationComparison
    )
    assert (
        verification_run_models_module.VerificationArtifactPaths
        is verification_models_module.VerificationArtifactPaths
    )


def test_verification_delta_models_module_exports_match_surface() -> None:
    assert (
        verification_delta_models_module.FastCheckDelta
        is verification_models_module.FastCheckDelta
    )
    assert (
        verification_delta_models_module.VerificationFinding
        is verification_models_module.VerificationFinding
    )
    assert (
        verification_delta_models_module.VerificationFindingDelta
        is verification_models_module.VerificationFindingDelta
    )


def test_verification_compare_module_exports_match_surface() -> None:
    assert (
        verification_compare_module.compare_verification_runs
        is verification_module.compare_verification_runs
    )
    assert (
        verification_compare_module.compare_deep_findings
        is verification_module.compare_deep_findings
    )


def test_verification_fast_compare_module_exports_match_surface() -> None:
    assert (
        verification_fast_compare_module.compare_fast_checks
        is verification_module.compare_fast_checks
    )


def test_verification_artifacts_module_exports_match_surface() -> None:
    assert (
        verification_artifacts_module.load_verification_run
        is verification_module.load_verification_run
    )
    assert (
        verification_artifacts_module.write_verification_artifacts
        is verification_module.write_verification_artifacts
    )
    assert (
        verification_artifacts_module.render_verification_report
        is verification_module.render_verification_report
    )


def test_verification_finding_support_module_exports_match_surface() -> None:
    assert (
        verification_finding_support_module.find_matching_candidate
        is verification_module.find_matching_candidate
    )
    assert (
        verification_finding_support_module.extract_deep_findings
        is verification_module.extract_deep_findings
    )
    assert (
        verification_finding_support_module.normalize_active_finding
        is verification_module.normalize_active_finding
    )
    assert (
        verification_finding_support_module.normalize_grouped_finding
        is verification_module.normalize_grouped_finding
    )
    assert (
        verification_finding_support_module.blocking_severities
        is verification_module.blocking_severities
    )


def test_verification_outcome_module_exports_match_surface() -> None:
    assert (
        verification_outcome_module.verification_summary_dict
        is verification_module.verification_summary_dict
    )
    assert (
        verification_outcome_module.verify_exit_code
        is verification_module.verify_exit_code
    )
    assert (
        verification_outcome_module.comparison_json
        is verification_module.comparison_json
    )


def test_verification_module_keeps_compare_and_artifact_defs_out_of_monolith() -> None:
    function_names = _verification_function_names()

    assert "load_verification_run" not in function_names
    assert "compare_verification_runs" not in function_names
    assert "compare_fast_checks" not in function_names
    assert "compare_deep_findings" not in function_names
    assert "_compare_verification_runs_impl" not in function_names
    assert "_compare_fast_checks_impl" not in function_names
    assert "classify_fast_check" not in function_names
    assert "write_verification_artifacts" not in function_names
    assert "render_verification_report" not in function_names
    assert "verification_summary_dict" not in function_names
    assert "verify_exit_code" not in function_names
    assert "comparison_json" not in function_names
    assert "_compare_deep_findings_impl" not in function_names
    assert "find_matching_candidate" not in function_names
    assert "classify_matched_finding" not in function_names
    assert "finding_delta" not in function_names
    assert "extract_deep_findings" not in function_names
    assert "normalize_active_finding" not in function_names
    assert "normalize_grouped_finding" not in function_names
    assert "blocking_severities" not in function_names
    assert "build_comparison_summary" not in function_names
    assert "derive_verdict" not in function_names
    assert "count_blocking_checks" not in function_names
    assert "count_blocking_deep_findings" not in function_names
    assert "count_deep_findings" not in function_names
    assert "is_blocking_check" not in function_names


def test_verification_module_keeps_model_classes_out_of_monolith() -> None:
    class_names = _verification_class_names()

    assert "VerificationRun" not in class_names
    assert "FastCheckDelta" not in class_names
    assert "VerificationFinding" not in class_names
    assert "VerificationFindingDelta" not in class_names
    assert "VerificationComparison" not in class_names
    assert "VerificationArtifactPaths" not in class_names


def test_verification_split_modules_import_together_without_cycle() -> None:
    imported_modules = [
        importlib.import_module("qa_z.verification"),
        importlib.import_module("qa_z.verification_compare"),
        importlib.import_module("qa_z.verification_findings"),
        importlib.import_module("qa_z.verification_models"),
    ]

    assert all(module is not None for module in imported_modules)
