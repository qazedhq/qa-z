"""Shared loaders for QA-Z run and contract artifacts."""

from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from qa_z.config import get_nested
from qa_z.runners.models import RunSummary


@dataclass(frozen=True)
class RunSource:
    """Resolved locations for one fast run artifact set."""

    run_dir: Path
    fast_dir: Path
    summary_path: Path


@dataclass
class ContractContext:
    """Best-effort structured context loaded from a QA contract."""

    path: str | None
    title: str | None
    summary: str | None
    scope_items: list[str]
    acceptance_checks: list[str]
    assumptions: list[str]
    constraints: list[str]
    raw_markdown: str


class ArtifactSourceNotFound(FileNotFoundError):
    """Raised when a run or contract source cannot be found."""


class ArtifactLoadError(ValueError):
    """Raised when an artifact exists but cannot be parsed."""


def contract_output_dir(root: Path, config: dict[str, Any]) -> Path:
    """Resolve the configured contract directory."""
    output_dir = Path(
        str(get_nested(config, "contracts", "output_dir", default="qa/contracts"))
    )
    if not output_dir.is_absolute():
        output_dir = root / output_dir
    return output_dir


def find_latest_contract(root: Path, config: dict[str, Any]) -> Path:
    """Find the newest contract in the configured output directory."""
    output_dir = contract_output_dir(root, config)
    candidates = sorted(
        output_dir.glob("*.md"), key=lambda path: path.stat().st_mtime, reverse=True
    )
    if not candidates:
        raise ArtifactSourceNotFound(f"No contract files found in {output_dir}")
    return candidates[0]


def resolve_run_source(
    root: Path, config: dict[str, Any], from_run: str | None = None
) -> RunSource:
    """Resolve latest, run root, fast directory, or summary file to a run source."""
    if from_run in (None, "", "latest"):
        return resolve_latest_run_source(root, config)

    candidate = Path(str(from_run)).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    candidate = candidate.resolve()

    if candidate.is_file():
        if candidate.name != "summary.json" or candidate.parent.name != "fast":
            raise ArtifactSourceNotFound(f"Unsupported run summary path: {candidate}")
        return RunSource(
            run_dir=candidate.parent.parent,
            fast_dir=candidate.parent,
            summary_path=candidate,
        )

    if (candidate / "summary.json").is_file():
        return RunSource(
            run_dir=candidate.parent,
            fast_dir=candidate,
            summary_path=candidate / "summary.json",
        )

    summary_path = candidate / "fast" / "summary.json"
    if summary_path.is_file():
        return RunSource(
            run_dir=candidate,
            fast_dir=candidate / "fast",
            summary_path=summary_path,
        )

    raise ArtifactSourceNotFound(f"No fast summary artifact found for {candidate}")


def resolve_latest_run_source(root: Path, config: dict[str, Any]) -> RunSource:
    """Resolve the latest run containing fast/summary.json."""
    runs_dir = Path(str(get_nested(config, "fast", "output_dir", default=".qa-z/runs")))
    if not runs_dir.is_absolute():
        runs_dir = root / runs_dir
    if not runs_dir.exists():
        raise ArtifactSourceNotFound(f"No run directory found at {runs_dir}")

    summaries = list(runs_dir.glob("*/fast/summary.json"))
    if not summaries:
        raise ArtifactSourceNotFound(f"No fast summary artifacts found in {runs_dir}")

    summary_path = max(
        summaries,
        key=lambda path: (path.stat().st_mtime, path.parent.parent.name),
    )
    return RunSource(
        run_dir=summary_path.parent.parent,
        fast_dir=summary_path.parent,
        summary_path=summary_path,
    )


def load_run_summary(summary_path: Path) -> RunSummary:
    """Load a run summary JSON artifact."""
    try:
        data = json.loads(summary_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactLoadError(f"Could not read run summary: {summary_path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(
            f"Run summary is not valid JSON: {summary_path}"
        ) from exc

    if not isinstance(data, dict):
        raise ArtifactLoadError("Run summary JSON must contain an object.")
    try:
        return RunSummary.from_dict(data)
    except (TypeError, ValueError) as exc:
        raise ArtifactLoadError(str(exc)) from exc


def resolve_contract_source(
    root: Path,
    config: dict[str, Any],
    summary: RunSummary | None = None,
    explicit_contract: str | None = None,
) -> Path:
    """Resolve a contract path using CLI override, run summary, then latest contract."""
    if explicit_contract:
        explicit_path = resolve_path(root, explicit_contract)
        if not explicit_path.is_file():
            raise ArtifactSourceNotFound(f"Contract not found: {explicit_path}")
        return explicit_path

    if summary and summary.contract_path:
        summary_path = resolve_path(root, summary.contract_path)
        if summary_path.is_file():
            return summary_path

    try:
        return find_latest_contract(root, config)
    except FileNotFoundError as exc:
        raise ArtifactSourceNotFound(str(exc)) from exc


def load_contract_context(contract_path: Path, root: Path) -> ContractContext:
    """Load contract markdown with optional YAML front matter metadata."""
    try:
        raw_markdown = contract_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ArtifactSourceNotFound(f"Contract not found: {contract_path}") from exc

    relative_path = format_path(contract_path, root)
    metadata, markdown_body = split_front_matter(raw_markdown)

    title = first_metadata_string(metadata, "title")
    summary = first_metadata_string(metadata, "summary")
    scope_items = metadata_list(metadata, "scope")
    acceptance_checks = metadata_list(metadata, "acceptance_checks")
    assumptions = metadata_list(metadata, "assumptions")
    constraints = metadata_list(metadata, "constraints")

    if not title:
        title = extract_title(markdown_body)
    if not summary:
        summary = extract_summary(markdown_body)
    if not scope_items:
        scope_items = extract_bullets(extract_section(markdown_body, "Scope"))
    if not acceptance_checks:
        acceptance_checks = extract_bullets(
            extract_section(markdown_body, "Acceptance Checks")
        )
    if not assumptions:
        assumptions = extract_bullets(extract_section(markdown_body, "Assumptions"))
    if not constraints:
        constraints = extract_bullets(extract_section(markdown_body, "Constraints"))

    return ContractContext(
        path=relative_path,
        title=title,
        summary=summary,
        scope_items=scope_items,
        acceptance_checks=acceptance_checks,
        assumptions=assumptions,
        constraints=constraints,
        raw_markdown=raw_markdown,
    )


def split_front_matter(raw_markdown: str) -> tuple[dict[str, Any], str]:
    """Return YAML front matter metadata and the markdown body, best effort."""
    if not raw_markdown.startswith("---"):
        return {}, raw_markdown

    match = re.match(r"\A---\s*\n(?P<yaml>.*?\n)---\s*\n?", raw_markdown, re.DOTALL)
    if not match:
        return {}, raw_markdown

    try:
        loaded = yaml.safe_load(match.group("yaml")) or {}
    except yaml.YAMLError:
        return {}, raw_markdown
    if not isinstance(loaded, dict):
        return {}, raw_markdown
    return loaded, raw_markdown[match.end() :]


def first_metadata_string(metadata: dict[str, Any], key: str) -> str | None:
    """Return a non-empty front matter string value."""
    value = metadata.get(key)
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


def metadata_list(metadata: dict[str, Any], key: str) -> list[str]:
    """Return a normalized front matter list."""
    value = metadata.get(key)
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def extract_title(document: str) -> str | None:
    """Extract a contract title from the first H1."""
    for line in document.splitlines():
        match = re.match(r"#\s+(?:QA Contract:\s*)?(?P<title>.+)", line.strip())
        if match:
            return match.group("title").strip()
    return None


def extract_summary(document: str) -> str | None:
    """Extract the first paragraph from the Contract Summary section."""
    section = extract_section(document, "Contract Summary")
    for block in re.split(r"\n\s*\n", section):
        cleaned = normalize_markdown_text(block)
        if cleaned:
            return cleaned
    return None


def extract_section(document: str, heading: str) -> str:
    """Extract a markdown section body by H2 heading."""
    pattern = rf"^## {re.escape(heading)}\n(?P<body>.*?)(?=^## |\Z)"
    match = re.search(pattern, document, flags=re.MULTILINE | re.DOTALL)
    if not match:
        return ""
    return match.group("body").strip()


def extract_bullets(section: str) -> list[str]:
    """Extract bullet items from a markdown section."""
    items: list[str] = []
    for line in section.splitlines():
        stripped = line.strip()
        if stripped.startswith(("- ", "* ")):
            items.append(stripped[2:].strip())
    return items


def normalize_markdown_text(text: str) -> str:
    """Collapse simple markdown text into one readable line."""
    lines = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("- ", "* ")):
            continue
        lines.append(stripped)
    return " ".join(lines).strip() or ""


def extract_contract_candidate_files(contract: ContractContext) -> list[str]:
    """Extract candidate files from contract related-file sections."""
    section_names = (
        "Related Files",
        "Changed Files",
        "Candidate Files",
        "Files",
    )
    text_parts = [
        extract_section(contract.raw_markdown, name) for name in section_names
    ]
    return extract_candidate_files("\n".join(text_parts))


def extract_candidate_files(text: str) -> list[str]:
    """Extract conservative source/test file candidates from text."""
    pattern = re.compile(
        r"(?P<path>(?:src|tests|app|apps|lib|packages|scripts|qa|docs|examples|"
        r"benchmark|templates)[A-Za-z0-9_./\\-]*\.(?:tsx|jsx|py|ts|js))"
    )
    counts: Counter[str] = Counter()
    first_seen: dict[str, int] = {}
    for index, match in enumerate(pattern.finditer(text)):
        path = match.group("path").replace("\\", "/").rstrip(".,:;)]}'\"")
        counts[path] += 1
        first_seen.setdefault(path, index)
    return [
        path
        for path, _count in sorted(
            counts.items(), key=lambda item: (-item[1], first_seen[item[0]], item[0])
        )
    ]


def format_path(path: Path, root: Path) -> str:
    """Format a path relative to the project root when possible."""
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(path)


def resolve_path(root: Path, value: str) -> Path:
    """Resolve a path relative to root when needed."""
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = root / path
    return path.resolve()
