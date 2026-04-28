from __future__ import annotations

import json
from pathlib import Path

import tests.benchmark_test_support as support_module


def test_benchmark_test_support_writes_contract_config_and_fast_summary(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    support_module.write_contract(repo, related_files=["src/app.py"], title="Fixture")
    support_module.write_config(
        repo,
        [{"id": "py_test", "kind": "test", "run": ["python", "-m", "pytest"]}],
    )
    support_module.write_fast_summary(
        repo, "baseline", check_id="py_test", status="failed", exit_code=1
    )

    contract = (repo / "qa" / "contracts" / "contract.md").read_text(encoding="utf-8")
    config = json.loads((repo / "qa-z.yaml").read_text(encoding="utf-8"))
    summary = json.loads(
        (repo / ".qa-z" / "runs" / "baseline" / "fast" / "summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert "# QA Contract: Fixture" in contract
    assert config["project"]["languages"] == ["python"]
    assert summary["checks"][0]["id"] == "py_test"


def test_benchmark_test_support_writes_expected_json_and_mixed_fast_summary(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    support_module.write_expected(
        tmp_path / "fixtures" / "fixture" / "expected.json",
        {"name": "fixture", "run": {"fast": True}},
    )
    support_module.write_json(
        repo / "external-result.json",
        {"kind": "qa_z.executor_result", "status": "partial"},
    )
    support_module.write_mixed_fast_summary(
        repo,
        "candidate",
        py_status="passed",
        py_exit_code=0,
        ts_status="failed",
        ts_exit_code=1,
    )

    expected = json.loads(
        (tmp_path / "fixtures" / "fixture" / "expected.json").read_text(
            encoding="utf-8"
        )
    )
    payload = json.loads((repo / "external-result.json").read_text(encoding="utf-8"))
    summary = json.loads(
        (repo / ".qa-z" / "runs" / "candidate" / "fast" / "summary.json").read_text(
            encoding="utf-8"
        )
    )

    assert expected["name"] == "fixture"
    assert payload["kind"] == "qa_z.executor_result"
    assert [check["id"] for check in summary["checks"]] == ["py_test", "ts_type"]
    assert summary["status"] == "failed"
