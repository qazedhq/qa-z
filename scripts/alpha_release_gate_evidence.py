"""Release evidence helpers for the deterministic alpha release gate."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Mapping
from typing import Sequence


TAIL_LIMIT = 4000


def output_tail(output: str) -> str:
    return output.strip()[-TAIL_LIMIT:]


def human_repository_branch(branch: object) -> str | None:
    if not isinstance(branch, str) or not branch:
        return None
    return "detached" if branch == "HEAD" else branch


def preflight_next_actions(payload: dict[str, object] | None) -> list[str]:
    if payload is None:
        return []
    actions = payload.get("next_actions")
    if not isinstance(actions, list):
        return []
    return unique_strings(actions)


def preflight_next_commands(payload: dict[str, object] | None) -> list[str]:
    if payload is None:
        return []
    commands = payload.get("next_commands")
    if not isinstance(commands, list):
        return []
    return unique_strings(commands)


def string_list(payload: Mapping[str, object], key: str) -> list[str]:
    values = payload.get(key)
    if not isinstance(values, list):
        return []
    return unique_strings(values)


def unique_strings(values: Sequence[object]) -> list[str]:
    strings: list[str] = []
    seen: set[str] = set()
    for value in values:
        if isinstance(value, str) and value not in seen:
            strings.append(value)
            seen.add(value)
    return strings


def preflight_has_next_actions(payload: dict[str, object] | None) -> bool:
    return payload is not None and isinstance(payload.get("next_actions"), list)


def preflight_failed_checks(payload: dict[str, object] | None) -> list[str]:
    if payload is None:
        return []
    failed_checks = payload.get("failed_checks")
    if not isinstance(failed_checks, list):
        return []
    return [check for check in failed_checks if isinstance(check, str)]


def synthesized_preflight_next_actions(failed_checks: Sequence[str]) -> list[str]:
    """Return fallback preflight repair guidance for older partial payloads."""
    failed = set(failed_checks)
    actions: list[str] = []
    if "worktree_clean" in failed:
        actions.append(
            (
                "Commit, stash, or intentionally rerun with --allow-dirty before "
                "publishing; the worktree_clean check must be clean for release."
            )
        )
    return actions


def preflight_payload(
    stdout: str, output_path: Path | None
) -> dict[str, object] | None:
    return payload_from_stdout_or_file(stdout, output_path)


def payload_from_stdout_or_file(
    stdout: str, output_path: Path | None
) -> dict[str, object] | None:
    payload = parse_json_object(stdout)
    if output_path is None or not output_path.exists():
        return payload
    try:
        file_payload = parse_json_object(output_path.read_text(encoding="utf-8"))
    except OSError:
        return payload
    if payload is None:
        return file_payload
    if file_payload is None:
        return payload
    merged_payload = dict(file_payload)
    merged_payload.update(payload)
    return merged_payload


def release_path_state_from_preflight_evidence(
    evidence: Mapping[str, object],
) -> str | None:
    state = evidence.get("release_path_state")
    if isinstance(state, str) and state:
        return state

    remote_path = evidence.get("remote_path")
    if not isinstance(remote_path, str) or not remote_path:
        return None
    if remote_path == "direct_publish":
        return "remote_direct_publish"
    if remote_path == "release_pr":
        return "remote_release_pr"
    if remote_path == "skipped":
        origin_state = evidence.get("origin_state")
        if origin_state == "missing":
            return "local_only_bootstrap_origin"
        if origin_state == "configured":
            return "local_only_remote_preflight"
        return "local_only_preflight"

    blocker_state = {
        "release_tag_exists": "blocked_existing_tag",
        "existing_refs_present": "blocked_existing_refs",
        "origin_mismatch": "blocked_origin_alignment",
        "origin_target_mismatch": "blocked_origin_alignment",
        "origin_present": "blocked_origin_alignment",
        "repository_target_mismatch": "blocked_repository",
        "repository_not_public": "blocked_repository",
        "repository_archived": "blocked_repository",
        "repository_unavailable": "blocked_repository",
        "repository_missing": "blocked_repository",
        "remote_unreachable": "blocked_remote_access",
    }
    blocker = evidence.get("remote_blocker")
    if isinstance(blocker, str) and blocker:
        return blocker_state.get(blocker, "blocked_remote_publish")
    return "blocked_remote_publish"


def repository_http_status_from_preflight_evidence(
    evidence: Mapping[str, object],
) -> int | None:
    status = evidence.get("repository_http_status")
    if isinstance(status, int) and status > 0:
        return status

    blocker = evidence.get("remote_blocker")
    if blocker == "repository_missing":
        return 404
    return None


def repository_probe_state_from_preflight_evidence(
    evidence: Mapping[str, object],
) -> str | None:
    state = evidence.get("repository_probe_state")
    if isinstance(state, str) and state:
        return state

    repository_http_status = repository_http_status_from_preflight_evidence(evidence)
    if isinstance(repository_http_status, int) and repository_http_status > 0:
        return "probed"

    remote_path = evidence.get("remote_path")
    if remote_path == "skipped":
        return "skipped"
    return None


def repository_probe_basis_from_preflight_evidence(
    evidence: Mapping[str, object],
) -> str | None:
    basis = evidence.get("repository_probe_basis")
    if isinstance(basis, str) and basis:
        return basis
    return None


def parse_json_object(stdout: str) -> dict[str, object] | None:
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict):
        return None
    return payload


def first_failed_nested_check(
    payload: Mapping[str, object],
) -> Mapping[str, object] | None:
    checks = payload.get("checks")
    if not isinstance(checks, list):
        return None
    for check in checks:
        if isinstance(check, Mapping) and check.get("status") == "failed":
            return check
    return None


def output_contains_offline_build_dependency_failure(text: str) -> bool:
    lowered = text.lower()
    return (
        "could not find a version that satisfies the requirement setuptools>=68"
        in lowered
        or "no matching distribution found for setuptools>=68" in lowered
    )


def classify_gate_failure(
    name: str, exit_code: int, stdout_tail: str, stderr_tail: str
) -> dict[str, str] | None:
    combined_output = "\n".join(
        part for part in (stdout_tail.strip(), stderr_tail.strip()) if part
    )

    if name == "mypy" and exit_code == 3221225477:
        return {
            "kind": "mypy_internal_error",
            "summary": "mypy exited with Windows access violation (3221225477)",
            "category": "environment",
        }

    if name == "qa_z_fast":
        payload = parse_json_object(stdout_tail)
        if payload is not None:
            failed_check = first_failed_nested_check(payload)
            if isinstance(failed_check, Mapping):
                tool = str(failed_check.get("tool") or "")
                nested_exit_code = failed_check.get("exit_code")
                if tool == "mypy" and nested_exit_code == 3221225477:
                    return {
                        "kind": "fast_typecheck_internal_error",
                        "summary": "qa-z fast failed because the nested mypy step crashed",
                        "category": "environment",
                    }

    if name == "qa_z_deep":
        payload = parse_json_object(stdout_tail)
        if payload is not None:
            failed_check = first_failed_nested_check(payload)
            if isinstance(failed_check, Mapping):
                tool = str(failed_check.get("tool") or "")
                nested_stderr = str(failed_check.get("stderr_tail") or "")
                lowered_nested_stderr = nested_stderr.lower()
                if tool == "semgrep" and "x509 authenticator" in lowered_nested_stderr:
                    return {
                        "kind": "semgrep_x509_store_failure",
                        "summary": "Semgrep could not initialize the Windows X509 authenticator",
                        "category": "environment",
                    }

    if name == "qa_z_benchmark":
        lowered_output = combined_output.lower()
        if (
            "benchmark results directory is already in use" in lowered_output
            or ".benchmark.lock" in lowered_output
        ):
            return {
                "kind": "benchmark_results_lock",
                "summary": "benchmark results directory is locked by another run",
                "category": "environment",
            }

    if name == "build" and output_contains_offline_build_dependency_failure(
        combined_output
    ):
        return {
            "kind": "offline_build_dependency_failure",
            "summary": "build could not install setuptools>=68 in the isolated env",
            "category": "environment",
        }

    if name == "artifact_smoke":
        payload = parse_json_object(stdout_tail)
        if payload is not None:
            failed_check = first_failed_nested_check(payload)
            if isinstance(failed_check, Mapping):
                detail = str(failed_check.get("detail") or "")
                if output_contains_offline_build_dependency_failure(detail):
                    return {
                        "kind": "offline_build_dependency_failure",
                        "summary": "artifact smoke could not install sdist build dependencies",
                        "category": "environment",
                    }

    if name == "bundle_manifest":
        lowered_output = combined_output.lower()
        if "permissionerror" in lowered_output and ".bundle" in lowered_output:
            return {
                "kind": "bundle_path_locked",
                "summary": "release bundle path could not be replaced because the file is locked",
                "category": "environment",
            }

    return None


def classify_gate_failures(
    checks: Sequence[Mapping[str, object]],
) -> tuple[dict[str, dict[str, str]], int, int]:
    failures: dict[str, dict[str, str]] = {}
    environment_failure_count = 0
    product_failure_count = 0

    for check in checks:
        if check.get("status") == "passed":
            continue
        name = str(check.get("name") or "")
        exit_code = int(check.get("exit_code") or 0)
        stdout_tail = str(check.get("stdout_tail") or "")
        stderr_tail = str(check.get("stderr_tail") or "")
        classification = classify_gate_failure(
            name, exit_code, stdout_tail, stderr_tail
        )
        if classification is None:
            product_failure_count += 1
            continue
        category = classification.pop("category", "product")
        if category == "environment":
            environment_failure_count += 1
        else:
            product_failure_count += 1
        failures[name] = classification

    return failures, environment_failure_count, product_failure_count


def next_actions_for_gate_failures(
    gate_failures: Mapping[str, Mapping[str, str]],
) -> list[str]:
    actions: list[str] = []
    kinds = {
        failure.get("kind")
        for failure in gate_failures.values()
        if isinstance(failure, Mapping) and isinstance(failure.get("kind"), str)
    }
    if "mypy_internal_error" in kinds or "fast_typecheck_internal_error" in kinds:
        actions.append(
            "Rerun `python -m mypy src tests`; if Windows access violation "
            "3221225477 persists, treat it as a local toolchain/runtime blocker "
            "before triaging code changes."
        )
    if "semgrep_x509_store_failure" in kinds:
        actions.append(
            "Repair the local Semgrep trust-store / Windows certificate setup, "
            "then rerun `python -m qa_z deep --selection smart --json`."
        )
    if "benchmark_results_lock" in kinds:
        actions.append(
            "Confirm no benchmark is active, remove the stale "
            "`benchmarks/results/.benchmark.lock` only after that check, or use "
            "a different `--results-dir`."
        )
    if "offline_build_dependency_failure" in kinds:
        actions.append(
            "Restore access to build dependencies such as `setuptools>=68`, then "
            "rerun the package build and artifact smoke checks."
        )
    if "bundle_path_locked" in kinds:
        actions.append(
            "Close any process holding the release bundle file, or choose a new "
            "bundle destination, before rerunning the bundle manifest step."
        )
    return actions


def next_commands_for_gate_failures(
    gate_failures: Mapping[str, Mapping[str, str]],
) -> list[str]:
    commands: list[str] = []
    kinds = {
        failure.get("kind")
        for failure in gate_failures.values()
        if isinstance(failure, Mapping) and isinstance(failure.get("kind"), str)
    }
    if "mypy_internal_error" in kinds or "fast_typecheck_internal_error" in kinds:
        commands.append("python -m mypy src tests")
    if "semgrep_x509_store_failure" in kinds:
        commands.append("python -m qa_z deep --selection smart --json")
    if "benchmark_results_lock" in kinds:
        commands.append("python -m qa_z benchmark --json")
    if "offline_build_dependency_failure" in kinds:
        commands.extend(
            [
                "python -m build --sdist --wheel",
                "python scripts/alpha_release_artifact_smoke.py --json",
            ]
        )
    if "bundle_path_locked" in kinds:
        commands.append("python scripts/alpha_release_bundle_manifest.py --json")
    return unique_strings(commands)


def release_evidence_for_command(
    name: str, stdout: str, output_path: Path | None = None
) -> dict[str, object] | None:
    """Extract compact release evidence from verbose gate command output."""
    if name == "local_preflight":
        payload = payload_from_stdout_or_file(stdout, output_path)
        if payload is None:
            return None
        evidence = {
            "summary": payload.get("summary"),
            "check_count": payload.get("check_count"),
            "passed_count": payload.get("passed_count"),
            "failed_count": payload.get("failed_count"),
            "skipped_count": payload.get("skipped_count"),
            "failed_checks": payload.get("failed_checks"),
        }
        for optional_key in (
            "repository_target",
            "repository_visibility",
            "repository_default_branch",
            "repository_probe_generated_at",
            "repository_probe_freshness",
            "expected_origin_target",
            "actual_origin_target",
            "repository_url",
            "expected_origin_url",
            "actual_origin_url",
            "origin_state",
            "remote_path",
            "release_path_state",
            "remote_readiness",
            "publish_strategy",
            "remote_blocker",
        ):
            value = payload.get(optional_key)
            if isinstance(value, str) and value:
                evidence[optional_key] = value
        repository_http_status = repository_http_status_from_preflight_evidence(payload)
        if isinstance(repository_http_status, int) and repository_http_status > 0:
            evidence["repository_http_status"] = repository_http_status
        repository_probe_state = repository_probe_state_from_preflight_evidence(payload)
        if isinstance(repository_probe_state, str) and repository_probe_state:
            evidence["repository_probe_state"] = repository_probe_state
        repository_probe_basis = repository_probe_basis_from_preflight_evidence(payload)
        if isinstance(repository_probe_basis, str) and repository_probe_basis:
            evidence["repository_probe_basis"] = repository_probe_basis
        repository_probe_generated_at = payload.get("repository_probe_generated_at")
        if (
            isinstance(repository_probe_generated_at, str)
            and repository_probe_generated_at
        ):
            evidence["repository_probe_generated_at"] = repository_probe_generated_at
        repository_probe_age_hours = payload.get("repository_probe_age_hours")
        if (
            isinstance(repository_probe_age_hours, int)
            and repository_probe_age_hours >= 0
        ):
            evidence["repository_probe_age_hours"] = repository_probe_age_hours
        repository_archived = payload.get("repository_archived")
        if isinstance(repository_archived, bool):
            evidence["repository_archived"] = repository_archived
        release_path_state = release_path_state_from_preflight_evidence(payload)
        if isinstance(release_path_state, str) and release_path_state:
            evidence["release_path_state"] = release_path_state
        remote_ref_count = payload.get("remote_ref_count")
        if isinstance(remote_ref_count, int) and remote_ref_count > 0:
            evidence["remote_ref_count"] = remote_ref_count
        remote_ref_head_count = payload.get("remote_ref_head_count")
        if isinstance(remote_ref_head_count, int) and remote_ref_head_count >= 0:
            evidence["remote_ref_head_count"] = remote_ref_head_count
        remote_ref_tag_count = payload.get("remote_ref_tag_count")
        if isinstance(remote_ref_tag_count, int) and remote_ref_tag_count >= 0:
            evidence["remote_ref_tag_count"] = remote_ref_tag_count
        remote_ref_kinds = payload.get("remote_ref_kinds")
        if isinstance(remote_ref_kinds, list):
            kind_values = unique_strings(remote_ref_kinds)
            if kind_values:
                evidence["remote_ref_kinds"] = kind_values
        remote_ref_sample = payload.get("remote_ref_sample")
        if isinstance(remote_ref_sample, list):
            sample_values = unique_strings(remote_ref_sample)
            if sample_values:
                evidence["remote_ref_sample"] = sample_values
        for mode_key in ("skip_remote", "allow_existing_refs", "allow_dirty"):
            value = payload.get(mode_key)
            if isinstance(value, bool):
                evidence[mode_key] = value
        for count_key in (
            "tracked_generated_artifact_count",
            "generated_local_only_tracked_count",
            "generated_local_by_default_tracked_count",
        ):
            value = payload.get(count_key)
            if isinstance(value, int) and value >= 0:
                evidence[count_key] = value
        next_actions = payload.get("next_actions")
        if isinstance(next_actions, list):
            evidence["next_action_count"] = len(unique_strings(next_actions))
        next_commands = payload.get("next_commands")
        if isinstance(next_commands, list):
            evidence["next_command_count"] = len(unique_strings(next_commands))
        publish_checklist = payload.get("publish_checklist")
        if isinstance(publish_checklist, list):
            evidence["publish_checklist_count"] = len(unique_strings(publish_checklist))
        return evidence
    if name == "pytest":
        match = re.search(r"\b(\d+)\s+passed\b", stdout)
        if match:
            pytest_evidence: dict[str, object] = {"passed": int(match.group(1))}
            skipped_match = re.search(r"\b(\d+)\s+skipped\b", stdout)
            if skipped_match:
                pytest_evidence["skipped"] = int(skipped_match.group(1))
            return pytest_evidence
        return None
    if name == "artifact_smoke":
        payload = parse_json_object(stdout)
        if payload is None:
            return None
        checks = payload.get("checks")
        return {
            "summary": payload.get("summary"),
            "check_count": len(checks) if isinstance(checks, list) else 0,
        }
    if name == "bundle_manifest":
        payload = parse_json_object(stdout)
        if payload is None:
            return None
        checks = payload.get("checks")
        return {
            "summary": payload.get("summary"),
            "check_count": len(checks) if isinstance(checks, list) else 0,
            "bundle_path": payload.get("bundle_path"),
        }
    if name == "build":
        summary = output_tail(stdout)
        match = re.search(r"Successfully built (.+)", stdout)
        if match:
            summary = match.group(0).strip()
            artifacts = re.split(r"\s+and\s+|\s+", match.group(1).strip())
            artifact_names = [artifact for artifact in artifacts if artifact]
            return {
                "summary": summary,
                "artifacts": artifact_names,
            }
        return {"summary": summary} if summary else None
    if name == "qa_z_deep":
        payload = parse_json_object(stdout)
        if payload is None:
            return None
        evidence: dict[str, object] = {"status": payload.get("status")}
        diagnostics = payload.get("diagnostics")
        scan_quality = (
            diagnostics.get("scan_quality") if isinstance(diagnostics, dict) else None
        )
        if isinstance(scan_quality, dict):
            evidence.update(
                {
                    "scan_quality_status": scan_quality.get("status"),
                    "scan_quality_warning_count": scan_quality.get("warning_count"),
                    "scan_quality_warning_types": scan_quality.get("warning_types"),
                    "scan_quality_warning_paths": scan_quality.get("warning_paths"),
                    "scan_quality_check_ids": scan_quality.get("check_ids"),
                }
            )
        return evidence
    if name == "qa_z_benchmark":
        payload = parse_json_object(stdout)
        if payload is None:
            return None
        fixtures_passed = payload.get("fixtures_passed")
        fixtures_total = payload.get("fixtures_total")
        overall_rate = payload.get("overall_rate")
        snapshot = payload.get("snapshot")
        if not isinstance(snapshot, str):
            snapshot = benchmark_snapshot_from_counts(
                fixtures_passed, fixtures_total, overall_rate
            )
        return {
            "fixtures_failed": payload.get("fixtures_failed"),
            "fixtures_passed": fixtures_passed,
            "fixtures_total": fixtures_total,
            "overall_rate": overall_rate,
            "snapshot": snapshot,
        }
    if name == "worktree_commit_plan":
        payload = payload_from_stdout_or_file(stdout, output_path)
        if payload is None:
            return None
        summary = payload.get("summary")
        if not isinstance(summary, dict):
            summary = {}
        repository = payload.get("repository")
        if not isinstance(repository, dict):
            repository = {}
        next_actions = payload.get("next_actions")
        evidence = {
            "status": payload.get("status"),
            "changed_batch_count": summary.get("changed_batch_count"),
            "generated_artifact_count": summary.get("generated_artifact_count"),
            "report_path_count": summary.get("report_path_count"),
            "cross_cutting_count": summary.get("cross_cutting_count"),
            "shared_patch_add_count": summary.get("shared_patch_add_count"),
            "unassigned_source_path_count": summary.get("unassigned_source_path_count"),
            "multi_batch_path_count": summary.get("multi_batch_path_count"),
            "next_action_count": len(next_actions)
            if isinstance(next_actions, list)
            else 0,
        }
        branch = repository.get("branch")
        if isinstance(branch, str) and branch:
            evidence["branch"] = branch
        head = repository.get("head")
        if isinstance(head, str) and head:
            evidence["head"] = head
        for optional_count_key in (
            "batch_count",
            "changed_path_count",
            "generated_artifact_file_count",
            "generated_artifact_dir_count",
            "generated_local_only_count",
            "generated_local_by_default_count",
            "cross_cutting_group_count",
        ):
            optional_count = summary.get(optional_count_key)
            if isinstance(optional_count, int):
                evidence[optional_count_key] = optional_count
        unchanged_batch_count = summary.get("unchanged_batch_count")
        if isinstance(unchanged_batch_count, int):
            evidence["unchanged_batch_count"] = unchanged_batch_count
        kind = payload.get("kind")
        if isinstance(kind, str):
            evidence["kind"] = kind
        schema_version = payload.get("schema_version")
        if isinstance(schema_version, int):
            evidence["schema_version"] = schema_version
        output_path_value = payload.get("output_path")
        if isinstance(output_path_value, str):
            evidence["output_path"] = output_path_value
        attention_reasons = string_list(payload, "attention_reasons")
        if attention_reasons:
            evidence["attention_reasons"] = attention_reasons
            evidence["attention_reason_count"] = len(attention_reasons)
        strict_mode = payload.get("strict_mode")
        if isinstance(strict_mode, dict):
            strict_flags = {
                key: strict_mode[key]
                for key in ("fail_on_generated", "fail_on_cross_cutting")
                if isinstance(strict_mode.get(key), bool)
            }
            if strict_flags:
                evidence["strict_mode"] = strict_flags
        return evidence
    return None


def benchmark_snapshot_from_counts(
    fixtures_passed: object, fixtures_total: object, overall_rate: object
) -> str | None:
    """Build the compact benchmark snapshot from legacy counter-only payloads."""
    if (
        isinstance(fixtures_passed, int)
        and isinstance(fixtures_total, int)
        and overall_rate is not None
    ):
        return (
            f"{fixtures_passed}/{fixtures_total} fixtures, overall_rate {overall_rate}"
        )
    return None


def release_evidence_consistency_errors(evidence: Mapping[str, object]) -> list[str]:
    """Return deterministic consistency errors for summarized release evidence."""
    errors: list[str] = []
    preflight_evidence = evidence.get("local_preflight")
    if isinstance(preflight_evidence, Mapping):
        repository_probe_state = repository_probe_state_from_preflight_evidence(
            preflight_evidence
        )
        repository_probe_basis = repository_probe_basis_from_preflight_evidence(
            preflight_evidence
        )
        repository_probe_generated_at = preflight_evidence.get(
            "repository_probe_generated_at"
        )
        repository_probe_freshness = preflight_evidence.get(
            "repository_probe_freshness"
        )
        repository_probe_age_hours = preflight_evidence.get(
            "repository_probe_age_hours"
        )
        if repository_probe_basis == "last_known":
            if not (
                isinstance(repository_probe_generated_at, str)
                and repository_probe_generated_at
                and repository_probe_freshness in {"carried_forward", "stale"}
                and isinstance(repository_probe_age_hours, int)
                and repository_probe_age_hours >= 0
            ):
                errors.append(
                    "preflight carried probe freshness missing: "
                    "repository_probe_basis=last_known requires "
                    "repository_probe_generated_at, repository_probe_freshness, and "
                    "repository_probe_age_hours"
                )
            if repository_probe_state != "skipped":
                errors.append(
                    "preflight carried probe basis mismatch: "
                    "repository_probe_basis=last_known requires "
                    "repository_probe_state=skipped"
                )
        wrong_target_probe_evidence = preflight_evidence.get(
            "remote_blocker"
        ) == "repository_target_mismatch" and (
            repository_probe_state == "probed"
            or isinstance(
                repository_http_status_from_preflight_evidence(preflight_evidence), int
            )
        )
        if wrong_target_probe_evidence:
            errors.append(
                "preflight wrong-target probe evidence mismatch: "
                "repository_target_mismatch must not report "
                "repository_probe_state or repository_http_status"
            )
        if repository_probe_state == "probed":
            if not wrong_target_probe_evidence and (
                repository_probe_freshness != "current"
                or repository_probe_age_hours != 0
            ):
                errors.append(
                    "preflight current probe freshness mismatch: "
                    "repository_probe_state=probed requires "
                    "repository_probe_freshness=current and "
                    "repository_probe_age_hours=0"
                )
        elif repository_probe_freshness == "current":
            errors.append(
                "preflight current probe freshness mismatch: "
                "repository_probe_freshness=current requires "
                "repository_probe_state=probed"
            )
    benchmark_evidence = evidence.get("benchmark")
    if isinstance(benchmark_evidence, Mapping):
        passed = benchmark_evidence.get("fixtures_passed")
        total = benchmark_evidence.get("fixtures_total")
        overall_rate = benchmark_evidence.get("overall_rate")
        snapshot = benchmark_evidence.get("snapshot")
        expected_snapshot = benchmark_snapshot_from_counts(passed, total, overall_rate)
        if expected_snapshot is not None and isinstance(snapshot, str):
            if snapshot != expected_snapshot:
                errors.append(
                    "benchmark snapshot mismatch: snapshot is "
                    f"'{snapshot}' but counters imply '{expected_snapshot}'"
                )
    worktree_evidence = evidence.get("worktree_commit_plan")
    if isinstance(worktree_evidence, Mapping):
        generated_count = worktree_evidence.get("generated_artifact_count")
        generated_file_count = worktree_evidence.get("generated_artifact_file_count")
        generated_dir_count = worktree_evidence.get("generated_artifact_dir_count")
        generated_local_only_count = worktree_evidence.get("generated_local_only_count")
        generated_local_by_default_count = worktree_evidence.get(
            "generated_local_by_default_count"
        )
        cross_cutting_group_count = worktree_evidence.get("cross_cutting_group_count")
        shared_patch_add_count = worktree_evidence.get("shared_patch_add_count")
        if (
            isinstance(generated_count, int)
            and isinstance(generated_file_count, int)
            and isinstance(generated_dir_count, int)
        ):
            split_total = generated_file_count + generated_dir_count
            if generated_count != split_total:
                errors.append(
                    "worktree generated artifact split mismatch: "
                    f"generated_artifact_count is {generated_count} but file plus "
                    f"directory counts imply {split_total}"
                )
        if (
            isinstance(generated_count, int)
            and isinstance(generated_local_only_count, int)
            and isinstance(generated_local_by_default_count, int)
        ):
            policy_total = generated_local_only_count + generated_local_by_default_count
            if generated_count != policy_total:
                errors.append(
                    "worktree generated artifact policy split mismatch: "
                    f"generated_artifact_count is {generated_count} but local-only "
                    f"plus local-by-default counts imply {policy_total}"
                )
        if isinstance(cross_cutting_group_count, int) and isinstance(
            shared_patch_add_count, int
        ):
            if cross_cutting_group_count > shared_patch_add_count:
                errors.append(
                    "worktree patch-add group mismatch: "
                    f"cross_cutting_group_count is {cross_cutting_group_count} but "
                    f"shared_patch_add_count is {shared_patch_add_count}"
                )
    return errors


def release_evidence_consistency_next_actions(errors: Sequence[str]) -> list[str]:
    """Return deterministic repair guidance for release evidence mismatches."""
    actions: list[str] = []
    if any(error.startswith("benchmark snapshot mismatch") for error in errors):
        actions.append(
            "Rerun the alpha release gate and inspect `python -m qa_z benchmark "
            "--json`; publish only after benchmark counters and snapshot agree."
        )
    if any(
        error.startswith("worktree generated artifact split mismatch")
        for error in errors
    ):
        actions.append(
            "Rerun `python scripts/worktree_commit_plan.py --include-ignored "
            "--json` and the alpha release gate; publish only after generated "
            "artifact totals and split counts agree."
        )
    if any(
        error.startswith("worktree generated artifact policy split mismatch")
        for error in errors
    ):
        actions.append(
            "Rerun `python scripts/worktree_commit_plan.py --include-ignored "
            "--json` and the alpha release gate; publish only after generated "
            "artifact totals and policy-bucket counts agree."
        )
    if any(error.startswith("worktree patch-add group mismatch") for error in errors):
        actions.append(
            "Rerun `python scripts/worktree_commit_plan.py --summary-only "
            "--json` and the alpha release gate; publish only after shared "
            "patch-add group counts agree."
        )
    if any(error.startswith("preflight carried probe freshness") for error in errors):
        actions.append(
            "Rerun `python scripts/alpha_release_preflight.py --skip-remote "
            "--output <path> --json` or the alpha release gate so carried "
            "probe basis, freshness, and age fields come from one consistent "
            "preflight artifact."
        )
    if any(
        error.startswith("preflight current probe freshness mismatch")
        for error in errors
    ):
        actions.append(
            "Rerun remote preflight or the alpha release gate so the current "
            "probe freshness fields are regenerated from one live preflight run."
        )
    return actions


def render_alpha_release_gate_human(payload: Mapping[str, object]) -> str:
    lines: list[str] = []
    generated_at = str(payload.get("generated_at") or "").strip()
    if generated_at:
        lines.append(f"Generated at: {generated_at}")
    artifact_lines = render_nested_artifact_lines(payload)
    if artifact_lines:
        if lines:
            lines.append("")
        lines.append("Artifacts:")
        lines.extend(artifact_lines)
    checks = payload.get("checks")
    if isinstance(checks, list):
        for check in checks:
            if not isinstance(check, dict):
                continue
            status = str(check.get("status", "unknown")).upper()
            name = str(check.get("name", "unknown"))
            label = str(check.get("label", ""))
            lines.append(f"[{status}] {name}: {label}")
            if check.get("status") != "passed":
                detail = check.get("stderr_tail") or check.get("stdout_tail")
                if detail:
                    lines.append(f"  {detail}")
                failure_parts: list[str] = []
                failure_scope = check.get("failure_scope")
                if isinstance(failure_scope, str) and failure_scope:
                    failure_parts.append(f"scope={failure_scope}")
                failure_kind = check.get("failure_kind")
                if isinstance(failure_kind, str) and failure_kind:
                    failure_parts.append(f"kind={failure_kind}")
                failure_summary = check.get("failure_summary")
                if isinstance(failure_summary, str) and failure_summary:
                    failure_parts.append(f"why={failure_summary}")
                if failure_parts:
                    lines.append(f"  {'; '.join(failure_parts)}")

    evidence_lines = render_release_evidence_lines(payload.get("evidence"))
    blocker_class_parts: list[str] = []
    environment_failure_count = payload.get("environment_failure_count")
    if isinstance(environment_failure_count, int):
        blocker_class_parts.append(f"environment={environment_failure_count}")
    product_failure_count = payload.get("product_failure_count")
    if isinstance(product_failure_count, int):
        blocker_class_parts.append(f"product={product_failure_count}")
    if evidence_lines or blocker_class_parts:
        if lines:
            lines.append("")
        lines.append("Evidence:")
        lines.extend(evidence_lines)
        if blocker_class_parts:
            lines.append(f"- gate blocker classes: {'; '.join(blocker_class_parts)}")

    worktree_attention_lines = render_worktree_plan_attention_lines(payload)
    if worktree_attention_lines:
        if lines:
            lines.append("")
        lines.append("Worktree plan attention:")
        lines.extend(worktree_attention_lines)

    next_actions = payload.get("next_actions")
    if isinstance(next_actions, list) and next_actions:
        if lines:
            lines.append("")
        lines.append("Next actions:")
        for action in unique_strings(next_actions):
            lines.append(f"- {action}")

    next_commands = payload.get("next_commands")
    if isinstance(next_commands, list) and next_commands:
        if lines:
            lines.append("")
        lines.append("Next commands:")
        for command in unique_strings(next_commands):
            lines.append(f"- {command}")

    summary = payload.get("summary")
    if isinstance(summary, str):
        lines.append(summary)
    return "\n".join(lines) + "\n"


def render_worktree_plan_attention_lines(payload: Mapping[str, object]) -> list[str]:
    reasons = payload.get("worktree_plan_attention_reasons")
    if not isinstance(reasons, list):
        return []
    return [f"- {reason}" for reason in reasons if isinstance(reason, str)]


def render_nested_artifact_lines(payload: Mapping[str, object]) -> list[str]:
    lines: list[str] = []
    preflight_output = payload.get("preflight_output")
    if isinstance(preflight_output, str) and preflight_output.strip():
        lines.append(f"- preflight: {preflight_output}")
    worktree_plan_output = payload.get("worktree_plan_output")
    if isinstance(worktree_plan_output, str) and worktree_plan_output.strip():
        lines.append(f"- worktree commit plan: {worktree_plan_output}")
    return lines


def render_release_evidence_lines(evidence: object) -> list[str]:
    """Render compact release evidence lines for human gate output."""
    if not isinstance(evidence, Mapping):
        return []
    lines: list[str] = []
    preflight_evidence = evidence.get("local_preflight")
    if isinstance(preflight_evidence, Mapping):
        preflight_parts = [str(preflight_evidence.get("summary") or "unknown")]
        for label, key in (("checks", "check_count"), ("passed", "passed_count")):
            value = preflight_evidence.get(key)
            if value is not None:
                preflight_parts.append(f"{label}={value}")
        failed_count = preflight_evidence.get("failed_count")
        if failed_count not in (None, 0):
            preflight_parts.append(f"failed={failed_count}")
        skipped_count = preflight_evidence.get("skipped_count")
        if skipped_count not in (None, 0):
            preflight_parts.append(f"skipped={skipped_count}")
        repository_target = preflight_evidence.get("repository_target")
        if isinstance(repository_target, str) and repository_target:
            preflight_parts.append(f"target={repository_target}")
        else:
            repository_url = preflight_evidence.get("repository_url")
            if isinstance(repository_url, str) and repository_url:
                preflight_parts.append(f"target_url={repository_url}")
        repository_http_status = repository_http_status_from_preflight_evidence(
            preflight_evidence
        )
        repository_probe_state = repository_probe_state_from_preflight_evidence(
            preflight_evidence
        )
        if isinstance(repository_probe_state, str) and repository_probe_state:
            preflight_parts.append(f"repo_probe={repository_probe_state}")
        repository_probe_basis = repository_probe_basis_from_preflight_evidence(
            preflight_evidence
        )
        if isinstance(repository_probe_basis, str) and repository_probe_basis:
            preflight_parts.append(f"repo_probe_basis={repository_probe_basis}")
        repository_probe_generated_at = preflight_evidence.get(
            "repository_probe_generated_at"
        )
        if (
            isinstance(repository_probe_generated_at, str)
            and repository_probe_generated_at
        ):
            preflight_parts.append(f"repo_probe_at={repository_probe_generated_at}")
        repository_probe_freshness = preflight_evidence.get(
            "repository_probe_freshness"
        )
        if isinstance(repository_probe_freshness, str) and repository_probe_freshness:
            preflight_parts.append(f"repo_probe_freshness={repository_probe_freshness}")
        repository_probe_age_hours = preflight_evidence.get(
            "repository_probe_age_hours"
        )
        if (
            isinstance(repository_probe_age_hours, int)
            and repository_probe_age_hours >= 0
        ):
            preflight_parts.append(f"repo_probe_age_hours={repository_probe_age_hours}")
        if isinstance(repository_http_status, int) and repository_http_status > 0:
            preflight_parts.append(f"repo_http={repository_http_status}")
        repository_visibility = preflight_evidence.get("repository_visibility")
        if isinstance(repository_visibility, str) and repository_visibility:
            preflight_parts.append(f"repo_visibility={repository_visibility}")
        repository_archived = preflight_evidence.get("repository_archived")
        if isinstance(repository_archived, bool):
            preflight_parts.append(
                f"repo_archived={'yes' if repository_archived else 'no'}"
            )
        repository_default_branch = preflight_evidence.get("repository_default_branch")
        if isinstance(repository_default_branch, str) and repository_default_branch:
            preflight_parts.append(f"repo_default_branch={repository_default_branch}")
        expected_origin_target = preflight_evidence.get("expected_origin_target")
        if isinstance(expected_origin_target, str) and expected_origin_target:
            preflight_parts.append(f"origin={expected_origin_target}")
        else:
            expected_origin_url = preflight_evidence.get("expected_origin_url")
            if isinstance(expected_origin_url, str) and expected_origin_url:
                preflight_parts.append(f"origin_url={expected_origin_url}")
        origin_state = preflight_evidence.get("origin_state")
        if isinstance(origin_state, str) and origin_state:
            preflight_parts.append(f"origin_state={origin_state}")
        actual_origin_url = preflight_evidence.get("actual_origin_url")
        actual_origin_target = preflight_evidence.get("actual_origin_target")
        if isinstance(actual_origin_target, str) and actual_origin_target:
            preflight_parts.append(f"origin_current_target={actual_origin_target}")
        if isinstance(actual_origin_url, str) and actual_origin_url:
            preflight_parts.append(f"origin_current={actual_origin_url}")
        remote_path = preflight_evidence.get("remote_path")
        if isinstance(remote_path, str) and remote_path:
            preflight_parts.append(f"path={remote_path}")
        release_path_state = release_path_state_from_preflight_evidence(
            preflight_evidence
        )
        if isinstance(release_path_state, str) and release_path_state:
            preflight_parts.append(f"state={release_path_state}")
        remote_readiness = preflight_evidence.get("remote_readiness")
        if isinstance(remote_readiness, str) and remote_readiness:
            preflight_parts.append(f"readiness={remote_readiness}")
        publish_strategy = preflight_evidence.get("publish_strategy")
        if isinstance(publish_strategy, str) and publish_strategy:
            preflight_parts.append(f"strategy={publish_strategy}")
        remote_blocker = preflight_evidence.get("remote_blocker")
        if isinstance(remote_blocker, str) and remote_blocker:
            preflight_parts.append(f"blocker={remote_blocker}")
        remote_ref_count = preflight_evidence.get("remote_ref_count")
        if isinstance(remote_ref_count, int) and remote_ref_count > 0:
            preflight_parts.append(f"refs={remote_ref_count}")
        remote_ref_head_count = preflight_evidence.get("remote_ref_head_count")
        if isinstance(remote_ref_head_count, int) and remote_ref_head_count >= 0:
            preflight_parts.append(f"head_refs={remote_ref_head_count}")
        remote_ref_tag_count = preflight_evidence.get("remote_ref_tag_count")
        if isinstance(remote_ref_tag_count, int) and remote_ref_tag_count >= 0:
            preflight_parts.append(f"tag_refs={remote_ref_tag_count}")
        remote_ref_kinds = preflight_evidence.get("remote_ref_kinds")
        if isinstance(remote_ref_kinds, list):
            kind_values = unique_strings(remote_ref_kinds)
            if kind_values:
                preflight_parts.append(f"ref_kinds={','.join(kind_values)}")
        remote_ref_sample = preflight_evidence.get("remote_ref_sample")
        if isinstance(remote_ref_sample, list):
            sample_values = unique_strings(remote_ref_sample)
            if sample_values:
                preflight_parts.append(f"ref_sample={','.join(sample_values)}")
        next_action_count = preflight_evidence.get("next_action_count")
        if isinstance(next_action_count, int) and next_action_count > 0:
            preflight_parts.append(f"next_actions={next_action_count}")
        next_command_count = preflight_evidence.get("next_command_count")
        if isinstance(next_command_count, int) and next_command_count > 0:
            preflight_parts.append(f"next_commands={next_command_count}")
        for label, key in (
            ("tracked_generated", "tracked_generated_artifact_count"),
            ("tracked_local_only", "generated_local_only_tracked_count"),
            ("tracked_local_by_default", "generated_local_by_default_tracked_count"),
        ):
            value = preflight_evidence.get(key)
            if isinstance(value, int) and value > 0:
                preflight_parts.append(f"{label}={value}")
        publish_checklist_count = preflight_evidence.get("publish_checklist_count")
        if isinstance(publish_checklist_count, int) and publish_checklist_count > 0:
            preflight_parts.append(f"checklist={publish_checklist_count}")
        mode_bits = []
        for label, key in (
            ("skip_remote", "skip_remote"),
            ("allow_existing_refs", "allow_existing_refs"),
            ("allow_dirty", "allow_dirty"),
        ):
            value = preflight_evidence.get(key)
            if isinstance(value, bool):
                mode_bits.append(f"{label}={'yes' if value else 'no'}")
        if mode_bits:
            preflight_parts.append(f"mode={','.join(mode_bits)}")
        lines.append(f"- preflight: {'; '.join(preflight_parts)}")
    pytest_evidence = evidence.get("pytest")
    if (
        isinstance(pytest_evidence, Mapping)
        and pytest_evidence.get("passed") is not None
    ):
        pytest_parts = [f"{pytest_evidence['passed']} passed"]
        if pytest_evidence.get("skipped") is not None:
            pytest_parts.append(f"{pytest_evidence['skipped']} skipped")
        lines.append(f"- pytest: {'; '.join(pytest_parts)}")
    deep_evidence = evidence.get("deep")
    if isinstance(deep_evidence, Mapping):
        parts = [str(deep_evidence.get("status") or "unknown")]
        scan_quality = deep_evidence.get("scan_quality_status")
        if scan_quality is not None:
            parts.append(f"scan_quality={scan_quality}")
        warning_count = deep_evidence.get("scan_quality_warning_count")
        if warning_count is not None:
            parts.append(f"warnings={warning_count}")
        warning_types = deep_evidence.get("scan_quality_warning_types")
        if isinstance(warning_types, list):
            warning_type_names = [
                warning_type
                for warning_type in warning_types
                if isinstance(warning_type, str)
            ]
            if warning_type_names:
                parts.append(f"warning_types={','.join(warning_type_names)}")
        warning_paths = deep_evidence.get("scan_quality_warning_paths")
        if isinstance(warning_paths, list):
            warning_path_names = [
                warning_path
                for warning_path in warning_paths
                if isinstance(warning_path, str)
            ]
            if warning_path_names:
                parts.append(f"warning_paths={','.join(warning_path_names)}")
        warning_check_ids = deep_evidence.get("scan_quality_check_ids")
        if isinstance(warning_check_ids, list):
            warning_check_names = [
                check_id for check_id in warning_check_ids if isinstance(check_id, str)
            ]
            if warning_check_names:
                parts.append(f"warning_checks={','.join(warning_check_names)}")
        lines.append(f"- deep: {'; '.join(parts)}")
    benchmark_evidence = evidence.get("benchmark")
    if isinstance(benchmark_evidence, Mapping):
        snapshot = benchmark_evidence.get("snapshot")
        if snapshot:
            lines.append(f"- benchmark: {snapshot}")
    artifact_smoke_evidence = evidence.get("artifact_smoke")
    if isinstance(artifact_smoke_evidence, Mapping):
        parts = [str(artifact_smoke_evidence.get("summary") or "unknown")]
        check_count = artifact_smoke_evidence.get("check_count")
        if check_count is not None:
            parts.append(f"checks={check_count}")
        lines.append(f"- artifact smoke: {'; '.join(parts)}")
    bundle_manifest_evidence = evidence.get("bundle_manifest")
    if isinstance(bundle_manifest_evidence, Mapping):
        parts = [str(bundle_manifest_evidence.get("summary") or "unknown")]
        check_count = bundle_manifest_evidence.get("check_count")
        if check_count is not None:
            parts.append(f"checks={check_count}")
        bundle_path = bundle_manifest_evidence.get("bundle_path")
        if isinstance(bundle_path, str) and bundle_path:
            parts.append(f"bundle={bundle_path}")
        lines.append(f"- bundle manifest: {'; '.join(parts)}")
    build_evidence = evidence.get("build")
    if isinstance(build_evidence, Mapping):
        summary = build_evidence.get("summary")
        if summary:
            lines.append(f"- build: {summary}")
    gate_failures = evidence.get("gate_failures")
    if isinstance(gate_failures, Mapping):
        failure_parts: list[str] = []
        for check_name, failure in gate_failures.items():
            if not isinstance(check_name, str) or not check_name:
                continue
            if not isinstance(failure, Mapping):
                continue
            kind = failure.get("kind")
            if isinstance(kind, str) and kind:
                failure_parts.append(f"{check_name}={kind}")
        if failure_parts:
            lines.append(f"- gate failures: {'; '.join(failure_parts)}")
    cli_help_evidence = evidence.get("cli_help")
    if isinstance(cli_help_evidence, Mapping):
        parts = []
        check_count = cli_help_evidence.get("check_count")
        if check_count is not None:
            parts.append(f"surfaces={check_count}")
        failed_count = cli_help_evidence.get("failed_count")
        if failed_count not in (None, 0):
            parts.append(f"failed={failed_count}")
        if parts:
            lines.append(f"- cli help: {'; '.join(parts)}")
    worktree_evidence = evidence.get("worktree_commit_plan")
    if isinstance(worktree_evidence, Mapping):
        worktree_parts = [str(worktree_evidence.get("status") or "unknown")]
        batch_count = worktree_evidence.get("batch_count")
        if batch_count is not None:
            worktree_parts.append(f"batches={batch_count}")
        changed_batch_count = worktree_evidence.get("changed_batch_count")
        if changed_batch_count is not None:
            worktree_parts.append(f"changed_batches={changed_batch_count}")
        changed_path_count = worktree_evidence.get("changed_path_count")
        if changed_path_count is not None:
            worktree_parts.append(f"changed_paths={changed_path_count}")
        generated_artifact_count = worktree_evidence.get("generated_artifact_count")
        if generated_artifact_count is not None:
            worktree_parts.append(f"generated_artifacts={generated_artifact_count}")
        generated_file_count = worktree_evidence.get("generated_artifact_file_count")
        generated_dir_count = worktree_evidence.get("generated_artifact_dir_count")
        if generated_file_count is not None:
            worktree_parts.append(f"generated_files={generated_file_count}")
        if generated_dir_count is not None:
            worktree_parts.append(f"generated_dirs={generated_dir_count}")
        generated_local_only_count = worktree_evidence.get("generated_local_only_count")
        generated_local_by_default_count = worktree_evidence.get(
            "generated_local_by_default_count"
        )
        if generated_local_only_count is not None:
            worktree_parts.append(f"generated_local_only={generated_local_only_count}")
        if generated_local_by_default_count is not None:
            worktree_parts.append(
                f"generated_local_by_default={generated_local_by_default_count}"
            )
        report_path_count = worktree_evidence.get("report_path_count")
        if report_path_count is not None:
            worktree_parts.append(f"reports={report_path_count}")
        cross_cutting_count = worktree_evidence.get("cross_cutting_count")
        if cross_cutting_count is not None:
            worktree_parts.append(f"cross_cutting={cross_cutting_count}")
        cross_cutting_group_count = worktree_evidence.get("cross_cutting_group_count")
        if cross_cutting_group_count is not None:
            worktree_parts.append(f"patch_add_groups={cross_cutting_group_count}")
        shared_patch_add_count = worktree_evidence.get("shared_patch_add_count")
        if shared_patch_add_count is not None:
            worktree_parts.append(f"patch_add_candidates={shared_patch_add_count}")
        unassigned_source_path_count = worktree_evidence.get(
            "unassigned_source_path_count"
        )
        if unassigned_source_path_count is not None:
            worktree_parts.append(f"unassigned={unassigned_source_path_count}")
        multi_batch_path_count = worktree_evidence.get("multi_batch_path_count")
        if multi_batch_path_count is not None:
            worktree_parts.append(f"multi_batch={multi_batch_path_count}")
        unchanged_batch_count = worktree_evidence.get("unchanged_batch_count")
        if unchanged_batch_count is not None:
            worktree_parts.append(f"unchanged_batches={unchanged_batch_count}")
        branch = human_repository_branch(worktree_evidence.get("branch"))
        if branch is not None:
            worktree_parts.append(f"branch={branch}")
        head = worktree_evidence.get("head")
        if isinstance(head, str) and head:
            worktree_parts.append(f"head={head}")
        output_path = worktree_evidence.get("output_path")
        if isinstance(output_path, str) and output_path:
            worktree_parts.append(f"output={output_path}")
        attention_reasons = worktree_evidence.get("attention_reasons")
        strict_mode = worktree_evidence.get("strict_mode")
        if isinstance(strict_mode, Mapping):
            strict_flags = [
                key
                for key in ("fail_on_generated", "fail_on_cross_cutting")
                if strict_mode.get(key) is True
            ]
            if strict_flags:
                worktree_parts.append(f"strict={','.join(strict_flags)}")
        if isinstance(attention_reasons, list):
            reasons = [
                reason for reason in attention_reasons if isinstance(reason, str)
            ]
            if reasons:
                worktree_parts.append(f"attention={','.join(reasons)}")
        lines.append(f"- worktree commit plan: {'; '.join(worktree_parts)}")
    return lines
