from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path


GITHUB_URL = "https://github.com/qazedhq/qa-z"
CONSERVATIVE_X_LIMIT = 260
MENTION_LIMIT = 3
MENTION_RE = re.compile(r"(?<![\w/])@[A-Za-z0-9_]{1,15}\b")
NEGATION_MARKERS = (
    "avoid",
    "do not",
    "don't",
    "future",
    "has not",
    "not ",
    "not yet",
    "no ",
    "never",
    "should not",
    "what not to claim",
    "without",
)
PACKAGE_CONTEXT = ("pypi", "testpypi", "package registry")
PACKAGE_CLAIM_WORDS = (
    "available",
    "install from",
    "live",
    "published",
    "released",
    "shipping on",
)
MARKETPLACE_CONTEXT = ("github marketplace", "marketplace action")


@dataclass(frozen=True)
class Issue:
    path: str
    line: int
    severity: str
    message: str
    excerpt: str


@dataclass(frozen=True)
class Payload:
    path: Path
    title: str
    text: str
    source_line: int


@dataclass(frozen=True)
class ValidationResult:
    errors: list[Issue]
    warnings: list[Issue]

    @property
    def ok(self) -> bool:
        return not self.errors


HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*$")
FENCE_RE = re.compile(r"^```")
CANDIDATE_HEADINGS = {
    "concise",
    "demo-first",
    "demo first",
    "long thread",
    "optional thread",
    "post",
    "reply",
    "short version",
    "thread",
    "thread starter",
}


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except AttributeError:
            pass


def normalize_heading(title: str) -> str:
    return re.sub(r"[^a-z0-9 -]+", "", title.lower()).strip()


def is_candidate_heading(title: str) -> bool:
    key = normalize_heading(title)
    return key in CANDIDATE_HEADINGS or key.startswith(("post ", "reply "))


def split_thread_payloads(text: str) -> list[str]:
    numbered_parts = [
        part.strip()
        for part in re.split(r"\n\s*\n(?=\d+/)", text.strip())
        if part.strip()
    ]
    if len(numbered_parts) > 1 and all(
        re.match(r"^\d+/", part) for part in numbered_parts
    ):
        return numbered_parts

    parts = [
        part.strip() for part in re.split(r"\n\s*\n", text.strip()) if part.strip()
    ]
    if len(parts) > 1 and all(re.match(r"^\d+/", part) for part in parts):
        return parts
    return [text.strip()] if text.strip() else []


def payloads_from_section(
    path: Path, title: str, section_lines: list[tuple[int, str]]
) -> list[Payload]:
    fenced_payloads: list[Payload] = []
    in_fence = False
    fence_start = 0
    current: list[str] = []

    for line_number, line in section_lines:
        if FENCE_RE.match(line.strip()):
            if in_fence:
                for text in split_thread_payloads("\n".join(current)):
                    fenced_payloads.append(Payload(path, title, text, fence_start))
                current = []
                in_fence = False
            else:
                in_fence = True
                fence_start = line_number + 1
            continue
        if in_fence:
            current.append(line)

    if fenced_payloads:
        return retitle_duplicates(fenced_payloads)

    plain = "\n".join(line for _, line in section_lines).strip()
    plain = re.sub(r"\n{3,}", "\n\n", plain)
    return [
        Payload(path, title, text, section_lines[0][0])
        for text in split_thread_payloads(plain)
    ]


def retitle_duplicates(payloads: list[Payload]) -> list[Payload]:
    if len(payloads) <= 1:
        return payloads
    return [
        Payload(
            payload.path, f"{payload.title} {index}", payload.text, payload.source_line
        )
        for index, payload in enumerate(payloads, start=1)
    ]


def extract_payloads(path: Path) -> list[Payload]:
    lines = path.read_text(encoding="utf-8").splitlines()
    payloads: list[Payload] = []
    index = 0

    while index < len(lines):
        match = HEADING_RE.match(lines[index])
        if match is None or not is_candidate_heading(match.group(2)):
            index += 1
            continue

        level = len(match.group(1))
        title = match.group(2).strip()
        index += 1
        section_lines: list[tuple[int, str]] = []

        while index < len(lines):
            next_match = HEADING_RE.match(lines[index])
            if next_match is not None and len(next_match.group(1)) <= level:
                break
            section_lines.append((index + 1, lines[index]))
            index += 1

        if section_lines:
            payloads.extend(payloads_from_section(path, title, section_lines))

    return [payload for payload in payloads if payload.text.strip()]


def scanned_files(root: Path) -> list[Path]:
    files = [root / "pinned-post.md", root / "launch-thread.md"]
    for folder in ("posts", "replies"):
        files.extend(sorted((root / folder).glob("*.md")))
    return [path for path in files if path.exists()]


def rel(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_negated(line: str) -> bool:
    lowered = line.lower()
    return any(marker in lowered for marker in NEGATION_MARKERS)


def add_issue(
    issues: list[Issue],
    root: Path,
    path: Path,
    line: int,
    severity: str,
    message: str,
    excerpt: str,
) -> None:
    issues.append(Issue(rel(path, root), line, severity, message, excerpt.strip()))


def check_claims(root: Path, path: Path, text: str, errors: list[Issue]) -> None:
    for line_number, line in enumerate(text.splitlines(), start=1):
        lowered = line.lower()
        if is_negated(lowered):
            continue

        has_package_context = any(context in lowered for context in PACKAGE_CONTEXT)
        has_package_claim = any(word in lowered for word in PACKAGE_CLAIM_WORDS)
        if has_package_context and has_package_claim:
            add_issue(
                errors,
                root,
                path,
                line_number,
                "error",
                "fake package publish claim",
                line,
            )

        if re.search(r"\bpipx\s+install\s+qa-z\b", lowered) and not (
            "future" in lowered or "pypi" in lowered
        ):
            add_issue(
                errors,
                root,
                path,
                line_number,
                "error",
                "pipx install qa-z is not allowed unless clearly future/PyPI marked",
                line,
            )

        has_marketplace_context = any(
            context in lowered for context in MARKETPLACE_CONTEXT
        )
        has_marketplace_claim = has_marketplace_context and any(
            word in lowered for word in ("available", "official", "published")
        )
        if has_marketplace_claim:
            add_issue(
                errors,
                root,
                path,
                line_number,
                "error",
                "GitHub Marketplace or official marketplace action claim",
                line,
            )


def check_payloads(
    root: Path,
    payloads: list[Payload],
    errors: list[Issue],
    warnings: list[Issue],
) -> None:
    seen: dict[str, Payload] = {}
    for payload in payloads:
        mentions = MENTION_RE.findall(payload.text)
        if len(mentions) > MENTION_LIMIT:
            add_issue(
                errors,
                root,
                payload.path,
                payload.source_line,
                "error",
                "excessive mentions in one candidate post",
                payload.text,
            )

        if len(payload.text) > CONSERVATIVE_X_LIMIT:
            add_issue(
                warnings,
                root,
                payload.path,
                payload.source_line,
                "warning",
                f"candidate post is over {CONSERVATIVE_X_LIMIT} characters",
                payload.text,
            )

        normalized = re.sub(r"\s+", " ", payload.text.strip().lower())
        if len(normalized) < 25:
            continue
        previous = seen.get(normalized)
        if previous is not None:
            add_issue(
                errors,
                root,
                payload.path,
                payload.source_line,
                "error",
                f"duplicate post body also appears in {rel(previous.path, root)}",
                payload.text,
            )
        else:
            seen[normalized] = payload


def validate(root: Path | None = None) -> ValidationResult:
    root = (root or Path(__file__).resolve().parents[1]).resolve()
    errors: list[Issue] = []
    warnings: list[Issue] = []
    payloads: list[Payload] = []

    for path in scanned_files(root):
        text = path.read_text(encoding="utf-8")
        check_claims(root, path, text, errors)
        payloads.extend(extract_payloads(path))

        if path.parent.name == "posts" and GITHUB_URL not in text:
            add_issue(
                errors,
                root,
                path,
                1,
                "error",
                "launch post file is missing the QA-Z GitHub link",
                path.name,
            )

    check_payloads(root, payloads, errors, warnings)
    return ValidationResult(errors=errors, warnings=warnings)


def print_issues(issues: list[Issue]) -> None:
    for issue in issues:
        print(
            f"{issue.severity.upper()}: {issue.path}:{issue.line}: "
            f"{issue.message}\n  {issue.excerpt}"
        )


def main(argv: list[str] | None = None) -> int:
    configure_console()
    parser = argparse.ArgumentParser(
        description="Validate QA-Z X launch markdown for safe manual posting."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Path to marketing/x.",
    )
    args = parser.parse_args(argv)

    result = validate(args.root)
    print_issues(result.errors)
    print_issues(result.warnings)
    if result.ok:
        print("X launch post validation passed.")
        return 0
    print("X launch post validation failed.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
