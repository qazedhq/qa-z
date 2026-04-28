from __future__ import annotations

import qa_z.verification_finding_matching as matching_module
from qa_z.verification_models import VerificationFinding


def _finding(
    *,
    source: str = "sg_scan",
    rule_id: str = "rule.one",
    severity: str = "ERROR",
    path: str = "src/app.py",
    line: int | None = 10,
    message: str = "Blocker",
    blocking: bool = True,
) -> VerificationFinding:
    return VerificationFinding(
        source=source,
        rule_id=rule_id,
        severity=severity,
        path=path,
        line=line,
        message=message,
        blocking=blocking,
    )


def test_compare_extracted_findings_marks_resolved_and_new_findings() -> None:
    categories = matching_module.compare_extracted_findings(
        baseline_findings=[_finding()],
        candidate_findings=[
            _finding(rule_id="rule.one", blocking=False, severity="WARNING"),
            _finding(rule_id="rule.two", path="src/new.py", line=7, blocking=True),
        ],
    )

    assert [delta.id for delta in categories["resolved"]] == [
        "sg_scan:rule.one:src/app.py:10"
    ]
    assert [delta.id for delta in categories["newly_introduced"]] == [
        "sg_scan:rule.two:src/new.py:7"
    ]
