from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]

PYTHON_RULE_PATHS = (
    Path("examples/agent-auth-bug/semgrep-rules/auth-bypass.yml"),
    Path("src/qa_z/templates/examples/agent-auth-bug/semgrep-rules/auth-bypass.yml"),
)

NESTED_REPO_RULE_PATHS = (
    Path("examples/agent-auth-bug/repo/semgrep-rules/auth-bypass.yml"),
    Path(
        "src/qa_z/templates/examples/agent-auth-bug/repo/semgrep-rules/auth-bypass.yml"
    ),
)

FASTAPI_RULE_PATH = Path("examples/fastapi-agent-bug/semgrep-rules/auth-bypass.yml")


def load_rules(relative_path: Path) -> dict[str, dict[str, Any]]:
    payload = yaml.safe_load((ROOT / relative_path).read_text(encoding="utf-8"))

    return {rule["id"]: rule for rule in payload["rules"]}


def test_auth_demo_rule_ids_stay_in_sync_between_public_and_template_files() -> None:
    expected_python_ids = {
        "qa-z.auth-bypass-any-authenticated-user",
        "qa-z.auth-bypass-missing-owner-check",
    }
    expected_nested_ids = {
        "qa-z-demo-auth-bypass",
        "qa-z-demo-missing-owner-check",
    }

    python_rule_sets = [set(load_rules(path)) for path in PYTHON_RULE_PATHS]
    nested_rule_sets = [set(load_rules(path)) for path in NESTED_REPO_RULE_PATHS]

    assert python_rule_sets == [expected_python_ids, expected_python_ids]
    assert nested_rule_sets == [expected_nested_ids, expected_nested_ids]


def test_auth_demo_owner_check_rules_explain_the_missing_identity_check() -> None:
    rule_paths = (*PYTHON_RULE_PATHS, *NESTED_REPO_RULE_PATHS, FASTAPI_RULE_PATH)

    for path in rule_paths:
        rules = load_rules(path)
        owner_rules = [
            rule
            for rule_id, rule in rules.items()
            if rule_id.endswith("missing-owner-check")
        ]

        assert len(owner_rules) == 1
        owner_rule = owner_rules[0]
        assert owner_rule["severity"] == "ERROR"
        assert owner_rule["languages"] == ["python"]
        assert "invoice" in owner_rule["message"]
        assert "owner_id" in owner_rule["message"]
        assert "patterns" in owner_rule
        assert "pattern-not" in yaml.safe_dump(owner_rule)


def test_fastapi_auth_demo_has_parallel_signed_in_and_owner_check_rules() -> None:
    rules = load_rules(FASTAPI_RULE_PATH)

    assert set(rules) == {
        "qa-z.fastapi-auth-bypass-any-signed-in-user",
        "qa-z.fastapi-auth-bypass-missing-owner-check",
    }
    assert (
        "user_id against invoice.owner_id"
        in rules["qa-z.fastapi-auth-bypass-missing-owner-check"]["message"]
    )


def test_fastapi_walkthrough_and_semgrep_docs_describe_two_finding_local_flow() -> None:
    fastapi_readme = (ROOT / "examples/fastapi-agent-bug/README.md").read_text(
        encoding="utf-8"
    )
    semgrep_docs = (ROOT / "docs/use-with-semgrep.md").read_text(encoding="utf-8")
    auth_walkthrough = (ROOT / "docs/walkthroughs/auth-bug.md").read_text(
        encoding="utf-8"
    )

    for text in (fastapi_readme, semgrep_docs, auth_walkthrough):
        assert "2 findings" in text
        assert ".qa-z/runs/baseline" in text
        assert "Do not commit" in text

    assert "examples/fastapi-agent-bug/semgrep-rules/auth-bypass.yml" in semgrep_docs
    assert "qa-z.fastapi-auth-bypass-missing-owner-check" in semgrep_docs
    assert "fail_on_severity" in semgrep_docs
    assert "ignore_rules" in semgrep_docs
    assert "exclude_paths" in semgrep_docs
