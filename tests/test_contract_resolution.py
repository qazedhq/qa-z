"""Tests for latest QA contract discovery."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from qa_z.artifacts import ArtifactSourceNotFound, find_latest_contract


def contract_config() -> dict[str, object]:
    return {"contracts": {"output_dir": "qa/contracts"}}


def write_contracts_readme(root: Path) -> Path:
    contracts_dir = root / "qa" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    path = contracts_dir / "README.md"
    path.write_text("# QA Contracts\n\nGenerated contracts live here.\n", "utf-8")
    return path


def test_find_latest_contract_ignores_contracts_readme(tmp_path: Path) -> None:
    write_contracts_readme(tmp_path)

    with pytest.raises(ArtifactSourceNotFound, match="No QA contract files found"):
        find_latest_contract(tmp_path, contract_config())


def test_find_latest_contract_selects_valid_contract_not_newer_readme(
    tmp_path: Path,
) -> None:
    readme = write_contracts_readme(tmp_path)
    contract = tmp_path / "qa" / "contracts" / "feature.md"
    contract.write_text("# QA Contract: Feature\n\n## Scope\n\n- one\n", "utf-8")
    os.utime(contract, (1, 1))
    os.utime(readme, (2, 2))

    assert find_latest_contract(tmp_path, contract_config()) == contract


def test_find_latest_contract_ignores_generic_markdown(tmp_path: Path) -> None:
    contracts_dir = tmp_path / "qa" / "contracts"
    contracts_dir.mkdir(parents=True, exist_ok=True)
    (contracts_dir / "notes.md").write_text("# Notes\n\nNot a QA contract.\n", "utf-8")

    with pytest.raises(ArtifactSourceNotFound, match="No QA contract files found"):
        find_latest_contract(tmp_path, contract_config())
