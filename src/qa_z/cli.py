"""Command line interface for QA-Z."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from .adapters.claude import render_claude_handoff
from .autonomy import (
    load_autonomy_status,
    render_autonomy_status,
    render_autonomy_summary,
    run_autonomy,
)
from .benchmark import (
    DEFAULT_FIXTURES_DIR,
    DEFAULT_RESULTS_DIR,
    BenchmarkError,
    render_benchmark_report,
    run_benchmark,
)
from .adapters.codex import render_codex_handoff
from .artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    RunSource,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_run_source,
    write_latest_run_manifest,
)
from .config import (
    CONTRACTS_README,
    EXAMPLE_CONFIG,
    ConfigError,
    get_nested,
    load_config,
)
from .executor_bridge import (
    ExecutorBridgeError,
    create_executor_bridge,
    render_bridge_stdout,
)
from .planner.contracts import plan_contract
from .self_improvement import (
    compact_backlog_evidence_summary,
    load_backlog,
    open_backlog_items,
    run_self_inspection,
    select_next_tasks,
)
from .repair_handoff import (
    build_repair_handoff,
    repair_handoff_json,
    write_repair_handoff_artifact,
)
from .repair_session import (
    create_repair_session,
    load_repair_session,
    render_session_status,
    repair_session_exit_code,
    session_status_json,
    verify_repair_session,
)
from .reporters.deep_context import load_sibling_deep_summary
from .reporters.github_summary import github_summary_json, render_github_summary
from .reporters.repair_prompt import (
    build_repair_packet,
    repair_packet_json,
    write_repair_artifacts,
)
from .reporters.review_packet import (
    find_latest_contract,
    render_review_packet,
    render_run_review_packet,
    review_packet_json,
    run_review_packet_json,
    write_review_artifacts,
)
from .reporters.run_summary import write_run_summary_artifacts
from .reporters.sarif import write_sarif_artifact
from .runners.deep import run_deep
from .runners.fast import run_fast, summary_json
from .verification import (
    VerificationArtifactPaths,
    VerificationRun,
    comparison_json,
    compare_verification_runs,
    load_verification_run,
    verify_exit_code,
    write_verification_artifacts,
)


def write_text_if_missing(path: Path, content: str) -> bool:
    """Create a text file only when it does not exist yet."""
    if path.exists():
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return True


def format_relative_path(path: Path, root: Path) -> str:
    """Render a stable relative path for CLI output."""
    return path.relative_to(root).as_posix()


def handle_init(args: argparse.Namespace) -> int:
    """Bootstrap a repository with starter QA-Z files."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)

    config_path = root / "qa-z.yaml"
    contracts_readme = root / "qa" / "contracts" / "README.md"

    created = []
    skipped = []

    for path, content in (
        (config_path, EXAMPLE_CONFIG),
        (contracts_readme, CONTRACTS_README),
    ):
        if write_text_if_missing(path, content):
            created.append(path)
        else:
            skipped.append(path)

    print(f"Initialized QA-Z bootstrap in {root}")
    for path in created:
        print(f"created: {format_relative_path(path, root)}")
    for path in skipped:
        print(f"skipped: {format_relative_path(path, root)}")

    if not created:
        print("Nothing new was written because the starter files already exist.")

    return 0


def handle_plan(args: argparse.Namespace) -> int:
    """Generate a QA contract draft from local context files."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "plan")
    if config is None:
        return 2

    contract_path, created = plan_contract(
        root=root,
        config=config,
        title=args.title,
        slug=args.slug,
        issue_path=Path(args.issue).expanduser().resolve() if args.issue else None,
        spec_path=Path(args.spec).expanduser().resolve() if args.spec else None,
        diff_path=Path(args.diff).expanduser().resolve() if args.diff else None,
        overwrite=args.overwrite,
    )

    relative_contract_path = format_relative_path(contract_path, root)
    status = "created contract" if created else "kept existing contract"
    print(f"{status}: {relative_contract_path}")
    return 0


def handle_review(args: argparse.Namespace) -> int:
    """Render a review packet from a generated contract."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "review")
    if config is None:
        return 2

    try:
        if args.from_run:
            run_source = resolve_run_source(root, config, args.from_run)
            summary = load_run_summary(run_source.summary_path)
            deep_summary = load_sibling_deep_summary(run_source)
            contract_path = resolve_contract_source(
                root, config, summary=summary, explicit_contract=args.contract
            )
            contract = load_contract_context(contract_path, root)
            markdown = render_run_review_packet(
                summary=summary,
                run_source=run_source,
                contract=contract,
                root=root,
                deep_summary=deep_summary,
            )
            json_text = run_review_packet_json(
                summary=summary,
                run_source=run_source,
                contract=contract,
                root=root,
                deep_summary=deep_summary,
            )
            if args.output_dir:
                write_review_artifacts(
                    markdown, json_text, resolve_cli_path(root, args.output_dir)
                )
            if args.json:
                print(json_text, end="")
            else:
                print(markdown, end="")
            return 0

        if args.contract:
            contract_path = resolve_cli_path(root, args.contract)
        else:
            contract_path = find_latest_contract(root, config)
        markdown = render_review_packet(contract_path, root)
        json_text = review_packet_json(contract_path, root)
        if args.output_dir:
            write_review_artifacts(
                markdown, json_text, resolve_cli_path(root, args.output_dir)
            )
        if args.json:
            print(json_text, end="")
        else:
            print(markdown, end="")
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z review: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z review: source not found: {exc}")
        return 4


def handle_fast(args: argparse.Namespace) -> int:
    """Run deterministic fast checks."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "fast")
    if config is None:
        return 2

    contract_path = resolve_cli_path(root, args.contract) if args.contract else None
    output_dir = resolve_cli_path(root, args.output_dir) if args.output_dir else None

    try:
        run = run_fast(
            root=root,
            config=config,
            contract_path=contract_path,
            diff_path=resolve_cli_path(root, args.diff) if args.diff else None,
            output_dir=output_dir,
            strict_no_tests=args.strict_no_tests,
            selection_mode=resolve_fast_selection_mode(config, args.selection),
        )
    except (FileNotFoundError, ValueError) as exc:
        print(f"qa-z fast: configuration error: {exc}")
        return 2

    artifact_dir = Path(run.summary.artifact_dir or "")
    if not artifact_dir.is_absolute():
        artifact_dir = root / artifact_dir
    summary_path = write_run_summary_artifacts(run.summary, artifact_dir)
    run_dir = artifact_dir.parent
    write_latest_run_manifest(root, config, run_dir)

    if args.json:
        print(summary_json(run.summary), end="")
    else:
        print(
            render_fast_stdout(
                run.summary.status, run.summary.contract_path, summary_path, root
            )
        )

    return run.exit_code


def handle_deep(args: argparse.Namespace) -> int:
    """Create deep-runner artifacts."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "deep")
    if config is None:
        return 2

    try:
        run = run_deep(
            root=root,
            config=config,
            output_dir=resolve_cli_path(root, args.output_dir)
            if args.output_dir
            else None,
            from_run=args.from_run,
            diff_path=resolve_cli_path(root, args.diff) if args.diff else None,
            selection_mode=resolve_deep_selection_mode(config, args.selection),
        )
    except ArtifactLoadError as exc:
        print(f"qa-z deep: artifact error: {exc}")
        return 2
    except ArtifactSourceNotFound as exc:
        print(f"qa-z deep: source not found: {exc}")
        return 4
    except (FileNotFoundError, ValueError) as exc:
        print(f"qa-z deep: configuration error: {exc}")
        return 2

    summary_path = write_run_summary_artifacts(run.summary, run.resolution.deep_dir)
    write_sarif_artifact(run.summary, run.resolution.deep_dir / "results.sarif")
    if args.sarif_output:
        write_sarif_artifact(run.summary, resolve_cli_path(root, args.sarif_output))

    if args.json:
        print(summary_json(run.summary), end="")
    else:
        print(render_deep_stdout(run.summary.status, summary_path, root))

    return run.exit_code


def handle_repair_prompt(args: argparse.Namespace) -> int:
    """Render deterministic repair artifacts from a failed run."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "repair-prompt")
    if config is None:
        return 2

    try:
        run_source = resolve_run_source(root, config, args.from_run)
        summary = load_run_summary(run_source.summary_path)
        deep_summary = load_sibling_deep_summary(run_source)
        contract_path = resolve_contract_source(
            root, config, summary=summary, explicit_contract=args.contract
        )
        contract = load_contract_context(contract_path, root)
        packet = build_repair_packet(
            summary=summary,
            run_source=run_source,
            contract=contract,
            root=root,
            deep_summary=deep_summary,
        )
        handoff = build_repair_handoff(
            repair_packet=packet,
            summary=summary,
            run_source=run_source,
            root=root,
            deep_summary=deep_summary,
        )
        codex_markdown = render_codex_handoff(handoff)
        claude_markdown = render_claude_handoff(handoff)
        output_dir = (
            resolve_cli_path(root, args.output_dir)
            if args.output_dir
            else run_source.run_dir / "repair"
        )
        write_repair_artifacts(packet, output_dir)
        write_repair_handoff_artifact(handoff, output_dir)
        (output_dir / "codex.md").write_text(codex_markdown, encoding="utf-8")
        (output_dir / "claude.md").write_text(claude_markdown, encoding="utf-8")
        if args.handoff_json:
            print(repair_handoff_json(handoff), end="")
            return 0
        if args.json:
            print(repair_packet_json(packet), end="")
        elif args.adapter == "codex":
            print(codex_markdown, end="")
        elif args.adapter == "claude":
            print(claude_markdown, end="")
        else:
            print(packet.agent_prompt, end="")
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z repair-prompt: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-prompt: source not found: {exc}")
        return 4


def handle_repair_session_start(args: argparse.Namespace) -> int:
    """Create a repair session from baseline run evidence."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "repair-session start")
    if config is None:
        return 2

    try:
        result = create_repair_session(
            root=root,
            config=config,
            baseline_run=args.baseline_run,
            session_id=args.session_id,
        )
        if args.json:
            print(session_status_json(result.session), end="")
        else:
            print(render_session_status(result.session))
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z repair-session start: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-session start: source not found: {exc}")
        return 4


def handle_repair_session_status(args: argparse.Namespace) -> int:
    """Print repair-session status."""
    root = Path(args.path).expanduser().resolve()

    try:
        session = load_repair_session(root, args.session)
        if args.json:
            print(session_status_json(session), end="")
        else:
            print(render_session_status(session))
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z repair-session status: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-session status: source not found: {exc}")
        return 4


def handle_repair_session_verify(args: argparse.Namespace) -> int:
    """Verify a repair session candidate run."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "repair-session verify")
    if config is None:
        return 2

    try:
        result = verify_repair_session(
            root=root,
            config=config,
            session_ref=args.session,
            candidate_run=args.candidate_run,
        )
        summary_json_text = result.summary_path.read_text(encoding="utf-8")
        if args.json:
            print(summary_json_text, end="")
        else:
            print(result.outcome_path.read_text(encoding="utf-8"), end="")
        return repair_session_exit_code(str(result.comparison.verdict))
    except ArtifactLoadError as exc:
        print(f"qa-z repair-session verify: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-session verify: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z repair-session verify: configuration error: {exc}")
        return 2


def handle_github_summary(args: argparse.Namespace) -> int:
    """Render compact Markdown or JSON for GitHub Actions summaries."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "github-summary")
    if config is None:
        return 2

    try:
        if args.json:
            print(
                github_summary_json(
                    root=root,
                    config=config,
                    from_run=args.from_run,
                    from_verify=args.from_verify,
                    from_session=args.from_session,
                ),
                end="",
            )
        else:
            print(
                render_github_summary(
                    root=root,
                    config=config,
                    from_run=args.from_run,
                    from_verify=args.from_verify,
                    from_session=args.from_session,
                ),
                end="",
            )
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z github-summary: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z github-summary: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z github-summary: configuration error: {exc}")
        return 2


def create_verify_candidate_run(
    *,
    root: Path,
    config: dict[str, Any],
    rerun_output_dir: Path,
    strict_no_tests: bool,
    baseline: VerificationRun,
) -> str:
    """Run fast and deep checks to create candidate evidence for verification."""
    contract_path = None
    if baseline.fast_summary.contract_path:
        candidate_contract = resolve_cli_path(root, baseline.fast_summary.contract_path)
        if candidate_contract.is_file():
            contract_path = candidate_contract

    fast_run = run_fast(
        root=root,
        config=config,
        contract_path=contract_path,
        output_dir=rerun_output_dir,
        strict_no_tests=strict_no_tests,
        selection_mode=resolve_fast_selection_mode(config, None),
    )
    artifact_dir = Path(fast_run.summary.artifact_dir or "")
    if not artifact_dir.is_absolute():
        artifact_dir = root / artifact_dir
    summary_path = write_run_summary_artifacts(fast_run.summary, artifact_dir)
    run_dir = artifact_dir.parent
    write_latest_run_manifest(root, config, run_dir)

    deep_run = run_deep(
        root=root,
        config=config,
        from_run=str(run_dir),
        selection_mode=resolve_deep_selection_mode(config, None),
    )
    write_run_summary_artifacts(deep_run.summary, deep_run.resolution.deep_dir)
    write_sarif_artifact(
        deep_run.summary, deep_run.resolution.deep_dir / "results.sarif"
    )
    candidate_source = RunSource(
        run_dir=run_dir,
        fast_dir=summary_path.parent,
        summary_path=summary_path,
    )
    write_verify_rerun_review_artifacts(
        root=root,
        config=config,
        run_source=candidate_source,
        summary=load_run_summary(summary_path),
        deep_summary=load_sibling_deep_summary(candidate_source) or deep_run.summary,
    )
    return format_relative_path(run_dir, root)


def write_verify_rerun_review_artifacts(
    *,
    root: Path,
    config: dict[str, Any],
    run_source: RunSource,
    summary: Any,
    deep_summary: Any,
) -> None:
    """Write run-aware review artifacts for a freshly rerun candidate."""
    contract_path = resolve_contract_source(root, config, summary=summary)
    contract = load_contract_context(contract_path, root)
    markdown = render_run_review_packet(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    json_text = run_review_packet_json(
        summary=summary,
        run_source=run_source,
        contract=contract,
        root=root,
        deep_summary=deep_summary,
    )
    write_review_artifacts(markdown, json_text, run_source.run_dir / "review")


def handle_verify(args: argparse.Namespace) -> int:
    """Compare a baseline run against a post-repair candidate run."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "verify")
    if config is None:
        return 2

    if bool(args.candidate_run) == bool(args.rerun):
        print(
            "qa-z verify: configuration error: provide exactly one of "
            "--candidate-run or --rerun."
        )
        return 2

    try:
        baseline, _baseline_source = load_verification_run(
            root=root,
            config=config,
            from_run=args.baseline_run,
        )
        if args.rerun:
            rerun_output_dir = (
                resolve_cli_path(root, args.rerun_output_dir)
                if args.rerun_output_dir
                else root / ".qa-z" / "runs" / "candidate"
            )
            candidate_run = create_verify_candidate_run(
                root=root,
                config=config,
                rerun_output_dir=rerun_output_dir,
                strict_no_tests=args.strict_no_tests,
                baseline=baseline,
            )
        else:
            candidate_run = args.candidate_run

        candidate, candidate_source = load_verification_run(
            root=root,
            config=config,
            from_run=candidate_run,
        )
        comparison = compare_verification_runs(baseline, candidate)
        output_dir = (
            resolve_cli_path(root, args.output_dir)
            if args.output_dir
            else candidate_source.run_dir / "verify"
        )
        paths = write_verification_artifacts(comparison, output_dir)

        if args.json:
            print(comparison_json(comparison), end="")
        else:
            print(render_verify_stdout(comparison.verdict, paths, root))
        return verify_exit_code(comparison.verdict)
    except ArtifactLoadError as exc:
        print(f"qa-z verify: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z verify: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z verify: configuration error: {exc}")
        return 2


def handle_benchmark(args: argparse.Namespace) -> int:
    """Run the local QA-Z benchmark fixture corpus."""
    root = Path(args.path).expanduser().resolve()
    fixtures_dir = resolve_cli_path(root, args.fixtures_dir)
    results_dir = resolve_cli_path(root, args.results_dir)

    try:
        summary = run_benchmark(
            fixtures_dir=fixtures_dir,
            results_dir=results_dir,
            fixture_names=args.fixture,
        )
    except BenchmarkError as exc:
        print(f"qa-z benchmark: benchmark error: {exc}")
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True), end="\n")
    else:
        print(render_benchmark_report(summary), end="")
    return 0 if summary["fixtures_failed"] == 0 else 1


def handle_self_inspect(args: argparse.Namespace) -> int:
    """Inspect local QA-Z artifacts and update the improvement backlog."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    paths = run_self_inspection(root=root)
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True), end="\n")
    else:
        print(render_self_inspect_stdout(report, paths, root))
    return 0


def handle_backlog(args: argparse.Namespace) -> int:
    """Print the current self-improvement backlog."""
    root = Path(args.path).expanduser().resolve()
    backlog = load_backlog(root)
    if args.json:
        print(json.dumps(backlog, indent=2, sort_keys=True), end="\n")
    else:
        print(render_backlog_stdout(backlog))
    return 0


def handle_select_next(args: argparse.Namespace) -> int:
    """Select the next one to three self-improvement backlog tasks."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    paths = select_next_tasks(root=root, count=args.count)
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(selected, indent=2, sort_keys=True), end="\n")
    else:
        print(render_select_next_stdout(selected, paths, root))
    return 0


def render_self_inspect_stdout(report: dict[str, Any], paths: Any, root: Path) -> str:
    """Render human output for qa-z self-inspect."""
    return "\n".join(
        [
            f"Self inspection: {report.get('candidates_total', 0)} candidate(s)",
            f"Report: {format_relative_path(paths.self_inspection_path, root)}",
            f"Backlog: {format_relative_path(paths.backlog_path, root)}",
            "No code was edited; this command only inspected local artifacts.",
        ]
    )


def render_backlog_stdout(backlog: dict[str, Any]) -> str:
    """Render human output for qa-z backlog."""
    open_items = open_backlog_items(backlog)
    lines = [f"Open backlog items: {len(open_items)}"]
    for item in open_items[:10]:
        lines.append(
            f"- {item.get('id')} [{item.get('category')}] "
            f"score={item.get('priority_score')}: {item.get('title')}"
        )
        lines.append(f"  Evidence: {compact_backlog_evidence_summary(item)}")
    return "\n".join(lines)


def render_select_next_stdout(selected: dict[str, Any], paths: Any, root: Path) -> str:
    """Render human output for qa-z select-next."""
    lines = [
        f"Selected tasks: {selected.get('selected_count', 0)}",
        f"Selected: {format_relative_path(paths.selected_tasks_path, root)}",
        f"Loop plan: {format_relative_path(paths.loop_plan_path, root)}",
        f"History: {format_relative_path(paths.history_path, root)}",
    ]
    for task in selected.get("selected_tasks", []):
        lines.append(
            f"- {task.get('id')} [{task.get('category')}] "
            f"score={task.get('priority_score')}: {task.get('title')}"
        )
        lines.append(f"  Action: {task.get('action_hint')}")
        lines.append(f"  Validation: {task.get('validation_command')}")
        lines.append(f"  Evidence: {task.get('compact_evidence')}")
    return "\n".join(lines)


def handle_autonomy(args: argparse.Namespace) -> int:
    """Run deterministic self-improvement planning loops."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    min_runtime_seconds = float(args.min_runtime_hours) * 3600
    summary = run_autonomy(
        root=root,
        loops=args.loops,
        count=args.count,
        min_runtime_seconds=min_runtime_seconds,
        min_loop_seconds=args.min_loop_seconds,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True), end="\n")
    else:
        print(render_autonomy_summary(summary, root))
    return 0


def handle_autonomy_status(args: argparse.Namespace) -> int:
    """Print the latest autonomy loop status."""
    root = Path(args.path).expanduser().resolve()
    status = load_autonomy_status(root)
    if args.json:
        print(json.dumps(status, indent=2, sort_keys=True), end="\n")
    else:
        print(render_autonomy_status(status))
    return 0


def handle_executor_bridge(args: argparse.Namespace) -> int:
    """Package loop or session evidence for an external executor."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    output_dir = resolve_cli_path(root, args.output_dir) if args.output_dir else None
    try:
        paths = create_executor_bridge(
            root=root,
            from_loop=args.from_loop,
            from_session=args.from_session,
            bridge_id=args.bridge_id,
            output_dir=output_dir,
        )
        manifest = json.loads(paths.manifest_path.read_text(encoding="utf-8"))
        if args.json:
            print(json.dumps(manifest, indent=2, sort_keys=True), end="\n")
        else:
            print(render_bridge_stdout(manifest))
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z executor-bridge: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z executor-bridge: source not found: {exc}")
        return 4
    except ExecutorBridgeError as exc:
        print(f"qa-z executor-bridge: configuration error: {exc}")
        return 2


def resolve_cli_path(root: Path, value: str) -> Path:
    """Resolve a CLI path relative to the project root when it is not absolute."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()


def load_cli_config(
    root: Path, args: argparse.Namespace, command: str
) -> dict[str, Any] | None:
    """Load config for a CLI command and print normalized errors."""
    config_path = Path(args.config).expanduser().resolve() if args.config else None
    try:
        return load_config(root, config_path=config_path)
    except ConfigError as exc:
        print(f"qa-z {command}: configuration error: {exc}")
        return None


def resolve_fast_selection_mode(config: dict[str, Any], explicit: str | None) -> str:
    """Resolve the fast selection mode from CLI input or config default."""
    if explicit:
        return explicit
    configured = str(
        get_nested(config, "fast", "selection", "default_mode", default="full")
    )
    return configured if configured in {"full", "smart"} else "full"


def resolve_deep_selection_mode(config: dict[str, Any], explicit: str | None) -> str:
    """Resolve the deep selection mode from CLI input or config default."""
    if explicit:
        return explicit
    configured = str(
        get_nested(config, "deep", "selection", "default_mode", default="full")
    )
    return configured if configured in {"full", "smart"} else "full"


def render_fast_stdout(
    status: str, contract_path: str | None, summary_path: Path, root: Path
) -> str:
    """Render the default human CLI output for qa-z fast."""
    try:
        relative_summary = summary_path.relative_to(root).as_posix()
    except ValueError:
        relative_summary = str(summary_path)
    contract = contract_path or "none"
    return "\n".join(
        [
            f"qa-z fast: {status}",
            f"Contract: {contract}",
            f"Summary: {relative_summary}",
        ]
    )


def render_deep_stdout(status: str, summary_path: Path, root: Path) -> str:
    """Render the default human CLI output for qa-z deep."""
    try:
        relative_summary = summary_path.relative_to(root).as_posix()
    except ValueError:
        relative_summary = str(summary_path)
    return "\n".join(
        [
            f"qa-z deep: {status}",
            f"Summary: {relative_summary}",
        ]
    )


def render_verify_stdout(
    verdict: str, paths: VerificationArtifactPaths, root: Path
) -> str:
    """Render the default human CLI output for qa-z verify."""
    return "\n".join(
        [
            f"qa-z verify: {verdict}",
            f"Summary: {format_relative_path(paths.summary_path, root)}",
            f"Compare: {format_relative_path(paths.compare_path, root)}",
            f"Report: {format_relative_path(paths.report_path, root)}",
        ]
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the root CLI parser."""
    parser = argparse.ArgumentParser(
        prog="qa-z",
        description="QA-Z is a QA control plane scaffold for coding agents.",
    )
    subparsers = parser.add_subparsers(dest="command")

    init_parser = subparsers.add_parser(
        "init",
        help="write a starter qa-z.yaml and contracts workspace",
    )
    init_parser.add_argument(
        "--path",
        default=".",
        help="directory to initialize, defaults to the current working directory",
    )
    init_parser.set_defaults(handler=handle_init)

    plan_parser = subparsers.add_parser(
        "plan",
        help="generate a QA contract draft from title and context files",
    )
    plan_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and contract output directories",
    )
    plan_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    plan_parser.add_argument(
        "--title",
        help="human-readable title for the contract",
    )
    plan_parser.add_argument(
        "--slug",
        help="optional custom file slug for the generated contract",
    )
    plan_parser.add_argument(
        "--issue",
        help="optional path to issue context markdown or text",
    )
    plan_parser.add_argument(
        "--spec",
        help="optional path to spec context markdown or text",
    )
    plan_parser.add_argument(
        "--diff",
        help="optional path to a diff excerpt or patch file",
    )
    plan_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="overwrite an existing contract draft with the same slug",
    )
    plan_parser.set_defaults(handler=handle_plan)

    review_parser = subparsers.add_parser(
        "review",
        help="render a review packet from a generated contract",
    )
    review_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and contract output directories",
    )
    review_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    review_parser.add_argument(
        "--contract",
        help="optional explicit contract path; defaults to the newest contract in the configured output directory",
    )
    review_parser.add_argument(
        "--from-run",
        help="optional run root, fast directory, summary.json, or latest fast run artifact",
    )
    review_parser.add_argument(
        "--json",
        action="store_true",
        help="print a machine-readable review packet to stdout",
    )
    review_parser.add_argument(
        "--output-dir",
        help="optional directory for review.md and review.json artifacts",
    )
    review_parser.set_defaults(handler=handle_review)

    fast_parser = subparsers.add_parser(
        "fast",
        help="run fast deterministic checks",
    )
    fast_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and contract output directories",
    )
    fast_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    fast_parser.add_argument(
        "--contract",
        help="optional explicit contract path; defaults to the newest contract in the configured output directory",
    )
    fast_parser.add_argument(
        "--output-dir",
        help="optional run artifact directory; defaults to fast.output_dir plus a UTC timestamp",
    )
    fast_parser.add_argument(
        "--selection",
        choices=("full", "smart"),
        default=None,
        help="check selection mode; defaults to fast.selection.default_mode or full",
    )
    fast_parser.add_argument(
        "--diff",
        help="optional diff excerpt or patch file for smart selection",
    )
    fast_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable run summary to stdout",
    )
    fast_parser.add_argument(
        "--strict-no-tests",
        action="store_true",
        help="treat pytest no-tests exit code as a failure",
    )
    fast_parser.set_defaults(handler=handle_fast)

    deep_parser = subparsers.add_parser(
        "deep",
        help="run deeper risk-oriented checks",
    )
    deep_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    deep_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    deep_parser.add_argument(
        "--from-run",
        help="optional run root, fast directory, summary.json, or latest fast run artifact",
    )
    deep_parser.add_argument(
        "--output-dir",
        help="optional run artifact directory; defaults to latest fast run or a new run",
    )
    deep_parser.add_argument(
        "--selection",
        choices=("full", "smart"),
        default=None,
        help="deep check selection mode; defaults to deep.selection.default_mode or full",
    )
    deep_parser.add_argument(
        "--diff",
        help="optional diff excerpt or patch file for smart selection",
    )
    deep_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable deep summary to stdout",
    )
    deep_parser.add_argument(
        "--sarif-output",
        help=(
            "optional extra path for SARIF 2.1.0 output; deep always writes "
            "results.sarif next to summary.json"
        ),
    )
    deep_parser.set_defaults(handler=handle_deep)

    repair_parser = subparsers.add_parser(
        "repair-prompt",
        help="emit an agent-friendly repair prompt",
    )
    repair_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    repair_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    repair_parser.add_argument(
        "--from-run",
        default="latest",
        help="run root, fast directory, summary.json, or latest fast run artifact",
    )
    repair_parser.add_argument(
        "--contract",
        help="optional explicit contract path overriding the run summary contract",
    )
    repair_parser.add_argument(
        "--output-dir",
        help="optional repair artifact directory; defaults to source run/repair",
    )
    repair_output_group = repair_parser.add_mutually_exclusive_group()
    repair_output_group.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable repair packet to stdout",
    )
    repair_output_group.add_argument(
        "--handoff-json",
        action="store_true",
        help="print the normalized executor handoff JSON to stdout",
    )
    repair_parser.add_argument(
        "--adapter",
        choices=("legacy", "codex", "claude"),
        default="legacy",
        help="stdout renderer for Markdown output; artifacts always include all adapters",
    )
    repair_parser.set_defaults(handler=handle_repair_prompt)

    repair_session_parser = subparsers.add_parser(
        "repair-session",
        help="create and verify local repair-session artifacts",
    )
    repair_session_subparsers = repair_session_parser.add_subparsers(
        dest="repair_session_command"
    )

    repair_session_start = repair_session_subparsers.add_parser(
        "start",
        help="create a repair session from a baseline run",
    )
    repair_session_start.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    repair_session_start.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    repair_session_start.add_argument(
        "--baseline-run",
        required=True,
        help="baseline run root, fast directory, summary.json, or latest",
    )
    repair_session_start.add_argument(
        "--session-id",
        help="optional stable id for the session directory",
    )
    repair_session_start.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable repair-session manifest to stdout",
    )
    repair_session_start.set_defaults(handler=handle_repair_session_start)

    repair_session_status = repair_session_subparsers.add_parser(
        "status",
        help="print a repair-session manifest",
    )
    repair_session_status.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z session artifacts",
    )
    repair_session_status.add_argument(
        "--session",
        required=True,
        help="session id, directory, or session.json path",
    )
    repair_session_status.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable repair-session manifest to stdout",
    )
    repair_session_status.set_defaults(handler=handle_repair_session_status)

    repair_session_verify = repair_session_subparsers.add_parser(
        "verify",
        help="verify a candidate run for a repair session",
    )
    repair_session_verify.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    repair_session_verify.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    repair_session_verify.add_argument(
        "--session",
        required=True,
        help="session id, directory, or session.json path",
    )
    repair_session_verify.add_argument(
        "--candidate-run",
        required=True,
        help="candidate run root, fast directory, summary.json, or latest",
    )
    repair_session_verify.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable repair-session summary to stdout",
    )
    repair_session_verify.set_defaults(handler=handle_repair_session_verify)

    github_summary_parser = subparsers.add_parser(
        "github-summary",
        help="render local QA-Z evidence for GitHub Actions summaries",
    )
    github_summary_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    github_summary_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    github_summary_parser.add_argument(
        "--from-run",
        help="run root, fast directory, summary.json, or latest",
    )
    github_summary_parser.add_argument(
        "--from-verify",
        help="verification summary.json path",
    )
    github_summary_parser.add_argument(
        "--from-session",
        help="repair session id, directory, or summary.json path",
    )
    github_summary_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable publish summary to stdout",
    )
    github_summary_parser.set_defaults(handler=handle_github_summary)

    verify_parser = subparsers.add_parser(
        "verify",
        help="compare a baseline run against a post-repair candidate run",
    )
    verify_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    verify_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    verify_parser.add_argument(
        "--baseline-run",
        required=True,
        help="baseline run root, fast directory, summary.json, or latest",
    )
    candidate_group = verify_parser.add_mutually_exclusive_group()
    candidate_group.add_argument(
        "--candidate-run",
        help="candidate run root, fast directory, summary.json, or latest",
    )
    candidate_group.add_argument(
        "--rerun",
        action="store_true",
        help="run qa-z fast and qa-z deep to create a candidate before comparing",
    )
    verify_parser.add_argument(
        "--rerun-output-dir",
        help="optional run directory for --rerun candidate artifacts",
    )
    verify_parser.add_argument(
        "--output-dir",
        help="optional verify artifact directory; defaults to candidate-run/verify",
    )
    verify_parser.add_argument(
        "--strict-no-tests",
        action="store_true",
        help="with --rerun, treat pytest no-tests exit code as a failure",
    )
    verify_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable verification comparison to stdout",
    )
    verify_parser.set_defaults(handler=handle_verify)

    benchmark_parser = subparsers.add_parser(
        "benchmark",
        help="run the seeded QA-Z benchmark corpus",
    )
    benchmark_parser.add_argument(
        "--path",
        default=".",
        help="repository root used to resolve benchmark fixture and results paths",
    )
    benchmark_parser.add_argument(
        "--fixtures-dir",
        default=DEFAULT_FIXTURES_DIR.as_posix(),
        help="directory containing benchmark fixtures with expected.json files",
    )
    benchmark_parser.add_argument(
        "--results-dir",
        default=DEFAULT_RESULTS_DIR.as_posix(),
        help="directory for benchmark summary/report artifacts",
    )
    benchmark_parser.add_argument(
        "--fixture",
        action="append",
        help="run only the named fixture; repeat to select multiple fixtures",
    )
    benchmark_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable benchmark summary to stdout",
    )
    benchmark_parser.set_defaults(handler=handle_benchmark)
    self_inspect_parser = subparsers.add_parser(
        "self-inspect",
        help="inspect local QA-Z artifacts and update the improvement backlog",
    )
    self_inspect_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    self_inspect_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable self-inspection report to stdout",
    )
    self_inspect_parser.set_defaults(handler=handle_self_inspect)

    backlog_parser = subparsers.add_parser(
        "backlog",
        help="print the artifact-derived improvement backlog",
    )
    backlog_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    backlog_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable backlog to stdout",
    )
    backlog_parser.set_defaults(handler=handle_backlog)

    select_next_parser = subparsers.add_parser(
        "select-next",
        help="select the next artifact-derived improvement tasks",
    )
    select_next_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    select_next_parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="number of open backlog items to select, clamped to 1 through 3",
    )
    select_next_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable selected-task artifact to stdout",
    )
    select_next_parser.set_defaults(handler=handle_select_next)
    autonomy_parser = subparsers.add_parser(
        "autonomy",
        help="run deterministic self-improvement planning loops",
    )
    autonomy_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    autonomy_parser.add_argument(
        "--loops",
        type=int,
        default=1,
        help="minimum number of planning loops to run",
    )
    autonomy_parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="number of backlog items to select per loop, clamped by select-next",
    )
    autonomy_parser.add_argument(
        "--min-runtime-hours",
        type=float,
        default=0.0,
        help="minimum wall-clock runtime budget in hours before stopping",
    )
    autonomy_parser.add_argument(
        "--min-loop-seconds",
        type=float,
        default=0.0,
        help="minimum elapsed seconds to account for each loop",
    )
    autonomy_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable autonomy summary to stdout",
    )
    autonomy_subparsers = autonomy_parser.add_subparsers(dest="autonomy_command")
    autonomy_status_parser = autonomy_subparsers.add_parser(
        "status",
        help="print the latest autonomy loop status",
    )
    autonomy_status_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    autonomy_status_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable autonomy status to stdout",
    )
    autonomy_status_parser.set_defaults(handler=handle_autonomy_status)
    autonomy_parser.set_defaults(handler=handle_autonomy)

    executor_bridge_parser = subparsers.add_parser(
        "executor-bridge",
        help="package a repair session for an external executor",
    )
    executor_bridge_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    bridge_source_group = executor_bridge_parser.add_mutually_exclusive_group(
        required=True
    )
    bridge_source_group.add_argument(
        "--from-loop",
        help="autonomy loop id, loop directory, or outcome.json path",
    )
    bridge_source_group.add_argument(
        "--from-session",
        help="repair-session id, session directory, or session.json path",
    )
    executor_bridge_parser.add_argument(
        "--bridge-id",
        help="optional stable bridge id; defaults to timestamp plus source id",
    )
    executor_bridge_parser.add_argument(
        "--output-dir",
        help="optional bridge package directory; defaults to .qa-z/executor/<bridge-id>",
    )
    executor_bridge_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable bridge manifest to stdout",
    )
    executor_bridge_parser.set_defaults(handler=handle_executor_bridge)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    return int(args.handler(args))
