from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = ROOT / "marketing" / "x" / "scripts" / "validate_x_posts.py"
DRY_RUN_PATH = ROOT / "marketing" / "x" / "scripts" / "x_post_dry_run.py"


def load_module(name: str, path: Path):
    cached = sys.modules.get(name)
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if isinstance(cached_path, str) and Path(cached_path).resolve() == path:
            return cached
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_marketing_file(root: Path, relative: str, text: str) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def test_validate_x_posts_catches_false_package_publish_claims(tmp_path: Path) -> None:
    module = load_module("validate_x_posts", VALIDATOR_PATH)
    write_marketing_file(
        tmp_path,
        "marketing/x/posts/day-00-launch.md",
        """
# Day 0

## Post

QA-Z is now published on PyPI.
Repo: https://github.com/qazedhq/qa-z
""",
    )

    result = module.validate(tmp_path / "marketing" / "x")

    assert result.errors
    assert any("package publish" in issue.message for issue in result.errors)


def test_validate_x_posts_catches_duplicate_post_bodies(tmp_path: Path) -> None:
    module = load_module("validate_x_posts", VALIDATOR_PATH)
    body = "QA-Z alpha is live: https://github.com/qazedhq/qa-z"
    write_marketing_file(
        tmp_path,
        "marketing/x/posts/day-00-launch.md",
        f"# Day 0\n\n## Post\n\n{body}\n",
    )
    write_marketing_file(
        tmp_path,
        "marketing/x/pinned-post.md",
        f"# Pinned\n\n## Concise\n\n{body}\n",
    )

    result = module.validate(tmp_path / "marketing" / "x")

    assert any("duplicate post body" in issue.message for issue in result.errors)


def test_validate_x_posts_catches_excessive_mentions(tmp_path: Path) -> None:
    module = load_module("validate_x_posts", VALIDATOR_PATH)
    write_marketing_file(
        tmp_path,
        "marketing/x/replies/ai-coding-agents.md",
        """
# Replies

## Reply

@one @two @three @four @five QA-Z might be relevant here.
""",
    )

    result = module.validate(tmp_path / "marketing" / "x")

    assert any("excessive mentions" in issue.message for issue in result.errors)


def test_validate_x_posts_allows_approved_launch_posts(tmp_path: Path) -> None:
    module = load_module("validate_x_posts", VALIDATOR_PATH)
    write_marketing_file(
        tmp_path,
        "marketing/x/posts/day-00-launch.md",
        """
# Day 0

## Goal

Launch QA-Z without package or marketplace claims.

## Post

QA-Z v0.9.9-alpha is a GitHub prerelease for making AI coding safer to merge.

Repo: https://github.com/qazedhq/qa-z
Release: https://github.com/qazedhq/qa-z/releases/tag/v0.9.9-alpha
""",
    )

    result = module.validate(tmp_path / "marketing" / "x")

    assert result.errors == []


def test_x_post_dry_run_extracts_post_blocks_without_network_calls(
    tmp_path: Path, monkeypatch
) -> None:
    module = load_module("x_post_dry_run", DRY_RUN_PATH)
    source = tmp_path / "pinned-post.md"
    source.write_text(
        """
# Pinned

## Concise

QA-Z makes AI coding safe to merge.

Repo: https://github.com/qazedhq/qa-z

## Notes

Do not post automatically.

## Demo-first

Watch QA-Z catch a risky auth change before merge.

Release: https://github.com/qazedhq/qa-z/releases/tag/v0.9.9-alpha
""",
        encoding="utf-8",
        newline="\n",
    )
    monkeypatch.setenv("QA_Z_X_POST_ENABLE", "1")
    monkeypatch.setenv("X_USER_ACCESS_TOKEN", "secret-token")

    payloads = module.extract_post_blocks(source)
    exit_code = module.main([str(source), "--post"])

    assert [payload.title for payload in payloads] == ["Concise", "Demo-first"]
    assert "secret-token" not in payloads[0].text
    assert exit_code == 2
