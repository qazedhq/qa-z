"""Tests for qa-z plan title resolution and contract metadata."""

from __future__ import annotations

from textwrap import dedent

import yaml

from qa_z.artifacts import load_contract_context
from qa_z.cli import main
from qa_z.diffing.models import ChangedFile, ChangeSet
from qa_z.planner.contracts import resolve_plan_title


def test_resolve_plan_title_priority_order() -> None:
    change_set = ChangeSet(
        source="cli_diff",
        files=[
            ChangedFile(
                path="src/qa_z/cli.py",
                old_path="src/qa_z/cli.py",
                status="modified",
                additions=8,
                deletions=2,
                language="python",
                kind="source",
            )
        ],
    )

    assert resolve_plan_title("Explicit", "# Issue", "# Spec", change_set) == "Explicit"
    assert (
        resolve_plan_title(None, "# Fix token refresh regression", "# Spec", change_set)
        == "Fix token refresh regression"
    )
    assert (
        resolve_plan_title(None, None, "# CLI output stability", change_set)
        == "CLI output stability"
    )
    assert (
        resolve_plan_title(None, None, None, change_set)
        == "Contract for changes in src/qa_z/cli.py"
    )
    assert resolve_plan_title(None, None, None, None) == "QA-Z Contract"


def test_plan_without_title_uses_issue_title_and_writes_changes_front_matter(
    tmp_path, capsys
) -> None:
    (tmp_path / "qa-z.yaml").write_text(
        yaml.safe_dump(
            {
                "project": {"name": "qa-z", "languages": ["python"]},
                "contracts": {"output_dir": "qa/contracts"},
                "fast": {"checks": []},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    issue_path = tmp_path / "issue.md"
    issue_path.write_text("# Fix token refresh regression\nBody\n", encoding="utf-8")
    diff_path = tmp_path / "changes.diff"
    diff_path.write_text(
        dedent(
            """\
            diff --git a/src/qa_z/cli.py b/src/qa_z/cli.py
            index 1111111..2222222 100644
            --- a/src/qa_z/cli.py
            +++ b/src/qa_z/cli.py
            @@ -1 +1,2 @@
             old
            +new
            """
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "plan",
            "--path",
            str(tmp_path),
            "--issue",
            str(issue_path),
            "--diff",
            str(diff_path),
        ]
    )
    capsys.readouterr()
    contract_path = tmp_path / "qa" / "contracts" / "fix-token-refresh-regression.md"

    assert exit_code == 0
    contract = contract_path.read_text(encoding="utf-8")
    assert contract.startswith("---\n")
    assert "title: Fix token refresh regression\n" in contract
    assert "diff_path: changes.diff\n" in contract
    assert "path: src/qa_z/cli.py\n" in contract

    context = load_contract_context(contract_path, tmp_path)
    assert context.title == "Fix token refresh regression"
    assert context.change_set is not None
    assert context.change_set.source == "cli_diff"
    assert context.change_set.files[0].path == "src/qa_z/cli.py"
