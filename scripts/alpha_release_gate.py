"""Run the deterministic local QA-Z alpha release gate."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable
from typing import NamedTuple
from typing import Sequence

from qa_z.subprocess_env import build_tool_subprocess_env


DEFAULT_REPOSITORY_FULL_NAME = "qazedhq/qa-z"
DEFAULT_REPOSITORY_URL = "https://github.com/qazedhq/qa-z.git"


class GateCommand(NamedTuple):
    name: str
    label: str
    command: tuple[str, ...]


class AlphaReleaseGateResult(NamedTuple):
    summary: str
    exit_code: int
    commands: Sequence[Sequence[str]]
    payload: dict[str, object]


Runner = Callable[[Sequence[str], Path], tuple[int, str, str]]


def subprocess_runner(command: Sequence[str], cwd: Path) -> tuple[int, str, str]:
    completed = subprocess.run(
        list(command),
        cwd=cwd,
        env=build_tool_subprocess_env(),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    return completed.returncode, completed.stdout or "", completed.stderr or ""


def configured_origin_url_for_gate(repo_root: Path) -> str | None:
    """Return the configured origin URL when the repository already has one."""
    exit_code, stdout, _stderr = subprocess_runner(
        ("git", "remote", "get-url", "origin"), repo_root
    )
    if exit_code != 0:
        return None
    origin_url = stdout.strip()
    return origin_url or None


def python_command(*args: str) -> tuple[str, ...]:
    return (sys.executable, *args)


def utc_timestamp() -> str:
    """Return a compact UTC timestamp for generated release evidence."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def cli_help_commands() -> list[GateCommand]:
    help_surfaces = [
        (),
        ("init",),
        ("plan",),
        ("fast",),
        ("deep",),
        ("review",),
        ("repair-prompt",),
        ("repair-session",),
        ("github-summary",),
        ("verify",),
        ("benchmark",),
        ("self-inspect",),
        ("select-next",),
        ("backlog",),
        ("autonomy",),
        ("executor-bridge",),
        ("executor-result",),
    ]
    commands: list[GateCommand] = []
    for surface in help_surfaces:
        name = "cli_help_root" if not surface else f"cli_help_{surface[0]}"
        label = " ".join(("python", "-m", "qa_z", *surface, "--help"))
        commands.append(
            GateCommand(
                name.replace("-", "_"),
                label,
                python_command("-m", "qa_z", *surface, "--help"),
            )
        )
    return commands


def default_gate_commands(
    *,
    with_deps: bool = False,
    allow_dirty: bool = False,
    include_remote: bool = False,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    expected_origin_url: str | None = None,
    local_expected_origin_url: str | None = None,
    allow_existing_refs: bool = False,
    preflight_output: Path | None = None,
    worktree_plan_output: Path | None = None,
    strict_worktree_plan: bool = False,
) -> list[GateCommand]:
    remote_options_requested = (
        repository_url != DEFAULT_REPOSITORY_URL
        or expected_repository != DEFAULT_REPOSITORY_FULL_NAME
        or expected_origin_url is not None
        or allow_existing_refs
    )
    effective_include_remote = include_remote or remote_options_requested
    effective_expected_origin_url = (
        repository_url
        if effective_include_remote and expected_origin_url is None
        else expected_origin_url
    )
    preflight_args = ["scripts/alpha_release_preflight.py"]
    preflight_label_parts = ["python", "scripts/alpha_release_preflight.py"]
    if effective_include_remote:
        preflight_args.extend(["--repository-url", repository_url])
        preflight_label_parts.extend(["--repository-url", repository_url])
        if expected_repository != DEFAULT_REPOSITORY_FULL_NAME:
            preflight_args.extend(["--expected-repository", expected_repository])
            preflight_label_parts.extend(["--expected-repository", expected_repository])
        if effective_expected_origin_url is not None:
            preflight_args.extend(
                ["--expected-origin-url", effective_expected_origin_url]
            )
            preflight_label_parts.extend(
                ["--expected-origin-url", effective_expected_origin_url]
            )
        if allow_existing_refs:
            preflight_args.append("--allow-existing-refs")
            preflight_label_parts.append("--allow-existing-refs")
    else:
        preflight_args.append("--skip-remote")
        preflight_label_parts.append("--skip-remote")
        if local_expected_origin_url is not None:
            preflight_args.extend(["--expected-origin-url", local_expected_origin_url])
            preflight_label_parts.extend(
                ["--expected-origin-url", local_expected_origin_url]
            )
    if allow_dirty:
        preflight_args.append("--allow-dirty")
        preflight_label_parts.append("--allow-dirty")
    if preflight_output is not None:
        preflight_args.extend(["--output", str(preflight_output)])
        preflight_label_parts.extend(["--output", str(preflight_output)])
    preflight_args.append("--json")
    preflight_label_parts.append("--json")

    worktree_plan_args = [
        "scripts/worktree_commit_plan.py",
        "--include-ignored",
    ]
    worktree_plan_label_parts = [
        "python",
        "scripts/worktree_commit_plan.py",
        "--include-ignored",
    ]
    if strict_worktree_plan:
        worktree_plan_args.append("--fail-on-generated")
        worktree_plan_label_parts.append("--fail-on-generated")
        worktree_plan_args.append("--fail-on-cross-cutting")
        worktree_plan_label_parts.append("--fail-on-cross-cutting")
    if worktree_plan_output is not None:
        worktree_plan_args.extend(["--output", str(worktree_plan_output)])
        worktree_plan_label_parts.extend(["--output", str(worktree_plan_output)])
    worktree_plan_args.append("--json")
    worktree_plan_label_parts.append("--json")

    commands = [
        GateCommand(
            "local_preflight",
            " ".join(preflight_label_parts),
            python_command(*preflight_args),
        ),
        GateCommand(
            "worktree_commit_plan",
            " ".join(worktree_plan_label_parts),
            python_command(*worktree_plan_args),
        ),
        GateCommand(
            "ruff_format",
            "python -m ruff format --check .",
            python_command("-m", "ruff", "format", "--check", "."),
        ),
        GateCommand(
            "ruff_check",
            "python -m ruff check .",
            python_command("-m", "ruff", "check", "."),
        ),
        GateCommand(
            "mypy",
            "python -m mypy src tests",
            python_command("-m", "mypy", "src", "tests"),
        ),
        GateCommand(
            "pytest",
            "python -m pytest",
            python_command("-m", "pytest"),
        ),
        *cli_help_commands(),
        GateCommand(
            "qa_z_fast",
            "python -m qa_z fast --selection smart --json",
            python_command("-m", "qa_z", "fast", "--selection", "smart", "--json"),
        ),
        GateCommand(
            "qa_z_deep",
            "python -m qa_z deep --selection smart --json",
            python_command("-m", "qa_z", "deep", "--selection", "smart", "--json"),
        ),
        GateCommand(
            "qa_z_benchmark",
            "python -m qa_z benchmark --json",
            python_command("-m", "qa_z", "benchmark", "--json"),
        ),
        GateCommand(
            "build",
            "python -m build --sdist --wheel",
            python_command("-m", "build", "--sdist", "--wheel"),
        ),
        GateCommand(
            "artifact_smoke",
            "python scripts/alpha_release_artifact_smoke.py --json",
            python_command("scripts/alpha_release_artifact_smoke.py", "--json"),
        ),
    ]

    if with_deps:
        commands.append(
            GateCommand(
                "artifact_smoke_with_deps",
                "python scripts/alpha_release_artifact_smoke.py --with-deps --json",
                python_command(
                    "scripts/alpha_release_artifact_smoke.py",
                    "--with-deps",
                    "--json",
                ),
            )
        )

    commands.append(
        GateCommand(
            "bundle_manifest",
            "python scripts/alpha_release_bundle_manifest.py --json",
            python_command("scripts/alpha_release_bundle_manifest.py", "--json"),
        )
    )
    return commands


def _load_alpha_release_gate_evidence_module():
    module_path = Path(__file__).with_name("alpha_release_gate_evidence.py")
    cached = sys.modules.get("alpha_release_gate_evidence")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == module_path.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "alpha_release_gate_evidence", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load alpha release gate evidence module: {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_ALPHA_RELEASE_GATE_EVIDENCE = _load_alpha_release_gate_evidence_module()
output_tail = _ALPHA_RELEASE_GATE_EVIDENCE.output_tail
human_repository_branch = _ALPHA_RELEASE_GATE_EVIDENCE.human_repository_branch
preflight_next_actions = _ALPHA_RELEASE_GATE_EVIDENCE.preflight_next_actions
preflight_next_commands = _ALPHA_RELEASE_GATE_EVIDENCE.preflight_next_commands
string_list = _ALPHA_RELEASE_GATE_EVIDENCE.string_list
unique_strings = _ALPHA_RELEASE_GATE_EVIDENCE.unique_strings
preflight_has_next_actions = _ALPHA_RELEASE_GATE_EVIDENCE.preflight_has_next_actions
preflight_failed_checks = _ALPHA_RELEASE_GATE_EVIDENCE.preflight_failed_checks
synthesized_preflight_next_actions = (
    _ALPHA_RELEASE_GATE_EVIDENCE.synthesized_preflight_next_actions
)
preflight_payload = _ALPHA_RELEASE_GATE_EVIDENCE.preflight_payload
payload_from_stdout_or_file = _ALPHA_RELEASE_GATE_EVIDENCE.payload_from_stdout_or_file
release_path_state_from_preflight_evidence = (
    _ALPHA_RELEASE_GATE_EVIDENCE.release_path_state_from_preflight_evidence
)
repository_http_status_from_preflight_evidence = (
    _ALPHA_RELEASE_GATE_EVIDENCE.repository_http_status_from_preflight_evidence
)
repository_probe_state_from_preflight_evidence = (
    _ALPHA_RELEASE_GATE_EVIDENCE.repository_probe_state_from_preflight_evidence
)
repository_probe_basis_from_preflight_evidence = (
    _ALPHA_RELEASE_GATE_EVIDENCE.repository_probe_basis_from_preflight_evidence
)
parse_json_object = _ALPHA_RELEASE_GATE_EVIDENCE.parse_json_object
first_failed_nested_check = _ALPHA_RELEASE_GATE_EVIDENCE.first_failed_nested_check
output_contains_offline_build_dependency_failure = (
    _ALPHA_RELEASE_GATE_EVIDENCE.output_contains_offline_build_dependency_failure
)
classify_gate_failure = _ALPHA_RELEASE_GATE_EVIDENCE.classify_gate_failure
classify_gate_failures = _ALPHA_RELEASE_GATE_EVIDENCE.classify_gate_failures
next_actions_for_gate_failures = (
    _ALPHA_RELEASE_GATE_EVIDENCE.next_actions_for_gate_failures
)
next_commands_for_gate_failures = (
    _ALPHA_RELEASE_GATE_EVIDENCE.next_commands_for_gate_failures
)
release_evidence_for_command = _ALPHA_RELEASE_GATE_EVIDENCE.release_evidence_for_command
benchmark_snapshot_from_counts = (
    _ALPHA_RELEASE_GATE_EVIDENCE.benchmark_snapshot_from_counts
)
release_evidence_consistency_errors = (
    _ALPHA_RELEASE_GATE_EVIDENCE.release_evidence_consistency_errors
)
release_evidence_consistency_next_actions = (
    _ALPHA_RELEASE_GATE_EVIDENCE.release_evidence_consistency_next_actions
)
render_alpha_release_gate_human = (
    _ALPHA_RELEASE_GATE_EVIDENCE.render_alpha_release_gate_human
)
render_worktree_plan_attention_lines = (
    _ALPHA_RELEASE_GATE_EVIDENCE.render_worktree_plan_attention_lines
)
render_nested_artifact_lines = _ALPHA_RELEASE_GATE_EVIDENCE.render_nested_artifact_lines
render_release_evidence_lines = (
    _ALPHA_RELEASE_GATE_EVIDENCE.render_release_evidence_lines
)


def run_alpha_release_gate(
    repo_root: Path,
    *,
    with_deps: bool = False,
    allow_dirty: bool = False,
    include_remote: bool = False,
    repository_url: str = DEFAULT_REPOSITORY_URL,
    expected_repository: str = DEFAULT_REPOSITORY_FULL_NAME,
    expected_origin_url: str | None = None,
    allow_existing_refs: bool = False,
    preflight_output: Path | None = None,
    worktree_plan_output: Path | None = None,
    strict_worktree_plan: bool = False,
    runner: Runner = subprocess_runner,
) -> AlphaReleaseGateResult:
    detected_origin_url = configured_origin_url_for_gate(repo_root)
    remote_options_requested = (
        repository_url != DEFAULT_REPOSITORY_URL
        or expected_repository != DEFAULT_REPOSITORY_FULL_NAME
        or expected_origin_url is not None
        or allow_existing_refs
    )
    effective_include_remote = include_remote or remote_options_requested
    effective_expected_origin_url = (
        repository_url
        if effective_include_remote and expected_origin_url is None
        else expected_origin_url
    )
    local_expected_origin_url = (
        repository_url
        if effective_expected_origin_url is None
        and not effective_include_remote
        and detected_origin_url is not None
        else None
    )
    commands = default_gate_commands(
        with_deps=with_deps,
        allow_dirty=allow_dirty,
        include_remote=effective_include_remote,
        repository_url=repository_url,
        expected_repository=expected_repository,
        expected_origin_url=effective_expected_origin_url,
        local_expected_origin_url=local_expected_origin_url,
        allow_existing_refs=allow_existing_refs,
        preflight_output=preflight_output,
        worktree_plan_output=worktree_plan_output,
        strict_worktree_plan=strict_worktree_plan,
    )
    checks: list[dict[str, object]] = []
    executed_commands: list[Sequence[str]] = []
    next_actions: list[str] = []
    next_commands: list[str] = []
    has_next_actions = False
    has_next_commands = False
    preflight_failures: list[str] = []
    worktree_plan_attention_reasons: list[str] = []
    evidence: dict[str, object] = {}

    for gate_command in commands:
        executed_commands.append(gate_command.command)
        exit_code, stdout, stderr = runner(gate_command.command, repo_root)
        command_output_path = (
            worktree_plan_output
            if gate_command.name == "worktree_commit_plan"
            else preflight_output
            if gate_command.name == "local_preflight"
            else None
        )
        command_evidence = release_evidence_for_command(
            gate_command.name, stdout, command_output_path
        )
        if command_evidence:
            evidence[gate_command.name.removeprefix("qa_z_")] = command_evidence
        if gate_command.name == "local_preflight":
            nested_preflight_payload = preflight_payload(stdout, preflight_output)
            explicit_preflight_next_actions = preflight_has_next_actions(
                nested_preflight_payload
            )
            promoted_actions = preflight_next_actions(nested_preflight_payload)
            if explicit_preflight_next_actions:
                has_next_actions = True
            if promoted_actions:
                next_actions.extend(promoted_actions)
                has_next_actions = True
            promoted_commands = preflight_next_commands(nested_preflight_payload)
            if promoted_commands:
                next_commands.extend(promoted_commands)
                has_next_commands = True
            if exit_code != 0:
                preflight_failures.extend(
                    preflight_failed_checks(nested_preflight_payload)
                )
                if not explicit_preflight_next_actions:
                    synthesized_actions = synthesized_preflight_next_actions(
                        preflight_failures
                    )
                    next_actions.extend(synthesized_actions)
                    has_next_actions = bool(synthesized_actions) or has_next_actions
        if gate_command.name == "worktree_commit_plan" and exit_code != 0:
            worktree_plan_payload = payload_from_stdout_or_file(
                stdout, worktree_plan_output
            )
            if worktree_plan_payload is not None:
                worktree_plan_attention_reasons.extend(
                    string_list(worktree_plan_payload, "attention_reasons")
                )
                worktree_plan_actions = string_list(
                    worktree_plan_payload, "next_actions"
                )
                if worktree_plan_actions:
                    next_actions.extend(worktree_plan_actions)
                    has_next_actions = True
        checks.append(
            {
                "name": gate_command.name,
                "label": gate_command.label,
                "status": "passed" if exit_code == 0 else "failed",
                "exit_code": exit_code,
                "stdout_tail": output_tail(stdout),
                "stderr_tail": output_tail(stderr),
            }
        )

    evidence_consistency_errors = release_evidence_consistency_errors(evidence)
    cli_help_checks = [
        check for check in checks if str(check.get("name", "")).startswith("cli_help")
    ]
    if cli_help_checks:
        evidence["cli_help"] = {
            "check_count": len(cli_help_checks),
            "failed_count": sum(
                1 for check in cli_help_checks if check.get("status") == "failed"
            ),
        }
    if evidence_consistency_errors:
        next_actions.extend(
            release_evidence_consistency_next_actions(evidence_consistency_errors)
        )
        has_next_actions = True
        checks.append(
            {
                "name": "release_evidence_consistency",
                "label": "release evidence consistency",
                "status": "failed",
                "exit_code": 1,
                "stdout_tail": output_tail("\n".join(evidence_consistency_errors)),
                "stderr_tail": "",
            }
        )

    failed_checks = [
        str(check["name"]) for check in checks if check["status"] == "failed"
    ]
    gate_failures, environment_failure_count, product_failure_count = (
        classify_gate_failures(checks)
    )
    for check in checks:
        if check.get("status") == "passed":
            continue
        name = str(check.get("name") or "")
        classified_failure = gate_failures.get(name)
        if classified_failure is None:
            check["failure_scope"] = "product"
            continue
        check["failure_scope"] = "environment"
        kind = classified_failure.get("kind")
        if kind:
            check["failure_kind"] = kind
        summary = classified_failure.get("summary")
        if summary:
            check["failure_summary"] = summary
    if gate_failures:
        evidence["gate_failures"] = gate_failures
        for action in next_actions_for_gate_failures(gate_failures):
            if action not in next_actions:
                next_actions.append(action)
                has_next_actions = True
        for command in next_commands_for_gate_failures(gate_failures):
            if command not in next_commands:
                next_commands.append(command)
                has_next_commands = True
    passed_count = sum(1 for check in checks if check["status"] == "passed")
    failed_count = len(failed_checks)
    check_count = len(checks)
    exit_code = 1 if failed_checks else 0
    summary = "alpha release gate failed" if exit_code else "alpha release gate passed"
    payload: dict[str, object] = {
        "summary": summary,
        "exit_code": exit_code,
        "generated_at": utc_timestamp(),
        "check_count": check_count,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "failed_checks": failed_checks,
        "with_deps": with_deps,
        "allow_dirty": allow_dirty,
        "include_remote": effective_include_remote,
        "repository_url": repository_url if effective_include_remote else None,
        "expected_repository": (
            expected_repository if effective_include_remote else None
        ),
        "expected_origin_url": effective_expected_origin_url
        if effective_include_remote
        else local_expected_origin_url
        if local_expected_origin_url is not None
        else None,
        "allow_existing_refs": allow_existing_refs
        if effective_include_remote
        else False,
        "strict_worktree_plan": strict_worktree_plan,
        "preflight_output": str(preflight_output)
        if preflight_output is not None
        else None,
        "worktree_plan_output": str(worktree_plan_output)
        if worktree_plan_output is not None
        else None,
        "checks": checks,
    }
    if evidence:
        payload["evidence"] = evidence
    if evidence_consistency_errors:
        payload["evidence_consistency_errors"] = evidence_consistency_errors
    if preflight_failures:
        payload["preflight_failed_checks"] = preflight_failures
    if worktree_plan_attention_reasons:
        payload["worktree_plan_attention_reasons"] = worktree_plan_attention_reasons
    if failed_checks or environment_failure_count > 0:
        payload["environment_failure_count"] = environment_failure_count
    if failed_checks or product_failure_count > 0:
        payload["product_failure_count"] = product_failure_count
    if has_next_actions:
        payload["next_actions"] = next_actions
    if has_next_commands:
        payload["next_commands"] = unique_strings(next_commands)
    return AlphaReleaseGateResult(
        summary=summary,
        exit_code=exit_code,
        commands=executed_commands,
        payload=payload,
    )


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the deterministic local QA-Z alpha release gate."
    )
    parser.add_argument(
        "--with-deps",
        action="store_true",
        help=(
            "Also run the stronger artifact smoke with dependency resolution. "
            "This may contact the configured Python package index."
        ),
    )
    parser.add_argument(
        "--allow-dirty",
        action="store_true",
        help=(
            "Pass --allow-dirty to local preflight. Use only while developing the "
            "release gate itself; omit for publish evidence."
        ),
    )
    parser.add_argument(
        "--include-remote",
        action="store_true",
        help=(
            "Include GitHub metadata and git ls-remote preflight checks. "
            "Use after the public repository exists."
        ),
    )
    parser.add_argument(
        "--repository-url",
        default=DEFAULT_REPOSITORY_URL,
        help=f"Git repository URL for --include-remote. Defaults to {DEFAULT_REPOSITORY_URL}.",
    )
    parser.add_argument(
        "--expected-repository",
        default=DEFAULT_REPOSITORY_FULL_NAME,
        help=(
            "Expected GitHub owner/repository full name for --include-remote. "
            f"Defaults to {DEFAULT_REPOSITORY_FULL_NAME}."
        ),
    )
    parser.add_argument(
        "--expected-origin-url",
        default=None,
        help=(
            "Require local origin to match this URL during --include-remote preflight."
        ),
    )
    parser.add_argument(
        "--allow-existing-refs",
        action="store_true",
        help=(
            "With --include-remote, allow a reachable repository that already "
            "has refs while still rejecting an existing release tag."
        ),
    )
    parser.add_argument(
        "--strict-worktree-plan",
        action="store_true",
        help=(
            "Run the worktree commit-plan helper with --fail-on-generated. "
            "Use for final source staging audits."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable gate evidence as JSON.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path where the JSON evidence payload should be written.",
    )
    parser.add_argument(
        "--preflight-output",
        type=Path,
        default=None,
        help=(
            "Optional path where the nested preflight JSON evidence should be "
            "written. Defaults to <output>.preflight.json when --output is set."
        ),
    )
    parser.add_argument(
        "--worktree-plan-output",
        type=Path,
        default=None,
        help=(
            "Optional path where the nested worktree commit-plan JSON evidence "
            "should be written. Defaults to <output>.worktree-plan.json when "
            "--output is set."
        ),
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    preflight_output = args.preflight_output
    if preflight_output is None and args.output is not None:
        preflight_output = args.output.with_suffix(".preflight.json")
    worktree_plan_output = args.worktree_plan_output
    if worktree_plan_output is None and args.output is not None:
        worktree_plan_output = args.output.with_suffix(".worktree-plan.json")
    result = run_alpha_release_gate(
        Path.cwd(),
        with_deps=args.with_deps,
        allow_dirty=args.allow_dirty,
        include_remote=args.include_remote,
        repository_url=args.repository_url,
        expected_repository=args.expected_repository,
        expected_origin_url=args.expected_origin_url,
        allow_existing_refs=args.allow_existing_refs,
        preflight_output=preflight_output,
        worktree_plan_output=worktree_plan_output,
        strict_worktree_plan=args.strict_worktree_plan,
    )
    payload_json = json.dumps(result.payload, indent=2)

    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{payload_json}\n", encoding="utf-8")

    if args.json:
        print(payload_json)
    else:
        print(render_alpha_release_gate_human(result.payload), end="")

    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
