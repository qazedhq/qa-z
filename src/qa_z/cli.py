"""Command line interface for QA-Z."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from .artifacts import (
    ArtifactLoadError,
    ArtifactSourceNotFound,
    load_contract_context,
    load_run_summary,
    resolve_contract_source,
    resolve_run_source,
    write_latest_run_manifest,
)
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
from .executor_bridge import (
    ExecutorBridgeError,
    create_executor_bridge,
    render_bridge_stdout,
)
from .executor_dry_run import run_executor_result_dry_run
from .executor_ingest import (
    ExecutorResultIngestRejected,
    create_verify_candidate_run,
    ingest_executor_result_artifact,
    verify_repair_session,
)
from .self_improvement import (
    SelectionArtifactPaths,
    compact_backlog_evidence_summary,
    int_value,
    load_backlog,
    open_backlog_items,
    run_self_inspection,
    select_next_tasks,
    selected_task_action_hint,
    selected_task_validation_command,
)
from .adapters.claude import render_claude_handoff
from .adapters.codex import render_codex_handoff
from .config import (
    COMMAND_GUIDANCE,
    CONTRACTS_README,
    EXAMPLE_CONFIG,
    ConfigError,
    get_nested,
    load_config,
)
from .planner.contracts import plan_contract
from .reporters.deep_context import load_sibling_deep_summary
from .reporters.repair_prompt import (
    build_repair_packet,
    repair_packet_json,
    write_repair_artifacts,
)
from .repair_handoff import (
    build_repair_handoff,
    repair_handoff_json,
    write_repair_handoff_artifact,
)
from .repair_session import (
    create_repair_session,
    load_repair_session,
    load_session_dry_run_summary,
    render_session_start_stdout,
    render_session_status_with_dry_run,
    render_session_verify_stdout,
    session_status_dict,
    session_summary_json,
)
from .reporters.github_summary import render_github_summary
from .reporters.run_summary import write_run_summary_artifacts
from .reporters.verification_publish import (
    detect_publish_summary_for_run,
    load_session_publish_summary,
)
from .reporters.sarif import write_sarif_artifact
from .reporters.review_packet import (
    find_latest_contract,
    render_review_packet,
    render_run_review_packet,
    review_packet_json,
    run_review_packet_json,
    write_review_artifacts,
)
from .runners.deep import run_deep
from .runners.fast import run_fast, summary_json
from .verification import (
    VerificationArtifactPaths,
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


def handle_github_summary(args: argparse.Namespace) -> int:
    """Render compact Markdown for GitHub Actions job summaries."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "github-summary")
    if config is None:
        return 2

    try:
        run_source = resolve_run_source(root, config, args.from_run)
        summary = load_run_summary(run_source.summary_path)
        deep_summary = load_sibling_deep_summary(run_source)
        publish_summary = (
            load_session_publish_summary(root=root, session=args.from_session)
            if args.from_session
            else detect_publish_summary_for_run(root=root, run_source=run_source)
        )
        markdown = render_github_summary(
            summary=summary,
            run_source=run_source,
            root=root,
            deep_summary=deep_summary,
            publish_summary=publish_summary,
        )
        if args.output:
            output_path = resolve_cli_path(root, args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(markdown, encoding="utf-8")
        print(markdown, end="")
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z github-summary: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z github-summary: source not found: {exc}")
        return 4


def handle_self_inspect(args: argparse.Namespace) -> int:
    """Inspect local QA-Z artifacts and update the improvement backlog."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    paths = run_self_inspection(root=root)
    report = json.loads(paths.self_inspection_path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True), end="\n")
    else:
        print(
            render_self_inspect_stdout(
                report,
                self_inspection_path=paths.self_inspection_path,
                backlog_path=paths.backlog_path,
                root=root,
            )
        )
    return 0


def render_self_inspect_stdout(
    report: dict[str, Any],
    *,
    self_inspection_path: Path,
    backlog_path: Path,
    root: Path,
) -> str:
    """Render human stdout for qa-z self-inspect."""
    candidates = [
        item for item in report.get("candidates", []) if isinstance(item, dict)
    ]
    lines = [
        "qa-z self-inspect: wrote self-improvement artifacts",
        f"Self inspection: {format_relative_path(self_inspection_path, root)}",
        f"Backlog: {format_relative_path(backlog_path, root)}",
        f"Candidates: {len(candidates)}",
        "Top candidates:",
    ]
    if not candidates:
        lines.append("- none")
    top_candidates = sorted(
        candidates,
        key=lambda item: (-int_value(item.get("priority_score")), str(item.get("id"))),
    )
    for item in top_candidates[:3]:
        lines.extend(
            [
                f"- {item.get('id')}: {item.get('title', item.get('id', 'untitled'))}",
                f"  recommendation: {item.get('recommendation', '')}",
                f"  action: {selected_task_action_hint(item)}",
                f"  validation: {selected_task_validation_command(item)}",
                f"  priority score: {item.get('priority_score', 0)}",
                f"  evidence: {compact_backlog_evidence_summary(item)}",
            ]
        )
    return "\n".join(lines)


def handle_select_next(args: argparse.Namespace) -> int:
    """Select the next highest-priority self-improvement tasks."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    paths = select_next_tasks(root=root, count=args.count)
    selected = json.loads(paths.selected_tasks_path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(selected, indent=2, sort_keys=True), end="\n")
    else:
        print(render_select_next_stdout(selected, paths, root))
    return 0


def handle_backlog(args: argparse.Namespace) -> int:
    """Print the current improvement backlog."""
    root = Path(args.path).expanduser().resolve()
    backlog = load_backlog(root)
    if args.json:
        print(json.dumps(backlog, indent=2, sort_keys=True), end="\n")
    else:
        print(render_backlog(backlog))
    return 0


def render_backlog(backlog: dict[str, Any]) -> str:
    """Render a human backlog summary that focuses on active work."""
    items = [item for item in backlog.get("items", []) if isinstance(item, dict)]
    open_items = open_backlog_items(backlog)
    closed_items = [
        item
        for item in items
        if str(item.get("status", "open")) not in {"open", "selected", "in_progress"}
    ]
    lines = [
        f"qa-z backlog: {len(items)} item(s)",
        f"Open items: {len(open_items)}",
    ]
    if not open_items:
        lines.append("- none")
    for item in open_items:
        lines.extend(
            [
                f"- {item.get('id')}: {item.get('title', item.get('id', 'untitled'))}",
                "  status: "
                f"{item.get('status', 'open')} | "
                f"priority: {item.get('priority_score', 0)} | "
                f"recommendation: {item.get('recommendation', '')}",
                f"  action: {selected_task_action_hint(item)}",
                f"  validation: {selected_task_validation_command(item)}",
                f"  evidence: {compact_backlog_evidence_summary(item)}",
            ]
        )
    lines.extend(
        [
            f"Closed items: {len(closed_items)}",
            "- use `qa-z backlog --json` for the full history"
            if closed_items
            else "- no closed history recorded",
        ]
    )
    return "\n".join(lines)


def render_select_next_stdout(
    selected: dict[str, Any], paths: SelectionArtifactPaths, root: Path
) -> str:
    """Render human stdout for qa-z select-next."""
    items = [
        item for item in selected.get("selected_tasks", []) if isinstance(item, dict)
    ]
    lines = [
        "qa-z select-next: wrote loop planning artifacts",
        f"Selected tasks: {format_relative_path(paths.selected_tasks_path, root)}",
        f"Loop plan: {format_relative_path(paths.loop_plan_path, root)}",
        f"History: {format_relative_path(paths.history_path, root)}",
        f"Count: {len(items)}",
        "Selected task details:",
    ]
    if not items:
        lines.append("- none")
    for item in items:
        lines.append(
            f"- {item.get('id')}: {item.get('title', item.get('id', 'untitled'))}"
        )
        if item.get("recommendation"):
            lines.append(f"  recommendation: {item['recommendation']}")
        lines.append(f"  action: {selected_task_action_hint(item)}")
        lines.append(f"  validation: {selected_task_validation_command(item)}")
        selection_score = item.get(
            "selection_priority_score", item.get("priority_score")
        )
        if selection_score is not None:
            lines.append(f"  selection score: {selection_score}")
        selection_penalty = item.get("selection_penalty")
        penalty_reasons = [
            str(reason)
            for reason in item.get("selection_penalty_reasons", [])
            if isinstance(reason, str) and reason.strip()
        ]
        if selection_penalty:
            if penalty_reasons:
                lines.append(
                    "  selection penalty: "
                    f"{selection_penalty} ({', '.join(penalty_reasons)})"
                )
            else:
                lines.append(f"  selection penalty: {selection_penalty}")
        evidence_summary = compact_backlog_evidence_summary(item)
        if evidence_summary:
            lines.append(f"  evidence: {evidence_summary}")
    return "\n".join(lines)


def handle_autonomy(args: argparse.Namespace) -> int:
    """Run or inspect deterministic autonomy planning loops."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if args.autonomy_command == "status":
        status = load_autonomy_status(root)
        if args.json:
            print(json.dumps(status, indent=2, sort_keys=True), end="\n")
        else:
            print(render_autonomy_status(status))
        return 0

    config = load_cli_config(root, args, "autonomy")
    if config is None:
        return 2
    summary = run_autonomy(
        root=root,
        config=config,
        loops=args.loops,
        count=args.count,
        min_runtime_seconds=args.min_runtime_hours * 3600,
        min_loop_seconds=args.min_loop_seconds,
    )
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True), end="\n")
    else:
        print(render_autonomy_summary(summary, root))
    return 0


def handle_executor_bridge(args: argparse.Namespace) -> int:
    """Package autonomy/session evidence for an external executor."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    if bool(args.from_loop) == bool(args.from_session):
        print(
            "qa-z executor-bridge: configuration error: provide exactly one of "
            "--from-loop or --from-session."
        )
        return 2
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


def handle_repair_session_start(args: argparse.Namespace) -> int:
    """Create a local repair-session from a baseline run."""
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
        print(render_session_start_stdout(result.session))
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z repair-session start: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-session start: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z repair-session start: configuration error: {exc}")
        return 2


def handle_repair_session_status(args: argparse.Namespace) -> int:
    """Print the current state of a repair-session."""
    root = Path(args.path).expanduser().resolve()

    try:
        session = load_repair_session(root, args.session)
        dry_run_summary = load_session_dry_run_summary(session, root)
        if args.json:
            print(
                json.dumps(
                    session_status_dict(session, dry_run_summary=dry_run_summary),
                    indent=2,
                    sort_keys=True,
                ),
                end="\n",
            )
        else:
            print(
                render_session_status_with_dry_run(
                    session,
                    dry_run_summary=dry_run_summary,
                )
            )
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z repair-session status: artifact error: {exc}")
        return 2


def handle_repair_session_verify(args: argparse.Namespace) -> int:
    """Verify a repair-session with an existing or freshly rerun candidate."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "repair-session verify")
    if config is None:
        return 2

    if bool(args.candidate_run) == bool(args.rerun):
        print(
            "qa-z repair-session verify: configuration error: provide exactly one "
            "of --candidate-run or --rerun."
        )
        return 2

    try:
        session = load_repair_session(root, args.session)
        updated, summary, comparison = verify_repair_session(
            session=session,
            root=root,
            config=config,
            candidate_run=args.candidate_run,
            rerun=args.rerun,
            rerun_output_dir=args.rerun_output_dir,
            strict_no_tests=args.strict_no_tests,
            output_dir=args.output_dir,
        )

        if args.json:
            print(session_summary_json(summary), end="")
        else:
            print(render_session_verify_stdout(updated, summary))
        return verify_exit_code(comparison.verdict)
    except ArtifactLoadError as exc:
        print(f"qa-z repair-session verify: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z repair-session verify: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z repair-session verify: configuration error: {exc}")
        return 2


def handle_executor_result_ingest(args: argparse.Namespace) -> int:
    """Ingest an external executor result and optionally resume verification."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    config = load_cli_config(root, args, "executor-result ingest")
    if config is None:
        return 2

    try:
        outcome = ingest_executor_result_artifact(
            root=root,
            config=config,
            result_path=args.result,
        )
        if args.json:
            print(json.dumps(outcome.summary, indent=2, sort_keys=True), end="\n")
        else:
            print(render_executor_result_ingest_stdout(outcome.summary))
        if (
            outcome.summary.get("verification_triggered")
            and outcome.verification_verdict
        ):
            return verify_exit_code(outcome.verification_verdict)
        return 0
    except ExecutorResultIngestRejected as exc:
        if args.json:
            print(json.dumps(exc.outcome.summary, indent=2, sort_keys=True), end="\n")
        else:
            print(render_executor_result_ingest_stdout(exc.outcome.summary))
        return exc.exit_code
    except ArtifactLoadError as exc:
        print(f"qa-z executor-result ingest: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z executor-result ingest: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z executor-result ingest: configuration error: {exc}")
        return 2


def handle_executor_result_dry_run(args: argparse.Namespace) -> int:
    """Run a live-free safety dry-run against one session history."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    try:
        outcome = run_executor_result_dry_run(root=root, session_ref=args.session)
        if args.json:
            print(json.dumps(outcome.summary, indent=2, sort_keys=True), end="\n")
        else:
            print(render_executor_result_dry_run_stdout(outcome.summary))
        return 0
    except ArtifactLoadError as exc:
        print(f"qa-z executor-result dry-run: artifact error: {exc}")
        return 2
    except (ArtifactSourceNotFound, FileNotFoundError) as exc:
        print(f"qa-z executor-result dry-run: source not found: {exc}")
        return 4
    except ValueError as exc:
        print(f"qa-z executor-result dry-run: configuration error: {exc}")
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


def handle_placeholder(args: argparse.Namespace) -> int:
    """Render roadmap guidance for a scaffolded command."""
    print(COMMAND_GUIDANCE[args.command])
    return 0


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


def render_executor_result_ingest_stdout(summary: dict[str, Any]) -> str:
    """Render human stdout for executor-result ingest."""
    return "\n".join(
        [
            f"qa-z executor-result ingest: {summary.get('ingest_status', summary['result_status'])}",
            f"Result: {summary['result_status']}",
            f"Session: {summary['session_id']}",
            f"Stored result: {summary.get('stored_result_path') or 'none'}",
            f"Verify resume: {summary.get('verify_resume_status', 'verify_blocked')}",
            f"Verification: {summary['verification_verdict'] or 'not_run'}",
            f"Next: {summary['next_recommendation']}",
        ]
    )


def render_executor_result_dry_run_stdout(summary: dict[str, Any]) -> str:
    """Render human stdout for executor-result dry-run."""
    lines = [
        f"qa-z executor-result dry-run: {summary['verdict']}",
        f"Session: {summary['session_id']}",
        f"Attempts: {summary['evaluated_attempt_count']}",
        f"Latest attempt: {summary.get('latest_attempt_id') or 'none'}",
    ]
    operator_summary = str(summary.get("operator_summary") or "").strip()
    if operator_summary:
        lines.append(f"Diagnostic: {operator_summary}")
    operator_decision = str(summary.get("operator_decision") or "").strip()
    if operator_decision:
        lines.append(f"Decision: {operator_decision}")
    actions = dry_run_action_summaries(summary.get("recommended_actions"))
    for action in actions[:3]:
        lines.append(f"Action: {action}")
    lines.append(f"Next: {summary['next_recommendation']}")
    return "\n".join(lines)


def dry_run_action_summaries(value: object) -> list[str]:
    """Return readable recommended dry-run actions from optional payload data."""
    if not isinstance(value, list):
        return []
    actions: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        summary = str(item.get("summary") or "").strip()
        if summary:
            actions.append(summary)
    return actions


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

    repair_session_parser = subparsers.add_parser(
        "repair-session",
        help="create and verify local repair workflow sessions",
    )
    repair_session_subparsers = repair_session_parser.add_subparsers(
        dest="repair_session_command"
    )

    repair_session_start_parser = repair_session_subparsers.add_parser(
        "start",
        help="create a repair session from a baseline run",
    )
    repair_session_start_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    repair_session_start_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    repair_session_start_parser.add_argument(
        "--baseline-run",
        required=True,
        help="baseline run root, fast directory, summary.json, or latest",
    )
    repair_session_start_parser.add_argument(
        "--session-id",
        help="optional stable session id; defaults to a UTC timestamp plus suffix",
    )
    repair_session_start_parser.set_defaults(handler=handle_repair_session_start)

    repair_session_status_parser = repair_session_subparsers.add_parser(
        "status",
        help="print repair-session state and artifact paths",
    )
    repair_session_status_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains .qa-z/sessions",
    )
    repair_session_status_parser.add_argument(
        "--session",
        required=True,
        help="session id, session directory, or session.json path",
    )
    repair_session_status_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable session manifest to stdout",
    )
    repair_session_status_parser.set_defaults(handler=handle_repair_session_status)

    repair_session_verify_parser = repair_session_subparsers.add_parser(
        "verify",
        help="verify a repair session against a candidate run",
    )
    repair_session_verify_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and session artifacts",
    )
    repair_session_verify_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    repair_session_verify_parser.add_argument(
        "--session",
        required=True,
        help="session id, session directory, or session.json path",
    )
    repair_session_candidate_group = (
        repair_session_verify_parser.add_mutually_exclusive_group()
    )
    repair_session_candidate_group.add_argument(
        "--candidate-run",
        help="candidate run root, fast directory, summary.json, or latest",
    )
    repair_session_candidate_group.add_argument(
        "--rerun",
        action="store_true",
        help="run qa-z fast and qa-z deep into the session candidate directory",
    )
    repair_session_verify_parser.add_argument(
        "--rerun-output-dir",
        help="optional run directory for a --rerun candidate",
    )
    repair_session_verify_parser.add_argument(
        "--output-dir",
        help="optional verify artifact directory; defaults to session/verify",
    )
    repair_session_verify_parser.add_argument(
        "--strict-no-tests",
        action="store_true",
        help="with --rerun, treat pytest no-tests exit code as a failure",
    )
    repair_session_verify_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable session outcome summary to stdout",
    )
    repair_session_verify_parser.set_defaults(handler=handle_repair_session_verify)

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

    select_next_parser = subparsers.add_parser(
        "select-next",
        help="select the next 1 to 3 self-improvement backlog tasks",
    )
    select_next_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains the improvement backlog",
    )
    select_next_parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="number of open tasks to select, clamped to 1 through 3",
    )
    select_next_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable selected-tasks artifact to stdout",
    )
    select_next_parser.set_defaults(handler=handle_select_next)

    backlog_parser = subparsers.add_parser(
        "backlog",
        help="print the current QA-Z improvement backlog",
    )
    backlog_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains the improvement backlog",
    )
    backlog_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable improvement backlog to stdout",
    )
    backlog_parser.set_defaults(handler=handle_backlog)

    autonomy_parser = subparsers.add_parser(
        "autonomy",
        help="run deterministic self-improvement planning loops",
    )
    autonomy_parser.add_argument(
        "autonomy_command",
        nargs="?",
        choices=("status",),
        help="print the latest autonomy workflow status",
    )
    autonomy_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    autonomy_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    autonomy_parser.add_argument(
        "--loops",
        type=int,
        default=1,
        help="number of planning loops to run",
    )
    autonomy_parser.add_argument(
        "--count",
        type=int,
        default=3,
        help="number of open tasks to select per loop, clamped to 1 through 3",
    )
    autonomy_parser.add_argument(
        "--min-runtime-hours",
        type=float,
        default=0.0,
        help="minimum wall-clock runtime budget in hours before the run may finish",
    )
    autonomy_parser.add_argument(
        "--min-loop-seconds",
        type=float,
        default=0.0,
        help="minimum wall-clock duration to spend in each loop before advancing",
    )
    autonomy_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable autonomy summary or status",
    )
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

    executor_result_parser = subparsers.add_parser(
        "executor-result",
        help="ingest an external executor result and resume QA-Z verification",
    )
    executor_result_subparsers = executor_result_parser.add_subparsers(
        dest="executor_result_command"
    )

    executor_result_ingest_parser = executor_result_subparsers.add_parser(
        "ingest",
        help="ingest an executor result JSON and optionally rerun verification",
    )
    executor_result_ingest_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    executor_result_ingest_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    executor_result_ingest_parser.add_argument(
        "--result",
        required=True,
        help="path to a filled executor result JSON artifact",
    )
    executor_result_ingest_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable ingest summary to stdout",
    )
    executor_result_ingest_parser.set_defaults(handler=handle_executor_result_ingest)
    executor_result_dry_run_parser = executor_result_subparsers.add_parser(
        "dry-run",
        help="evaluate session executor history against the pre-live safety package",
    )
    executor_result_dry_run_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains QA-Z artifacts",
    )
    executor_result_dry_run_parser.add_argument(
        "--session",
        required=True,
        help="repair-session id, session directory, or session.json path",
    )
    executor_result_dry_run_parser.add_argument(
        "--json",
        action="store_true",
        help="print the machine-readable dry-run summary to stdout",
    )
    executor_result_dry_run_parser.set_defaults(handler=handle_executor_result_dry_run)

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

    github_summary_parser = subparsers.add_parser(
        "github-summary",
        help="render compact Markdown for a GitHub Actions job summary",
    )
    github_summary_parser.add_argument(
        "--path",
        default=".",
        help="repository root that contains qa-z.yaml and run artifacts",
    )
    github_summary_parser.add_argument(
        "--config",
        help="optional explicit path to a qa-z config file",
    )
    github_summary_parser.add_argument(
        "--from-run",
        default="latest",
        help="run root, fast directory, summary.json, or latest fast run artifact",
    )
    github_summary_parser.add_argument(
        "--from-session",
        help=(
            "optional repair-session id, directory, or session.json whose "
            "outcome should be included"
        ),
    )
    github_summary_parser.add_argument(
        "--output",
        help="optional file path for the rendered GitHub summary Markdown",
    )
    github_summary_parser.set_defaults(handler=handle_github_summary)

    return parser


def main(argv: Iterable[str] | None = None) -> int:
    """Run the CLI."""
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if not hasattr(args, "handler"):
        parser.print_help()
        return 0

    return int(args.handler(args))
