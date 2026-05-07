"""Verify public GitHub raw URLs preserve critical files as LF multiline text."""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Sequence


CRITICAL_MIN_LF = {
    "README.md": 80,
    "pyproject.toml": 30,
    ".gitattributes": 10,
    ".editorconfig": 8,
    ".github/workflows/ci.yml": 30,
    ".github/actions/guard/action.yml": 30,
    ".github/actions/qa-z/action.yml": 30,
    "skills/qa-z-merge-safety/SKILL.md": 40,
    "scripts/check_text_file_hygiene.py": 80,
    "scripts/alpha_release_gate.py": 150,
}


@dataclass(frozen=True)
class RawUrlResult:
    """One public raw URL check result."""

    selector_kind: str
    selector: str
    path: str
    url: str
    http_status: int | None
    byte_count: int
    lf_count: int
    cr_count: int
    crlf_count: int
    passed: bool
    reason: str


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Fail when public GitHub raw URLs expose collapsed text files."
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="GitHub repository in OWNER/REPO form",
    )
    parser.add_argument(
        "--ref",
        required=True,
        help="branch or ref name to verify through raw.githubusercontent.com",
    )
    parser.add_argument(
        "--commit",
        required=True,
        help="exact commit SHA to verify through raw.githubusercontent.com",
    )
    args = parser.parse_args(argv)
    if not valid_repo(args.repo):
        parser.error("--repo must be in OWNER/REPO form")

    results = check_public_raw_urls(args.repo, args.ref, args.commit)
    for result in results:
        print_result(result)

    if all(result.passed for result in results):
        print("public raw URL hygiene passed")
        return 0
    print("public raw URL hygiene failed")
    return 1


def valid_repo(repo: str) -> bool:
    parts = repo.split("/")
    return len(parts) == 2 and all(parts)


def check_public_raw_urls(repo: str, ref: str, commit: str) -> list[RawUrlResult]:
    """Check each critical file at both the branch/ref URL and commit URL."""
    results: list[RawUrlResult] = []
    for selector_kind, selector in (("ref", ref), ("commit", commit)):
        for path, minimum_lf in CRITICAL_MIN_LF.items():
            results.append(
                check_one_url(
                    selector_kind=selector_kind,
                    selector=selector,
                    repo=repo,
                    path=path,
                    minimum_lf=minimum_lf,
                )
            )
    return results


def check_one_url(
    *,
    selector_kind: str,
    selector: str,
    repo: str,
    path: str,
    minimum_lf: int,
) -> RawUrlResult:
    """Fetch one raw URL and check its bytes."""
    url = build_raw_url(repo, selector, path)
    status, data, fetch_error = fetch_raw_url(url)
    if fetch_error is not None:
        return RawUrlResult(
            selector_kind=selector_kind,
            selector=selector,
            path=path,
            url=url,
            http_status=status,
            byte_count=0,
            lf_count=0,
            cr_count=0,
            crlf_count=0,
            passed=False,
            reason=f"fetch failed: {fetch_error}",
        )

    byte_count = len(data)
    lf_count = data.count(b"\n")
    cr_count = data.count(b"\r")
    crlf_count = data.count(b"\r\n")

    reason = raw_hygiene_failure_reason(
        http_status=status,
        byte_count=byte_count,
        lf_count=lf_count,
        cr_count=cr_count,
        crlf_count=crlf_count,
        minimum_lf=minimum_lf,
    )
    return RawUrlResult(
        selector_kind=selector_kind,
        selector=selector,
        path=path,
        url=url,
        http_status=status,
        byte_count=byte_count,
        lf_count=lf_count,
        cr_count=cr_count,
        crlf_count=crlf_count,
        passed=reason is None,
        reason=reason or "ok",
    )


def fetch_raw_url(url: str) -> tuple[int | None, bytes, str | None]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "qa-z-public-raw-hygiene"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = response_status(response)
            data = response.read() if status == 200 else b""
            return status, data, None
    except urllib.error.HTTPError as exc:
        return exc.code, b"", None
    except Exception as exc:
        return None, b"", str(exc)


def response_status(response: object) -> int:
    status = getattr(response, "status", None)
    if isinstance(status, int):
        return status
    getcode = getattr(response, "getcode", None)
    if callable(getcode):
        code = getcode()
        if isinstance(code, int):
            return code
    return 200


def raw_hygiene_failure_reason(
    *,
    http_status: int | None,
    byte_count: int,
    lf_count: int,
    cr_count: int,
    crlf_count: int,
    minimum_lf: int,
) -> str | None:
    if http_status != 200:
        return f"HTTP status is {http_status}; expected 200"
    if crlf_count:
        return "contains CRLF line endings"
    if cr_count:
        return "contains CR-only line endings"
    collapse_lf_ceiling = max(1, minimum_lf // 4)
    if byte_count >= 240 and lf_count <= collapse_lf_ceiling:
        return (
            "critical file appears collapsed: "
            f"LF count {lf_count} is below collapse ceiling {collapse_lf_ceiling}"
        )
    if lf_count < minimum_lf:
        return f"LF count {lf_count} is below threshold {minimum_lf}"
    return None


def build_raw_url(repo: str, selector: str, path: str) -> str:
    quoted_repo = "/".join(
        urllib.parse.quote(part, safe="-._~") for part in repo.split("/")
    )
    quoted_selector = urllib.parse.quote(selector, safe="/-._~")
    quoted_path = urllib.parse.quote(path, safe="/-._~")
    return f"https://raw.githubusercontent.com/{quoted_repo}/{quoted_selector}/{quoted_path}"


def print_result(result: RawUrlResult) -> None:
    outcome = "PASS" if result.passed else "FAIL"
    print(f"{outcome} {result.selector_kind} {result.path}")
    print(f"  URL: {result.url}")
    print(f"  HTTP status: {result.http_status}")
    print(f"  byte count: {result.byte_count}")
    print(f"  LF count: {result.lf_count}")
    print(f"  CR count: {result.cr_count}")
    print(f"  CRLF count: {result.crlf_count}")
    print(f"  reason: {result.reason}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
