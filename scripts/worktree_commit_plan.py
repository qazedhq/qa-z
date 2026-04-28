"""Summarize the dirty worktree against the alpha commit split plan."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
from pathlib import Path
from typing import Sequence

sys.dont_write_bytecode = True

from qa_z.subprocess_env import build_tool_subprocess_env  # noqa: E402


def _load_worktree_commit_plan_support_module():
    module_path = Path(__file__).with_name("worktree_commit_plan_support.py")
    cached = sys.modules.get("worktree_commit_plan_support")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == module_path.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "worktree_commit_plan_support", module_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Unable to load worktree commit plan support module: {module_path}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_WORKTREE_COMMIT_PLAN_SUPPORT = _load_worktree_commit_plan_support_module()
Runner = _WORKTREE_COMMIT_PLAN_SUPPORT.Runner
BatchRule = _WORKTREE_COMMIT_PLAN_SUPPORT.BatchRule
BATCH_RULES = _WORKTREE_COMMIT_PLAN_SUPPORT.BATCH_RULES
GENERATED_PATTERNS = _WORKTREE_COMMIT_PLAN_SUPPORT.GENERATED_PATTERNS
FROZEN_FIXTURE_EXCEPTIONS = _WORKTREE_COMMIT_PLAN_SUPPORT.FROZEN_FIXTURE_EXCEPTIONS
CROSS_CUTTING_PATTERNS = _WORKTREE_COMMIT_PLAN_SUPPORT.CROSS_CUTTING_PATTERNS
REPORT_PATTERNS = _WORKTREE_COMMIT_PLAN_SUPPORT.REPORT_PATTERNS
OWNER_OVERRIDES = _WORKTREE_COMMIT_PLAN_SUPPORT.OWNER_OVERRIDES
SOURCE_PATTERNS = _WORKTREE_COMMIT_PLAN_SUPPORT.SOURCE_PATTERNS
utc_timestamp = _WORKTREE_COMMIT_PLAN_SUPPORT.utc_timestamp
normalize_path = _WORKTREE_COMMIT_PLAN_SUPPORT.normalize_path
unquote_status_path = _WORKTREE_COMMIT_PLAN_SUPPORT.unquote_status_path
matches_any = _WORKTREE_COMMIT_PLAN_SUPPORT.matches_any
parse_status_line = _WORKTREE_COMMIT_PLAN_SUPPORT.parse_status_line
status_paths = _WORKTREE_COMMIT_PLAN_SUPPORT.status_paths
is_generated_artifact = _WORKTREE_COMMIT_PLAN_SUPPORT.is_generated_artifact
is_source_like = _WORKTREE_COMMIT_PLAN_SUPPORT.is_source_like
owner_override_for_path = _WORKTREE_COMMIT_PLAN_SUPPORT.owner_override_for_path
build_staging_plan = _WORKTREE_COMMIT_PLAN_SUPPORT.build_staging_plan
render_command_part = _WORKTREE_COMMIT_PLAN_SUPPORT.render_command_part
render_command = _WORKTREE_COMMIT_PLAN_SUPPORT.render_command
next_actions = _WORKTREE_COMMIT_PLAN_SUPPORT.next_actions
analyze_paths = _WORKTREE_COMMIT_PLAN_SUPPORT.analyze_paths
analyze_status_lines = _WORKTREE_COMMIT_PLAN_SUPPORT.analyze_status_lines
filter_payload_for_batch = _WORKTREE_COMMIT_PLAN_SUPPORT.filter_payload_for_batch
compact_payload = _WORKTREE_COMMIT_PLAN_SUPPORT.compact_payload
render_human = _WORKTREE_COMMIT_PLAN_SUPPORT.render_human
unique_strings = _WORKTREE_COMMIT_PLAN_SUPPORT.unique_strings


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
    return completed.returncode, completed.stdout, completed.stderr


def git_status_lines(
    repo_root: Path,
    runner: Runner = subprocess_runner,
    *,
    include_ignored: bool = False,
) -> list[str]:
    return git_status_lines_with_options(
        repo_root,
        runner=runner,
        include_ignored=include_ignored,
    )


def git_status_lines_with_options(
    repo_root: Path,
    *,
    runner: Runner = subprocess_runner,
    include_ignored: bool = False,
) -> list[str]:
    command = ["git", "status", "--short", "--untracked-files=all"]
    if include_ignored:
        command.append("--ignored")
    exit_code, stdout, stderr = runner(
        tuple(command),
        repo_root,
    )
    if exit_code != 0:
        detail = stderr.strip() or stdout.strip() or "git status failed"
        raise RuntimeError(detail)
    return stdout.splitlines()


def repository_context(
    repo_root: Path,
    *,
    runner: Runner = subprocess_runner,
) -> dict[str, str]:
    branch_exit, branch_stdout, _branch_stderr = runner(
        ("git", "branch", "--show-current"),
        repo_root,
    )
    head_exit, head_stdout, _head_stderr = runner(
        ("git", "rev-parse", "HEAD"),
        repo_root,
    )
    return {
        "branch": branch_stdout.strip() if branch_exit == 0 else "",
        "head": head_stdout.strip() if head_exit == 0 else "",
    }


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize dirty worktree paths against the QA-Z alpha commit plan."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON output.")
    parser.add_argument(
        "--batch",
        default=None,
        help="Limit output to one batch id, for example benchmark_coverage.",
    )
    parser.add_argument(
        "--include-ignored",
        action="store_true",
        help="Include ignored generated artifacts from git status --ignored.",
    )
    parser.add_argument(
        "--fail-on-generated",
        action="store_true",
        help="Return attention_required when generated artifacts are present.",
    )
    parser.add_argument(
        "--fail-on-cross-cutting",
        action="store_true",
        help="Return attention_required when cross-cutting paths require patch-add.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional path where the JSON evidence payload should be written.",
    )
    parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Write/print compact JSON evidence without per-file batch details.",
    )
    return parser.parse_args(argv)


def write_json_output(payload: dict[str, object], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        payload = analyze_status_lines(
            git_status_lines(Path.cwd(), include_ignored=args.include_ignored),
            fail_on_generated=args.fail_on_generated,
            fail_on_cross_cutting=args.fail_on_cross_cutting,
        )
        payload["repository"] = repository_context(Path.cwd())
        if args.batch is not None:
            payload = filter_payload_for_batch(payload, args.batch)
    except RuntimeError as exc:
        print(f"worktree commit plan failed: {exc}", file=sys.stderr)
        return 2
    except ValueError as exc:
        print(f"worktree commit plan failed: {exc}", file=sys.stderr)
        return 2
    output_payload = compact_payload(payload) if args.summary_only else payload
    if args.output is not None:
        output_payload["output_path"] = str(args.output)
        try:
            write_json_output(output_payload, args.output)
        except OSError as exc:
            print(
                f"worktree commit plan failed: could not write output: {exc}",
                file=sys.stderr,
            )
            return 2
    if args.json:
        print(json.dumps(output_payload, indent=2))
    else:
        print(render_human(payload))
    return 1 if payload["status"] == "attention_required" else 0


if __name__ == "__main__":
    raise SystemExit(main())
