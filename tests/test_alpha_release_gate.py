"""Tests for the alpha release local gate runner."""

from __future__ import annotations

import json

from tests.alpha_release_gate_test_support import (
    RecordingRunner,
    labels_from_result,
    load_gate_module,
)


def test_alpha_release_gate_runs_release_checks_in_publish_order(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 0
    assert result.summary == "alpha release gate passed"
    assert str(result.payload["generated_at"]).endswith("Z")
    assert labels_from_result(result) == [
        "python scripts/alpha_release_preflight.py --skip-remote --json",
        "python scripts/worktree_commit_plan.py --include-ignored --json",
        "python -m ruff format --check .",
        "python -m ruff check .",
        "python -m mypy src tests",
        "python -m pytest",
        "python -m qa_z --help",
        "python -m qa_z init --help",
        "python -m qa_z plan --help",
        "python -m qa_z fast --help",
        "python -m qa_z deep --help",
        "python -m qa_z review --help",
        "python -m qa_z repair-prompt --help",
        "python -m qa_z repair-session --help",
        "python -m qa_z github-summary --help",
        "python -m qa_z verify --help",
        "python -m qa_z benchmark --help",
        "python -m qa_z self-inspect --help",
        "python -m qa_z select-next --help",
        "python -m qa_z backlog --help",
        "python -m qa_z autonomy --help",
        "python -m qa_z executor-bridge --help",
        "python -m qa_z executor-result --help",
        "python -m qa_z fast --selection smart --json",
        "python -m qa_z deep --selection smart --json",
        "python -m qa_z benchmark --json",
        "python -m build --sdist --wheel",
        "python scripts/alpha_release_artifact_smoke.py --json",
        "python scripts/alpha_release_bundle_manifest.py --json",
    ]
    assert [tuple(command) for command in result.commands] == runner.commands


def test_alpha_release_gate_records_failures_but_continues_running(tmp_path):
    module = load_gate_module()
    failing_command = next(
        command.command
        for command in module.default_gate_commands()
        if command.name == "pytest"
    )
    runner = RecordingRunner(
        {tuple(failing_command): (1, "", "pytest failed with one regression\n")}
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.exit_code == 1
    assert result.summary == "alpha release gate failed"
    assert result.payload["check_count"] == len(module.default_gate_commands())
    assert result.payload["passed_count"] == len(module.default_gate_commands()) - 1
    assert result.payload["failed_count"] == 1
    assert result.payload["failed_checks"] == ["pytest"]
    assert len(runner.commands) == len(module.default_gate_commands())
    failed_checks = [
        check for check in result.payload["checks"] if check["status"] == "failed"
    ]
    assert failed_checks == [
        {
            "name": "pytest",
            "label": "python -m pytest",
            "status": "failed",
            "exit_code": 1,
            "stdout_tail": "",
            "stderr_tail": "pytest failed with one regression",
            "failure_scope": "product",
        }
    ]


def test_alpha_release_gate_classifies_environment_failures(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    fast_failure_payload = {
        "status": "failed",
        "checks": [
            {
                "id": "py_type",
                "tool": "mypy",
                "status": "failed",
                "exit_code": 3221225477,
                "stdout_tail": "",
                "stderr_tail": "",
            }
        ],
        "totals": {"passed": 3, "failed": 1, "warning": 0, "skipped": 0},
    }
    deep_failure_payload = {
        "status": "failed",
        "checks": [
            {
                "id": "sg_scan",
                "tool": "semgrep",
                "status": "failed",
                "exit_code": 2,
                "message": "Semgrep failed before producing valid JSON.",
                "stderr_tail": (
                    'Fatal error: exception Failure("Failed to create system store '
                    "X509 authenticator: ca_certs_iter_on_anchors: "
                    'CertOpenSystemStore returned NULL")'
                ),
                "stdout_tail": "",
            }
        ],
        "totals": {"passed": 0, "failed": 1, "warning": 0, "skipped": 0},
    }
    artifact_smoke_payload = {
        "summary": "artifact smoke failed",
        "exit_code": 1,
        "checks": [
            {
                "name": "wheel_install_smoke",
                "status": "passed",
                "detail": "dist\\qa_z-0.9.8a0-py3-none-any.whl installed",
            },
            {
                "name": "sdist_install_smoke",
                "status": "failed",
                "detail": (
                    "artifact install failed with exit 1: "
                    "ERROR: Could not find a version that satisfies the requirement "
                    "setuptools>=68"
                ),
            },
        ],
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["mypy"]): (3221225477, "", ""),
            tuple(commands_by_name["qa_z_fast"]): (
                1,
                json.dumps(fast_failure_payload),
                "",
            ),
            tuple(commands_by_name["qa_z_deep"]): (
                1,
                json.dumps(deep_failure_payload),
                "",
            ),
            tuple(commands_by_name["qa_z_benchmark"]): (
                2,
                (
                    "qa-z benchmark: benchmark error: Benchmark results directory "
                    "is already in use: F:\\JustTyping\\benchmarks\\results. "
                    "Remove stale lock F:\\JustTyping\\benchmarks\\results\\.benchmark.lock "
                    "only after confirming no benchmark is running."
                ),
                "",
            ),
            tuple(commands_by_name["build"]): (
                1,
                "",
                (
                    "ERROR: Could not find a version that satisfies the requirement "
                    "setuptools>=68\n"
                    "ERROR: No matching distribution found for setuptools>=68"
                ),
            ),
            tuple(commands_by_name["artifact_smoke"]): (
                1,
                json.dumps(artifact_smoke_payload),
                "",
            ),
            tuple(commands_by_name["bundle_manifest"]): (
                1,
                "",
                (
                    "Traceback (most recent call last):\n"
                    "PermissionError: [WinError 5] Access is denied: "
                    "'F:\\JustTyping\\dist\\qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle'"
                ),
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.payload["environment_failure_count"] == 7
    assert result.payload["product_failure_count"] == 0
    assert result.payload["evidence"]["gate_failures"] == {
        "mypy": {
            "kind": "mypy_internal_error",
            "summary": "mypy exited with Windows access violation (3221225477)",
        },
        "qa_z_fast": {
            "kind": "fast_typecheck_internal_error",
            "summary": "qa-z fast failed because the nested mypy step crashed",
        },
        "qa_z_deep": {
            "kind": "semgrep_x509_store_failure",
            "summary": "Semgrep could not initialize the Windows X509 authenticator",
        },
        "qa_z_benchmark": {
            "kind": "benchmark_results_lock",
            "summary": "benchmark results directory is locked by another run",
        },
        "build": {
            "kind": "offline_build_dependency_failure",
            "summary": "build could not install setuptools>=68 in the isolated env",
        },
        "artifact_smoke": {
            "kind": "offline_build_dependency_failure",
            "summary": "artifact smoke could not install sdist build dependencies",
        },
        "bundle_manifest": {
            "kind": "bundle_path_locked",
            "summary": "release bundle path could not be replaced because the file is locked",
        },
    }


def test_alpha_release_gate_adds_known_failure_next_actions(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    deep_failure_payload = {
        "status": "failed",
        "checks": [
            {
                "id": "sg_scan",
                "tool": "semgrep",
                "status": "failed",
                "exit_code": 2,
                "message": "Semgrep failed before producing valid JSON.",
                "stderr_tail": (
                    'Fatal error: exception Failure("Failed to create system store '
                    "X509 authenticator: ca_certs_iter_on_anchors: "
                    'CertOpenSystemStore returned NULL")'
                ),
                "stdout_tail": "",
            }
        ],
        "totals": {"passed": 0, "failed": 1, "warning": 0, "skipped": 0},
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["mypy"]): (3221225477, "", ""),
            tuple(commands_by_name["qa_z_deep"]): (
                1,
                json.dumps(deep_failure_payload),
                "",
            ),
            tuple(commands_by_name["qa_z_benchmark"]): (
                2,
                (
                    "qa-z benchmark: benchmark error: Benchmark results directory "
                    "is already in use: F:\\JustTyping\\benchmarks\\results. "
                    "Remove stale lock F:\\JustTyping\\benchmarks\\results\\.benchmark.lock "
                    "only after confirming no benchmark is running."
                ),
                "",
            ),
            tuple(commands_by_name["build"]): (
                1,
                "",
                (
                    "ERROR: Could not find a version that satisfies the requirement "
                    "setuptools>=68\n"
                    "ERROR: No matching distribution found for setuptools>=68"
                ),
            ),
            tuple(commands_by_name["bundle_manifest"]): (
                1,
                "",
                (
                    "Traceback (most recent call last):\n"
                    "PermissionError: [WinError 5] Access is denied: "
                    "'F:\\JustTyping\\dist\\qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle'"
                ),
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.payload["next_actions"] == [
        (
            "Rerun `python -m mypy src tests`; if Windows access violation "
            "3221225477 persists, treat it as a local toolchain/runtime blocker "
            "before triaging code changes."
        ),
        (
            "Repair the local Semgrep trust-store / Windows certificate setup, "
            "then rerun `python -m qa_z deep --selection smart --json`."
        ),
        (
            "Confirm no benchmark is active, remove the stale "
            "`benchmarks/results/.benchmark.lock` only after that check, or use "
            "a different `--results-dir`."
        ),
        (
            "Restore access to build dependencies such as `setuptools>=68`, then "
            "rerun the package build and artifact smoke checks."
        ),
        (
            "Close any process holding the release bundle file, or choose a new "
            "bundle destination, before rerunning the bundle manifest step."
        ),
    ]
    assert result.payload["next_commands"] == [
        "python -m mypy src tests",
        "python -m qa_z deep --selection smart --json",
        "python -m qa_z benchmark --json",
        "python -m build --sdist --wheel",
        "python scripts/alpha_release_artifact_smoke.py --json",
        "python scripts/alpha_release_bundle_manifest.py --json",
    ]


def test_alpha_release_gate_attaches_failure_scope_to_failed_checks(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["mypy"]): (3221225477, "", ""),
            tuple(commands_by_name["pytest"]): (
                1,
                "",
                "pytest failed with one regression\n",
            ),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)
    checks_by_name = {check["name"]: check for check in result.payload["checks"]}

    assert checks_by_name["mypy"]["failure_scope"] == "environment"
    assert checks_by_name["mypy"]["failure_kind"] == "mypy_internal_error"
    assert (
        checks_by_name["mypy"]["failure_summary"]
        == "mypy exited with Windows access violation (3221225477)"
    )
    assert checks_by_name["pytest"]["failure_scope"] == "product"
    assert "failure_kind" not in checks_by_name["pytest"]
    assert "failure_summary" not in checks_by_name["pytest"]


def test_alpha_release_gate_can_include_dependency_smoke(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(tmp_path, with_deps=True, runner=runner)

    assert result.exit_code == 0
    labels = labels_from_result(result)
    assert "python scripts/alpha_release_artifact_smoke.py --with-deps --json" in labels
    assert labels.index("python scripts/alpha_release_artifact_smoke.py --json") < (
        labels.index(
            "python scripts/alpha_release_artifact_smoke.py --with-deps --json"
        )
    )


def test_alpha_release_gate_can_allow_dirty_worktree_for_development(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(tmp_path, allow_dirty=True, runner=runner)

    assert result.exit_code == 0
    assert labels_from_result(result)[0] == (
        "python scripts/alpha_release_preflight.py --skip-remote --allow-dirty --json"
    )


def test_alpha_release_gate_carries_expected_origin_when_origin_is_configured(
    tmp_path, monkeypatch
):
    module = load_gate_module()
    runner = RecordingRunner()
    monkeypatch.setattr(
        module,
        "configured_origin_url_for_gate",
        lambda _repo_root: "https://github.com/qazedhq/qa-z.git",
    )

    result = module.run_alpha_release_gate(tmp_path, allow_dirty=True, runner=runner)

    assert result.exit_code == 0
    assert labels_from_result(result)[0] == (
        "python scripts/alpha_release_preflight.py --skip-remote "
        "--expected-origin-url https://github.com/qazedhq/qa-z.git "
        "--allow-dirty --json"
    )


def test_alpha_release_gate_can_request_strict_worktree_commit_plan(tmp_path):
    module = load_gate_module()
    runner = RecordingRunner()

    result = module.run_alpha_release_gate(
        tmp_path,
        strict_worktree_plan=True,
        runner=runner,
    )

    assert result.exit_code == 0
    assert labels_from_result(result)[1] == (
        "python scripts/worktree_commit_plan.py --include-ignored "
        "--fail-on-generated --fail-on-cross-cutting --json"
    )


def test_alpha_release_gate_promotes_worktree_commit_plan_attention(tmp_path):
    module = load_gate_module()
    worktree_command = next(
        command.command
        for command in module.default_gate_commands(strict_worktree_plan=True)
        if command.name == "worktree_commit_plan"
    )
    worktree_payload = {
        "kind": "qa_z.worktree_commit_plan",
        "status": "attention_required",
        "strict_mode": {
            "fail_on_generated": True,
            "fail_on_cross_cutting": True,
        },
        "attention_reasons": ["generated_artifacts_present"],
        "summary": {
            "changed_batch_count": 2,
            "generated_artifact_count": 3,
            "cross_cutting_count": 1,
            "unassigned_source_path_count": 0,
            "multi_batch_path_count": 0,
        },
        "next_actions": [
            "Remove or ignore generated local artifacts before source staging."
        ],
    }
    runner = RecordingRunner(
        {tuple(worktree_command): (1, json.dumps(worktree_payload), "")}
    )

    result = module.run_alpha_release_gate(
        tmp_path,
        strict_worktree_plan=True,
        runner=runner,
    )

    assert result.exit_code == 1
    assert result.payload["failed_checks"] == ["worktree_commit_plan"]
    assert result.payload["worktree_plan_attention_reasons"] == [
        "generated_artifacts_present"
    ]
    evidence = result.payload["evidence"]["worktree_commit_plan"]
    assert evidence["status"] == "attention_required"
    assert evidence["strict_mode"] == {
        "fail_on_generated": True,
        "fail_on_cross_cutting": True,
    }
    assert evidence["attention_reasons"] == ["generated_artifacts_present"]
    assert evidence["attention_reason_count"] == 1
    assert result.payload["next_actions"] == [
        "Remove or ignore generated local artifacts before source staging."
    ]
    rendered = module.render_alpha_release_gate_human(result.payload)
    assert "attention=generated_artifacts_present" in rendered
    assert "Remove or ignore generated local artifacts" in rendered


def test_alpha_release_gate_deduplicates_promoted_worktree_guidance(tmp_path):
    module = load_gate_module()
    worktree_command = next(
        command.command
        for command in module.default_gate_commands(strict_worktree_plan=True)
        if command.name == "worktree_commit_plan"
    )
    worktree_payload = {
        "kind": "qa_z.worktree_commit_plan",
        "status": "attention_required",
        "attention_reasons": [
            "generated_artifacts_present",
            "generated_artifacts_present",
            "cross_cutting_paths_present",
        ],
        "summary": {},
        "next_actions": [
            "Review generated artifacts before staging.",
            "Review generated artifacts before staging.",
            "Patch-add cross-cutting docs with the owning batch.",
        ],
    }
    runner = RecordingRunner(
        {tuple(worktree_command): (1, json.dumps(worktree_payload), "")}
    )

    result = module.run_alpha_release_gate(
        tmp_path,
        strict_worktree_plan=True,
        runner=runner,
    )

    assert result.payload["worktree_plan_attention_reasons"] == [
        "generated_artifacts_present",
        "cross_cutting_paths_present",
    ]
    assert result.payload["next_actions"] == [
        "Review generated artifacts before staging.",
        "Patch-add cross-cutting docs with the owning batch.",
    ]
