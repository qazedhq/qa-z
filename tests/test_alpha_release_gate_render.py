"""Human render tests for the alpha release local gate runner."""

from __future__ import annotations

import json

from tests.alpha_release_gate_test_support import RecordingRunner, load_gate_module


def test_alpha_release_gate_human_output_prints_gate_failure_summary():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate failed",
            "checks": [],
            "environment_failure_count": 3,
            "product_failure_count": 1,
            "evidence": {
                "gate_failures": {
                    "mypy": {
                        "kind": "mypy_internal_error",
                        "summary": "mypy exited with Windows access violation (3221225477)",
                    },
                    "qa_z_deep": {
                        "kind": "semgrep_x509_store_failure",
                        "summary": (
                            "Semgrep could not initialize the Windows X509 "
                            "authenticator"
                        ),
                    },
                    "build": {
                        "kind": "offline_build_dependency_failure",
                        "summary": (
                            "build could not install setuptools>=68 in the isolated env"
                        ),
                    },
                }
            },
        }
    )

    assert (
        "- gate failures: mypy=mypy_internal_error; "
        "qa_z_deep=semgrep_x509_store_failure; "
        "build=offline_build_dependency_failure"
    ) in output
    assert "- gate blocker classes: environment=3; product=1" in output


def test_alpha_release_gate_human_output_prints_failure_scope_details():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate failed",
            "checks": [
                {
                    "name": "mypy",
                    "label": "python -m mypy src tests",
                    "status": "failed",
                    "exit_code": 3221225477,
                    "stdout_tail": "",
                    "stderr_tail": "",
                    "failure_scope": "environment",
                    "failure_kind": "mypy_internal_error",
                    "failure_summary": (
                        "mypy exited with Windows access violation (3221225477)"
                    ),
                },
                {
                    "name": "pytest",
                    "label": "python -m pytest",
                    "status": "failed",
                    "exit_code": 1,
                    "stdout_tail": "",
                    "stderr_tail": "pytest failed with one regression",
                    "failure_scope": "product",
                },
            ],
        }
    )

    assert (
        "  scope=environment; kind=mypy_internal_error; "
        "why=mypy exited with Windows access violation (3221225477)"
    ) in output
    assert "  scope=product" in output


def test_alpha_release_gate_summarizes_release_evidence(tmp_path):
    module = load_gate_module()
    commands_by_name = {
        command.name: command.command for command in module.default_gate_commands()
    }
    deep_payload = {
        "status": "passed",
        "totals": {"passed": 1, "failed": 0, "warning": 0, "skipped": 0},
        "diagnostics": {
            "scan_quality": {
                "status": "warning",
                "warning_count": 19,
                "warning_types": ["Fixpoint timeout"],
                "warning_paths": ["src/app.py"],
                "check_ids": ["sg_scan"],
            }
        },
    }
    benchmark_payload = {
        "fixtures_passed": 52,
        "fixtures_failed": 0,
        "fixtures_total": 52,
        "overall_rate": 1.0,
        "snapshot": "52/52 fixtures, overall_rate 1.0",
    }
    preflight_payload = {
        "summary": "release preflight passed",
        "exit_code": 0,
        "check_count": 9,
        "passed_count": 6,
        "failed_count": 0,
        "skipped_count": 3,
        "failed_checks": [],
        "repository_target": "qazedhq/qa-z",
        "repository_http_status": 200,
        "repository_probe_state": "probed",
        "repository_probe_generated_at": "2026-04-21T05:00:00Z",
        "expected_origin_target": "qazedhq/qa-z",
        "actual_origin_url": "https://github.com/qazedhq/qa-z.git",
        "origin_state": "configured",
        "remote_path": "direct_publish",
        "skip_remote": False,
        "allow_existing_refs": False,
        "allow_dirty": False,
    }
    artifact_smoke_payload = {
        "summary": "artifact smoke passed",
        "exit_code": 0,
        "checks": [
            {"name": "wheel_install_smoke", "status": "passed"},
            {"name": "sdist_install_smoke", "status": "passed"},
        ],
    }
    bundle_manifest_payload = {
        "summary": "release bundle manifest passed",
        "exit_code": 0,
        "bundle_path": "dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle",
        "checks": [
            {"name": "head_resolves", "status": "passed"},
            {"name": "branch_matches_head", "status": "passed"},
        ],
    }
    build_stdout = (
        "Successfully built qa_z-0.9.8a0.tar.gz and qa_z-0.9.8a0-py3-none-any.whl\n"
    )
    worktree_plan_payload = {
        "status": "ready",
        "repository": {"branch": "main", "head": "abc1234"},
        "summary": {
            "batch_count": 11,
            "changed_batch_count": 8,
            "changed_path_count": 72,
            "generated_artifact_count": 24,
            "generated_local_only_count": 20,
            "generated_local_by_default_count": 4,
            "report_path_count": 3,
            "cross_cutting_count": 4,
            "shared_patch_add_count": 7,
            "unassigned_source_path_count": 0,
            "multi_batch_path_count": 0,
        },
        "next_actions": [
            (
                "Patch-add cross-cutting docs or tests with the feature batch "
                "they describe instead of staging them wholesale."
            )
        ],
    }
    runner = RecordingRunner(
        {
            tuple(commands_by_name["local_preflight"]): (
                0,
                json.dumps(preflight_payload),
                "",
            ),
            tuple(commands_by_name["worktree_commit_plan"]): (
                0,
                json.dumps(worktree_plan_payload),
                "",
            ),
            tuple(commands_by_name["pytest"]): (
                0,
                "============================ 448 passed in 17.10s ============================\n",
                "",
            ),
            tuple(commands_by_name["qa_z_deep"]): (0, json.dumps(deep_payload), ""),
            tuple(commands_by_name["qa_z_benchmark"]): (
                0,
                json.dumps(benchmark_payload),
                "",
            ),
            tuple(commands_by_name["artifact_smoke"]): (
                0,
                json.dumps(artifact_smoke_payload),
                "",
            ),
            tuple(commands_by_name["bundle_manifest"]): (
                0,
                json.dumps(bundle_manifest_payload),
                "",
            ),
            tuple(commands_by_name["build"]): (0, build_stdout, ""),
        }
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)

    assert result.payload["evidence"] == {
        "benchmark": {
            "fixtures_failed": 0,
            "fixtures_passed": 52,
            "fixtures_total": 52,
            "overall_rate": 1.0,
            "snapshot": "52/52 fixtures, overall_rate 1.0",
        },
        "artifact_smoke": {
            "check_count": 2,
            "summary": "artifact smoke passed",
        },
        "bundle_manifest": {
            "bundle_path": "dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle",
            "check_count": 2,
            "summary": "release bundle manifest passed",
        },
        "build": {
            "artifacts": ["qa_z-0.9.8a0.tar.gz", "qa_z-0.9.8a0-py3-none-any.whl"],
            "summary": "Successfully built qa_z-0.9.8a0.tar.gz and qa_z-0.9.8a0-py3-none-any.whl",
        },
        "cli_help": {"check_count": 17, "failed_count": 0},
        "deep": {
            "scan_quality_check_ids": ["sg_scan"],
            "scan_quality_status": "warning",
            "scan_quality_warning_count": 19,
            "scan_quality_warning_paths": ["src/app.py"],
            "scan_quality_warning_types": ["Fixpoint timeout"],
            "status": "passed",
        },
        "local_preflight": {
            "check_count": 9,
            "failed_count": 0,
            "failed_checks": [],
            "passed_count": 6,
            "repository_target": "qazedhq/qa-z",
            "repository_http_status": 200,
            "repository_probe_state": "probed",
            "repository_probe_generated_at": "2026-04-21T05:00:00Z",
            "expected_origin_target": "qazedhq/qa-z",
            "actual_origin_url": "https://github.com/qazedhq/qa-z.git",
            "origin_state": "configured",
            "remote_path": "direct_publish",
            "release_path_state": "remote_direct_publish",
            "skipped_count": 3,
            "summary": "release preflight passed",
            "skip_remote": False,
            "allow_existing_refs": False,
            "allow_dirty": False,
        },
        "pytest": {"passed": 448},
        "worktree_commit_plan": {
            "status": "ready",
            "branch": "main",
            "head": "abc1234",
            "batch_count": 11,
            "changed_batch_count": 8,
            "changed_path_count": 72,
            "generated_artifact_count": 24,
            "generated_local_only_count": 20,
            "generated_local_by_default_count": 4,
            "report_path_count": 3,
            "cross_cutting_count": 4,
            "shared_patch_add_count": 7,
            "unassigned_source_path_count": 0,
            "multi_batch_path_count": 0,
            "next_action_count": 1,
        },
    }


def test_alpha_release_gate_summarizes_pytest_skipped_count(tmp_path):
    module = load_gate_module()

    evidence = module.release_evidence_for_command(
        "pytest",
        (
            "===================== 448 passed, 2 skipped in 17.10s "
            "=====================\n"
        ),
    )
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "checks": [],
            "evidence": {"pytest": evidence},
        }
    )

    assert evidence == {"passed": 448, "skipped": 2}
    assert "- pytest: 448 passed; 2 skipped" in output


def test_alpha_release_gate_human_output_prints_evidence_summary():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "generated_at": "2026-04-21T00:00:00Z",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight passed",
                    "check_count": 9,
                    "passed_count": 6,
                    "failed_count": 0,
                    "skipped_count": 3,
                    "failed_checks": [],
                    "repository_target": "qazedhq/qa-z",
                    "expected_origin_target": "qazedhq/qa-z",
                    "origin_state": "configured",
                    "actual_origin_url": "https://github.com/qazedhq/qa-z.git",
                    "remote_path": "direct_publish",
                    "release_path_state": "remote_direct_publish",
                    "publish_strategy": "push_default_branch",
                    "publish_checklist_count": 3,
                    "skip_remote": False,
                    "allow_existing_refs": False,
                    "allow_dirty": False,
                },
                "pytest": {"passed": 448},
                "deep": {
                    "status": "passed",
                    "scan_quality_status": "warning",
                    "scan_quality_warning_count": 18,
                    "scan_quality_warning_types": ["Fixpoint timeout"],
                    "scan_quality_warning_paths": ["src/app.py"],
                    "scan_quality_check_ids": ["sg_scan"],
                },
                "benchmark": {"snapshot": "52/52 fixtures, overall_rate 1.0"},
                "artifact_smoke": {
                    "summary": "artifact smoke passed",
                    "check_count": 2,
                },
                "bundle_manifest": {
                    "summary": "release bundle manifest passed",
                    "check_count": 2,
                    "bundle_path": "dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle",
                },
                "build": {
                    "summary": (
                        "Successfully built qa_z-0.9.8a0.tar.gz and "
                        "qa_z-0.9.8a0-py3-none-any.whl"
                    ),
                    "artifacts": [
                        "qa_z-0.9.8a0.tar.gz",
                        "qa_z-0.9.8a0-py3-none-any.whl",
                    ],
                },
                "cli_help": {"check_count": 17, "failed_count": 0},
                "worktree_commit_plan": {
                    "status": "ready",
                    "branch": "main",
                    "head": "abc1234",
                    "output_path": "dist/alpha-release-gate.worktree-plan.json",
                    "batch_count": 11,
                    "changed_batch_count": 8,
                    "unchanged_batch_count": 3,
                    "changed_path_count": 72,
                    "generated_artifact_count": 24,
                    "generated_artifact_file_count": 9,
                    "generated_artifact_dir_count": 15,
                    "generated_local_only_count": 20,
                    "generated_local_by_default_count": 4,
                    "report_path_count": 3,
                    "cross_cutting_count": 4,
                    "shared_patch_add_count": 7,
                    "unassigned_source_path_count": 0,
                    "multi_batch_path_count": 0,
                },
            },
        }
    )

    assert "Evidence:" in output
    assert "Generated at: 2026-04-21T00:00:00Z" in output
    assert (
        "- preflight: release preflight passed; checks=9; passed=6; skipped=3; "
        "target=qazedhq/qa-z; origin=qazedhq/qa-z; origin_state=configured; "
        "origin_current=https://github.com/qazedhq/qa-z.git; "
        "path=direct_publish; state=remote_direct_publish; "
        "strategy=push_default_branch; checklist=3; "
        "mode=skip_remote=no,allow_existing_refs=no,allow_dirty=no" in output
    )
    assert "- pytest: 448 passed" in output
    assert "- artifact smoke: artifact smoke passed; checks=2" in output
    assert (
        "- bundle manifest: release bundle manifest passed; checks=2; "
        "bundle=dist/qa-z-v0.9.8-alpha-codex-qa-z-bootstrap.bundle"
    ) in output
    assert (
        "- build: Successfully built qa_z-0.9.8a0.tar.gz and "
        "qa_z-0.9.8a0-py3-none-any.whl"
    ) in output
    assert "- cli help: surfaces=17" in output
    assert (
        "- deep: passed; scan_quality=warning; warnings=18; "
        "warning_types=Fixpoint timeout; warning_paths=src/app.py; "
        "warning_checks=sg_scan"
    ) in output
    assert "- benchmark: 52/52 fixtures, overall_rate 1.0" in output
    assert (
        "- worktree commit plan: ready; batches=11; changed_batches=8; "
        "changed_paths=72; generated_artifacts=24; generated_files=9; "
        "generated_dirs=15; generated_local_only=20; "
        "generated_local_by_default=4; reports=3; cross_cutting=4; "
        "patch_add_candidates=7; unassigned=0; multi_batch=0; "
        "unchanged_batches=3; branch=main; head=abc1234; "
        "output=dist/alpha-release-gate.worktree-plan.json"
    ) in output


def test_alpha_release_gate_human_output_prints_repository_metadata():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight passed",
                    "check_count": 9,
                    "passed_count": 9,
                    "failed_count": 0,
                    "repository_target": "qazedhq/qa-z",
                    "repository_http_status": 200,
                    "repository_probe_state": "probed",
                    "repository_probe_generated_at": "2026-04-21T05:02:00Z",
                    "repository_visibility": "public",
                    "repository_archived": False,
                    "repository_default_branch": "release",
                    "remote_path": "direct_publish",
                    "release_path_state": "remote_direct_publish",
                    "publish_strategy": "push_default_branch",
                    "skip_remote": False,
                    "allow_existing_refs": False,
                    "allow_dirty": False,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight passed; checks=9; passed=9; "
        "target=qazedhq/qa-z; repo_probe=probed; repo_probe_at=2026-04-21T05:02:00Z; repo_http=200; repo_visibility=public; "
        "repo_archived=no; repo_default_branch=release; path=direct_publish; "
        "state=remote_direct_publish; strategy=push_default_branch; "
        "mode=skip_remote=no,allow_existing_refs=no,allow_dirty=no"
    ) in output


def test_alpha_release_gate_human_output_prints_skipped_repository_probe_state():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight passed",
                    "check_count": 9,
                    "passed_count": 6,
                    "repository_target": "qazedhq/qa-z",
                    "repository_probe_state": "skipped",
                    "remote_path": "skipped",
                    "release_path_state": "local_only_bootstrap_origin",
                    "publish_strategy": "bootstrap_origin",
                    "skip_remote": True,
                    "allow_existing_refs": False,
                    "allow_dirty": True,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight passed; checks=9; passed=6; "
        "target=qazedhq/qa-z; repo_probe=skipped; path=skipped; "
        "state=local_only_bootstrap_origin; strategy=bootstrap_origin; "
        "mode=skip_remote=yes,allow_existing_refs=no,allow_dirty=yes"
    ) in output


def test_alpha_release_gate_human_output_prints_last_known_probe_basis():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight passed",
                    "check_count": 9,
                    "passed_count": 6,
                    "repository_target": "qazedhq/qa-z",
                    "repository_probe_state": "skipped",
                    "repository_probe_basis": "last_known",
                    "repository_probe_generated_at": "2026-04-21T05:20:00Z",
                    "repository_probe_freshness": "carried_forward",
                    "repository_probe_age_hours": 1,
                    "repository_http_status": 200,
                    "repository_visibility": "public",
                    "repository_archived": False,
                    "repository_default_branch": "release",
                    "remote_path": "skipped",
                    "release_path_state": "local_only_remote_preflight",
                    "publish_strategy": "remote_preflight",
                    "skip_remote": True,
                    "allow_existing_refs": False,
                    "allow_dirty": True,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight passed; checks=9; passed=6; "
        "target=qazedhq/qa-z; repo_probe=skipped; repo_probe_basis=last_known; "
        "repo_probe_at=2026-04-21T05:20:00Z; repo_probe_freshness=carried_forward; "
        "repo_probe_age_hours=1; repo_http=200; repo_visibility=public; repo_archived=no; "
        "repo_default_branch=release; "
        "path=skipped; state=local_only_remote_preflight; strategy=remote_preflight; "
        "mode=skip_remote=yes,allow_existing_refs=no,allow_dirty=yes"
    ) in output


def test_alpha_release_gate_human_output_prints_preflight_raw_url_fallbacks():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate failed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight failed",
                    "check_count": 9,
                    "passed_count": 4,
                    "failed_count": 2,
                    "repository_url": "https://gitlab.com/qazedhq/qa-z.git",
                    "expected_origin_url": "ssh://git@example.com/qazedhq/qa-z.git",
                    "origin_state": "missing",
                    "remote_path": "blocked",
                    "remote_blocker": "repository_target_mismatch",
                    "skip_remote": False,
                    "allow_existing_refs": False,
                    "allow_dirty": True,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight failed; checks=9; passed=4; failed=2; "
        "target_url=https://gitlab.com/qazedhq/qa-z.git; "
        "origin_url=ssh://git@example.com/qazedhq/qa-z.git; "
        "origin_state=missing; "
        "path=blocked; state=blocked_repository; blocker=repository_target_mismatch; "
        "mode=skip_remote=no,allow_existing_refs=no,allow_dirty=yes"
    ) in output


def test_alpha_release_gate_human_output_prints_unexpected_origin_presence():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate failed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight failed",
                    "check_count": 9,
                    "passed_count": 5,
                    "failed_count": 1,
                    "repository_target": "qazedhq/qa-z",
                    "actual_origin_url": "https://github.com/qazedhq/qa-z.git",
                    "origin_state": "configured",
                    "remote_path": "blocked",
                    "remote_blocker": "origin_present",
                    "skip_remote": True,
                    "allow_existing_refs": False,
                    "allow_dirty": False,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight failed; checks=9; passed=5; failed=1; "
        "target=qazedhq/qa-z; origin_state=configured; "
        "origin_current=https://github.com/qazedhq/qa-z.git; "
        "path=blocked; state=blocked_origin_alignment; blocker=origin_present; "
        "mode=skip_remote=yes,allow_existing_refs=no,allow_dirty=no"
    ) in output


def test_alpha_release_gate_human_output_prints_skipped_remote_readiness():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight passed",
                    "check_count": 9,
                    "passed_count": 6,
                    "failed_count": 0,
                    "repository_target": "qazedhq/qa-z",
                    "origin_state": "missing",
                    "remote_path": "skipped",
                    "remote_readiness": "needs_origin_bootstrap",
                    "skip_remote": True,
                    "allow_existing_refs": False,
                    "allow_dirty": True,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight passed; checks=9; passed=6; "
        "target=qazedhq/qa-z; repo_probe=skipped; origin_state=missing; "
        "path=skipped; state=local_only_bootstrap_origin; "
        "readiness=needs_origin_bootstrap; "
        "mode=skip_remote=yes,allow_existing_refs=no,allow_dirty=yes"
    ) in output


def test_alpha_release_gate_human_output_prints_bootstrap_publish_strategy():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight passed",
                    "check_count": 9,
                    "passed_count": 6,
                    "failed_count": 0,
                    "repository_target": "qazedhq/qa-z",
                    "origin_state": "missing",
                    "remote_path": "skipped",
                    "release_path_state": "local_only_bootstrap_origin",
                    "remote_readiness": "needs_origin_bootstrap",
                    "publish_strategy": "bootstrap_origin",
                    "publish_checklist_count": 2,
                    "next_action_count": 1,
                    "next_command_count": 2,
                    "skip_remote": True,
                    "allow_existing_refs": False,
                    "allow_dirty": True,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight passed; checks=9; passed=6; "
        "target=qazedhq/qa-z; repo_probe=skipped; origin_state=missing; "
        "path=skipped; state=local_only_bootstrap_origin; "
        "readiness=needs_origin_bootstrap; strategy=bootstrap_origin; "
        "next_actions=1; next_commands=2; checklist=2; "
        "mode=skip_remote=yes,allow_existing_refs=no,allow_dirty=yes"
    ) in output


def test_alpha_release_gate_human_output_prints_actual_origin_target():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate failed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight failed",
                    "check_count": 9,
                    "passed_count": 4,
                    "failed_count": 1,
                    "repository_target": "qazedhq/qa-z",
                    "expected_origin_target": "qazedhq/qa-z",
                    "actual_origin_target": "other/qa-z",
                    "actual_origin_url": "git@github.com:other/qa-z.git",
                    "origin_state": "configured",
                    "remote_path": "blocked",
                    "remote_blocker": "origin_mismatch",
                    "skip_remote": True,
                    "allow_existing_refs": False,
                    "allow_dirty": False,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight failed; checks=9; passed=4; failed=1; "
        "target=qazedhq/qa-z; origin=qazedhq/qa-z; origin_state=configured; "
        "origin_current_target=other/qa-z; origin_current=git@github.com:other/qa-z.git; "
        "path=blocked; state=blocked_origin_alignment; blocker=origin_mismatch; "
        "mode=skip_remote=yes,allow_existing_refs=no,allow_dirty=no"
    ) in output


def test_alpha_release_gate_human_output_prints_remote_ref_diagnostics():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate failed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight failed",
                    "check_count": 9,
                    "passed_count": 5,
                    "failed_count": 1,
                    "repository_target": "qazedhq/qa-z",
                    "remote_path": "blocked",
                    "release_path_state": "blocked_existing_refs",
                    "remote_blocker": "existing_refs_present",
                    "remote_ref_count": 2,
                    "remote_ref_head_count": 2,
                    "remote_ref_tag_count": 0,
                    "remote_ref_kinds": ["heads"],
                    "remote_ref_sample": [
                        "refs/heads/main",
                        "refs/heads/release/v0.9.8-alpha",
                    ],
                    "skip_remote": False,
                    "allow_existing_refs": False,
                    "allow_dirty": False,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight failed; checks=9; passed=5; failed=1; "
        "target=qazedhq/qa-z; path=blocked; state=blocked_existing_refs; "
        "blocker=existing_refs_present; "
        "refs=2; head_refs=2; tag_refs=0; ref_kinds=heads; "
        "ref_sample=refs/heads/main,refs/heads/release/v0.9.8-alpha; "
        "mode=skip_remote=no,allow_existing_refs=no,allow_dirty=no"
    ) in output


def test_alpha_release_gate_human_output_prints_remote_check_next_counts():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "checks": [],
            "evidence": {
                "local_preflight": {
                    "summary": "release preflight passed",
                    "check_count": 9,
                    "passed_count": 6,
                    "failed_count": 0,
                    "repository_target": "qazedhq/qa-z",
                    "expected_origin_target": "qazedhq/qa-z",
                    "origin_state": "configured",
                    "actual_origin_url": "git@github.com:qazedhq/qa-z.git",
                    "remote_path": "skipped",
                    "release_path_state": "local_only_remote_preflight",
                    "remote_readiness": "ready_for_remote_checks",
                    "next_action_count": 1,
                    "next_command_count": 1,
                    "skip_remote": True,
                    "allow_existing_refs": False,
                    "allow_dirty": True,
                }
            },
        }
    )

    assert (
        "- preflight: release preflight passed; checks=9; passed=6; "
        "target=qazedhq/qa-z; repo_probe=skipped; origin=qazedhq/qa-z; "
        "origin_state=configured; origin_current=git@github.com:qazedhq/qa-z.git; "
        "path=skipped; state=local_only_remote_preflight; "
        "readiness=ready_for_remote_checks; "
        "next_actions=1; next_commands=1; "
        "mode=skip_remote=yes,allow_existing_refs=no,allow_dirty=yes"
    ) in output


def test_alpha_release_gate_human_output_omits_missing_worktree_counts():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "checks": [],
            "evidence": {
                "worktree_commit_plan": {
                    "status": "ready",
                    "generated_artifact_count": 2,
                }
            },
        }
    )

    assert "- worktree commit plan: ready; generated_artifacts=2" in output
    assert "changed_batches=None" not in output
    assert "cross_cutting=None" not in output
    assert "unassigned=None" not in output
    assert "multi_batch=None" not in output


def test_alpha_release_gate_human_output_normalizes_detached_worktree_branch():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate passed",
            "checks": [],
            "evidence": {
                "worktree_commit_plan": {
                    "status": "ready",
                    "branch": "HEAD",
                    "head": "abc1234",
                }
            },
        }
    )

    assert "- worktree commit plan: ready; branch=detached; head=abc1234" in output
    assert "branch=HEAD" not in output


def test_alpha_release_gate_human_output_prints_nested_artifact_paths():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate failed",
            "generated_at": "2026-04-21T00:00:00Z",
            "preflight_output": "dist/alpha-release-gate.preflight.json",
            "worktree_plan_output": "dist/alpha-release-gate.worktree-plan.json",
            "checks": [],
        }
    )

    assert "Artifacts:" in output
    assert "- preflight: dist/alpha-release-gate.preflight.json" in output
    assert (
        "- worktree commit plan: dist/alpha-release-gate.worktree-plan.json" in output
    )


def test_alpha_release_gate_human_output_prints_worktree_strict_mode():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate failed",
            "generated_at": "2026-04-21T00:00:00Z",
            "checks": [],
            "evidence": {
                "worktree_commit_plan": {
                    "status": "attention_required",
                    "changed_batch_count": 2,
                    "generated_artifact_count": 3,
                    "cross_cutting_count": 1,
                    "unassigned_source_path_count": 0,
                    "multi_batch_path_count": 0,
                    "strict_mode": {
                        "fail_on_generated": True,
                        "fail_on_cross_cutting": True,
                    },
                    "attention_reasons": ["generated_artifacts_present"],
                },
            },
        }
    )

    assert (
        "- worktree commit plan: attention_required; changed_batches=2; "
        "generated_artifacts=3; cross_cutting=1; unassigned=0; multi_batch=0; "
        "strict=fail_on_generated,fail_on_cross_cutting; "
        "attention=generated_artifacts_present"
    ) in output


def test_alpha_release_gate_human_output_prints_worktree_attention_reasons():
    module = load_gate_module()
    output = module.render_alpha_release_gate_human(
        {
            "summary": "alpha release gate failed",
            "generated_at": "2026-04-21T00:00:00Z",
            "worktree_plan_attention_reasons": [
                "generated_artifacts_present",
                "cross_cutting_paths_present",
            ],
            "checks": [],
        }
    )

    assert "Worktree plan attention:" in output
    assert "- generated_artifacts_present" in output
    assert "- cross_cutting_paths_present" in output


def test_alpha_release_gate_human_output_includes_synthesized_dirty_action(tmp_path):
    module = load_gate_module()
    preflight_command = module.default_gate_commands()[0].command
    preflight_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "failed_checks": ["worktree_clean"],
    }
    runner = RecordingRunner(
        {tuple(preflight_command): (1, json.dumps(preflight_payload), "")}
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)
    output = module.render_alpha_release_gate_human(result.payload)

    assert "[FAILED] local_preflight:" in output
    assert "Next actions:" in output
    assert (
        "- Commit, stash, or intentionally rerun with --allow-dirty before "
        "publishing; the worktree_clean check must be clean for release."
    ) in output


def test_alpha_release_gate_human_output_omits_empty_next_actions(tmp_path):
    module = load_gate_module()
    preflight_command = module.default_gate_commands()[0].command
    preflight_payload = {
        "summary": "release preflight failed",
        "exit_code": 1,
        "failed_checks": ["current_branch"],
        "next_actions": [],
    }
    runner = RecordingRunner(
        {tuple(preflight_command): (1, json.dumps(preflight_payload), "")}
    )

    result = module.run_alpha_release_gate(tmp_path, runner=runner)
    output = module.render_alpha_release_gate_human(result.payload)

    assert "[FAILED] local_preflight:" in output
    assert "Next actions:" not in output
    assert output.rstrip().endswith("alpha release gate failed")
