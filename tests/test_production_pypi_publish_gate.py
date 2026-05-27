from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = ROOT / "scripts" / "production_pypi_publish_gate.py"


def load_gate_module():
    cached = sys.modules.get("production_pypi_publish_gate")
    if cached is not None:
        cached_path = getattr(cached, "__file__", None)
        if (
            isinstance(cached_path, str)
            and Path(cached_path).resolve() == SCRIPT_PATH.resolve()
        ):
            return cached
    spec = importlib.util.spec_from_file_location(
        "production_pypi_publish_gate", SCRIPT_PATH
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_pyproject(tmp_path: Path, version: str = "0.10.0b0") -> None:
    (tmp_path / "pyproject.toml").write_text(
        f'[project]\nname = "qa-z"\nversion = "{version}"\n',
        encoding="utf-8",
    )


def approval_env(**overrides: str) -> dict[str, str]:
    env = {
        "PRODUCTION_PYPI_RELEASE_APPROVED": "true",
        "PYPI_UPLOAD_ALLOWED": "true",
        "PACKAGE_PUBLISH_ALLOWED": "true",
        "TARGET_REGISTRY": "PyPI",
        "RELEASE_VERSION": "0.10.0b0",
        "PYPI_TRUSTED_PUBLISHING_PROOF_PRESENT": "true",
    }
    env.update(overrides)
    return env


def test_missing_approval_flags_block_production_upload(tmp_path: Path) -> None:
    module = load_gate_module()
    write_pyproject(tmp_path)

    result = module.run_production_pypi_publish_gate(
        tmp_path,
        env={},
        current_sha="425476382830baf35678b7daf876f285c590ad46",
        final_sha="425476382830baf35678b7daf876f285c590ad46",
        local_proof="docs/reports/v0.18-production-pypi-go-no-go.md",
    )
    payload = module.result_payload(result)

    assert payload["decision"] == "NO_GO_MISSING_APPROVAL"
    assert payload["upload_allowed"] is False
    assert payload["production_pypi_upload_executed"] is False
    assert payload["registry_upload_executed"] is False
    assert payload["exit_code"] == 1
    assert "PRODUCTION_PYPI_RELEASE_APPROVED" in payload["missing_approval_flags"]
    assert "PACKAGE_PUBLISH_ALLOWED" in payload["missing_approval_flags"]
    assert "twine upload" in "\n".join(payload["forbidden_commands"])


def test_missing_trusted_publishing_or_credential_proof_blocks_after_approval(
    tmp_path: Path,
) -> None:
    module = load_gate_module()
    write_pyproject(tmp_path)
    env = approval_env(PYPI_TRUSTED_PUBLISHING_PROOF_PRESENT="false")

    result = module.run_production_pypi_publish_gate(
        tmp_path,
        env=env,
        current_sha="425476382830baf35678b7daf876f285c590ad46",
        final_sha="425476382830baf35678b7daf876f285c590ad46",
        local_proof="docs/reports/v0.18-production-pypi-go-no-go.md",
    )
    payload = module.result_payload(result)

    assert payload["decision"] == "NO_GO_MISSING_CREDENTIALS"
    assert payload["upload_allowed"] is False
    assert payload["credential_or_trust_proof"] == "missing"
    assert payload["secret_value_keys_reported"] == []


def test_final_sha_must_match_current_head(tmp_path: Path) -> None:
    module = load_gate_module()
    write_pyproject(tmp_path)

    result = module.run_production_pypi_publish_gate(
        tmp_path,
        env=approval_env(),
        current_sha="425476382830baf35678b7daf876f285c590ad46",
        final_sha="573b4b29a984a170390c738ef302e2da55592163",
        local_proof="docs/reports/v0.18-production-pypi-go-no-go.md",
    )
    payload = module.result_payload(result)

    assert payload["decision"] == "NO_GO_FINAL_SHA_MISMATCH"
    assert payload["upload_allowed"] is False
    assert payload["current_sha"] == "425476382830baf35678b7daf876f285c590ad46"
    assert payload["final_sha"] == "573b4b29a984a170390c738ef302e2da55592163"


def test_all_required_gate_evidence_allows_upload_decision_without_uploading(
    tmp_path: Path,
) -> None:
    module = load_gate_module()
    write_pyproject(tmp_path)
    proof = tmp_path / "docs" / "reports" / "v0.20-proof.md"
    proof.parent.mkdir(parents=True)
    proof.write_text(
        "local build, twine check, and install smoke proof\n", encoding="utf-8"
    )

    result = module.run_production_pypi_publish_gate(
        tmp_path,
        env=approval_env(),
        current_sha="425476382830baf35678b7daf876f285c590ad46",
        final_sha="425476382830baf35678b7daf876f285c590ad46",
        local_proof=str(proof.relative_to(tmp_path)),
    )
    payload = module.result_payload(result)

    assert payload["decision"] == "GO_FOR_PRODUCTION_PYPI_UPLOAD"
    assert payload["upload_allowed"] is True
    assert payload["production_pypi_upload_executed"] is False
    assert payload["registry_upload_executed"] is False
    assert payload["exit_code"] == 0
    assert "python -m twine upload dist/*" in payload["forbidden_commands"]
    assert payload["next_actions"][0].startswith("Run the protected production")
