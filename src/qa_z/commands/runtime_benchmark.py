"""Benchmark CLI command for local deterministic runtime workflows."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from qa_z.benchmark import (
    DEFAULT_FIXTURES_DIR,
    DEFAULT_RESULTS_DIR,
    BenchmarkError,
    render_benchmark_report,
    run_benchmark,
)
from qa_z.commands.common import resolve_cli_path

__all__ = [
    "handle_benchmark",
    "register_benchmark_command",
]


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


def register_benchmark_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the benchmark command."""
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
