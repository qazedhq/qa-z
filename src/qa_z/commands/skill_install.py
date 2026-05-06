"""Install QA-Z agent merge-safety instructions into a repository."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

from qa_z.commands.common import format_relative_path, resolve_cli_path


TARGETS = ("codex", "claude", "cursor", "copilot")
SECTION_START = "<!-- QA-Z MERGE SAFETY START -->"
SECTION_END = "<!-- QA-Z MERGE SAFETY END -->"


@dataclass(frozen=True)
class SkillInstallTarget:
    """One supported instruction target."""

    name: str
    default_path: str
    template_name: str


INSTALL_TARGETS = {
    "codex": SkillInstallTarget("codex", "AGENTS.md", "AGENTS.qa-z.md"),
    "claude": SkillInstallTarget("claude", "CLAUDE.md", "CLAUDE.qa-z.md"),
    "cursor": SkillInstallTarget("cursor", ".cursor/rules/qa-z.mdc", "CURSOR.qa-z.mdc"),
    "copilot": SkillInstallTarget(
        "copilot",
        ".github/copilot-instructions.md",
        "COPILOT.qa-z.instructions.md",
    ),
}


def handle_skill_install(args: argparse.Namespace) -> int:
    """Install one or more QA-Z instruction templates."""
    root = Path(args.path).expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    targets = list(TARGETS) if args.target == "all" else [args.target]
    if args.output and len(targets) > 1:
        print("qa-z skill install: argument error: --output can target only one file")
        return 2

    exit_code = 0
    for target_name in targets:
        target = INSTALL_TARGETS[target_name]
        output_path = (
            resolve_cli_path(root, args.output)
            if args.output
            else root / target.default_path
        )
        action = install_target(
            root=root,
            target=target,
            output_path=output_path,
            append=args.append,
            force=args.force,
            dry_run=args.dry_run,
        )
        print(action)
        if action.startswith("refusing"):
            exit_code = 1
    return exit_code


def install_target(
    *,
    root: Path,
    target: SkillInstallTarget,
    output_path: Path,
    append: bool,
    force: bool,
    dry_run: bool,
) -> str:
    """Install one target and return a stable human message."""
    relative = format_relative_path(output_path, root)
    content = template_text(target.template_name)
    if dry_run:
        verb = "append" if append else "install"
        return f"would {verb} {target.name}: {relative}"
    if output_path.exists() and not append and not force:
        return f"refusing to overwrite: {relative} (use --append or --force)"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if append and output_path.exists():
        existing = output_path.read_text(encoding="utf-8")
        output_path.write_text(
            append_section(existing, content),
            encoding="utf-8",
            newline="\n",
        )
        return f"appended {target.name}: {relative}"

    output_path.write_text(ensure_lf(content), encoding="utf-8", newline="\n")
    return f"installed {target.name}: {relative}"


def template_text(template_name: str) -> str:
    """Load one packaged QA-Z instruction template."""
    return files("qa_z.templates").joinpath(template_name).read_text(encoding="utf-8")


def append_section(existing: str, content: str) -> str:
    """Append a delimited QA-Z section to existing instructions."""
    clean_existing = existing.rstrip()
    section = "\n".join([SECTION_START, ensure_lf(content).strip(), SECTION_END])
    return f"{clean_existing}\n\n{section}\n"


def ensure_lf(content: str) -> str:
    """Normalize content to LF with one trailing newline."""
    return content.replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"


def handle_skill(args: argparse.Namespace) -> int:
    """Dispatch skill subcommands."""
    if hasattr(args, "skill_handler"):
        return int(args.skill_handler(args))
    print("qa-z skill: missing subcommand; run `qa-z skill --help`")
    return 2


def register_skill_command(subparsers: argparse._SubParsersAction) -> None:
    """Register the nested skill command."""
    skill_parser = subparsers.add_parser(
        "skill",
        help="install QA-Z agent safety instructions",
    )
    skill_subparsers = skill_parser.add_subparsers(dest="skill_command")
    install_parser = skill_subparsers.add_parser(
        "install",
        help="install QA-Z merge-safety instructions",
    )
    install_parser.add_argument(
        "target",
        choices=(*TARGETS, "all"),
        help="instruction target to install",
    )
    install_parser.add_argument(
        "--path",
        default=".",
        help="repository root where instructions should be installed",
    )
    install_parser.add_argument(
        "--append",
        action="store_true",
        help="append a delimited QA-Z section to an existing file",
    )
    install_parser.add_argument(
        "--force",
        action="store_true",
        help="overwrite an existing file",
    )
    install_parser.add_argument(
        "--output",
        help="custom output path for a single target",
    )
    install_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print intended writes without modifying files",
    )
    install_parser.set_defaults(skill_handler=handle_skill_install)
    skill_parser.set_defaults(handler=handle_skill)
