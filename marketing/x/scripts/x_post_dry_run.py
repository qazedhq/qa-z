from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


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


@dataclass(frozen=True)
class Payload:
    title: str
    text: str
    source_line: int


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
    title: str, section_lines: list[tuple[int, str]]
) -> list[Payload]:
    fenced_payloads: list[Payload] = []
    in_fence = False
    fence_start = 0
    current: list[str] = []

    for line_number, line in section_lines:
        if FENCE_RE.match(line.strip()):
            if in_fence:
                for text in split_thread_payloads("\n".join(current)):
                    fenced_payloads.append(Payload(title, text, fence_start))
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
        Payload(title, text, section_lines[0][0])
        for text in split_thread_payloads(plain)
    ]


def retitle_duplicates(payloads: list[Payload]) -> list[Payload]:
    if len(payloads) <= 1:
        return payloads
    return [
        Payload(f"{payload.title} {index}", payload.text, payload.source_line)
        for index, payload in enumerate(payloads, start=1)
    ]


def extract_post_blocks(path: Path) -> list[Payload]:
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
        section_start = index + 2
        index += 1
        section_lines: list[tuple[int, str]] = []

        while index < len(lines):
            next_match = HEADING_RE.match(lines[index])
            if next_match is not None and len(next_match.group(1)) <= level:
                break
            section_lines.append((index + 1, lines[index]))
            index += 1

        if section_lines:
            payloads.extend(payloads_from_section(title, section_lines))
        elif section_start <= len(lines):
            payloads.append(Payload(title, "", section_start))

    return [payload for payload in payloads if payload.text.strip()]


def render_payloads(path: Path, payloads: list[Payload]) -> str:
    chunks = [f"Dry run for {path}"]
    for index, payload in enumerate(payloads, start=1):
        chunks.extend(
            [
                "",
                f"Payload {index}: {payload.title}",
                f"Source line: {payload.source_line}",
                f"Characters: {len(payload.text)}",
                "---",
                payload.text,
            ]
        )
    return "\n".join(chunks)


def main(argv: list[str] | None = None) -> int:
    configure_console()
    parser = argparse.ArgumentParser(
        description="Print X payloads extracted from a markdown launch file."
    )
    parser.add_argument("markdown_file", type=Path)
    parser.add_argument(
        "--post",
        action="store_true",
        help="Disabled for this dry-run kit; never performs network calls.",
    )
    args = parser.parse_args(argv)

    if args.post:
        enabled = os.environ.get("QA_Z_X_POST_ENABLE") == "1"
        has_token = bool(os.environ.get("X_USER_ACCESS_TOKEN"))
        if not (enabled and has_token):
            print(
                "Refusing to post: --post requires QA_Z_X_POST_ENABLE=1 and "
                "X_USER_ACCESS_TOKEN, and this tool does not print tokens.",
                file=sys.stderr,
            )
            return 2
        print(
            "Refusing to post: this repository dry-run intentionally makes no "
            "network calls. Post manually in the X UI.",
            file=sys.stderr,
        )
        return 2

    if not args.markdown_file.exists():
        print(f"Markdown file not found: {args.markdown_file}", file=sys.stderr)
        return 1

    payloads = extract_post_blocks(args.markdown_file)
    if not payloads:
        print(
            f"No candidate post blocks found in {args.markdown_file}", file=sys.stderr
        )
        return 1

    print(render_payloads(args.markdown_file, payloads))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
