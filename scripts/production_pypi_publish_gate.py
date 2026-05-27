"""Production PyPI publish-execution gate for QA-Z."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from qa_z.subprocess_env import build_tool_subprocess_env


GO = "GO_FOR_PRODUCTION_PYPI_UPLOAD"
NO_GO_MISSING_APPROVAL = "NO_GO_MISSING_APPROVAL"
NO_GO_MISSING_CREDENTIALS = "NO_GO_MISSING_CREDENTIALS"
NO_GO_FINAL_SHA_MISMATCH = "NO_GO_FINAL_SHA_MISMATCH"
NO_GO_MISSING_FINAL_SHA_PROOF = "NO_GO_MISSING_FINAL_SHA_PROOF"
NO_GO_MISSING_LOCAL_PROOF = "NO_GO_MISSING_LOCAL_PROOF"

REQUIRED_APPROVALS = {
    "PRODUCTION_PYPI_RELEASE_APPROVED": "true",
    "PYPI_UPLOAD_ALLOWED": "true",
    "PACKAGE_PUBLISH_ALLOWED": "true",
    "TARGET_REGISTRY": "PyPI",
}

FORBIDDEN_COMMANDS = (
    "python -m twine upload dist/*",
    "python -m twine upload --repository pypi dist/*",
    "uv publish dist/*",
    "git tag",
    "gh release create",
    "deploy",
)

SAFE_NEXT_COMMANDS = (
    "python -m build --sdist --wheel",
    "python -m twine check dist/qa_z-<version>-py3-none-any.whl dist/qa_z-<version>.tar.gz",
    "python scripts/installed_package_smoke.py --json",
)


@dataclass(frozen=True)
class ProductionPyPIGateResult:
    decision: str
    package_version: str
    release_version: str | None
    current_sha: str | None
    final_sha: str | None
    local_proof: str | None
    local_proof_exists: bool
    missing_approval_flags: tuple[str, ...]
    mismatched_approval_flags: tuple[str, ...]
    credential_or_trust_proof: str

    @property
    def upload_allowed(self) -> bool:
        return self.decision == GO

    @property
    def exit_code(self) -> int:
        return 0 if self.upload_allowed else 1


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y"}


def read_package_version(repo_root: Path) -> str:
    pyproject = repo_root / "pyproject.toml"
    text = pyproject.read_text(encoding="utf-8")
    match = re.search(r'^version = "([^"]+)"$', text, flags=re.MULTILINE)
    if match is None:
        raise ValueError(f"could not read project.version from {pyproject}")
    return match.group(1)


def current_git_sha(repo_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            env=build_tool_subprocess_env(),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except OSError:
        return None
    if completed.returncode:
        return None
    return completed.stdout.strip() or None


def approval_state(
    env: Mapping[str, str],
    *,
    expected_release_version: str,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    required = dict(REQUIRED_APPROVALS)
    required["RELEASE_VERSION"] = expected_release_version
    missing: list[str] = []
    mismatched: list[str] = []
    for key, expected in required.items():
        value = env.get(key)
        if value is None or value == "":
            missing.append(key)
        elif value != expected:
            mismatched.append(key)
    return tuple(missing), tuple(mismatched)


def credential_or_trust_state(env: Mapping[str, str]) -> str:
    if _truthy(env.get("PYPI_TRUSTED_PUBLISHING_PROOF_PRESENT")):
        return "trusted_publishing"
    if _truthy(env.get("PYPI_CREDENTIAL_PROOF_PRESENT")):
        return "credential"
    return "missing"


def resolve_local_proof(
    repo_root: Path, local_proof: str | None
) -> tuple[str | None, bool]:
    if not local_proof:
        return None, False
    path = Path(local_proof)
    proof_path = path if path.is_absolute() else repo_root / path
    return local_proof, proof_path.is_file()


def decide_gate(
    *,
    missing_approval_flags: Sequence[str],
    mismatched_approval_flags: Sequence[str],
    credential_or_trust_proof: str,
    current_sha: str | None,
    final_sha: str | None,
    local_proof_exists: bool,
) -> str:
    if missing_approval_flags or mismatched_approval_flags:
        return NO_GO_MISSING_APPROVAL
    if credential_or_trust_proof == "missing":
        return NO_GO_MISSING_CREDENTIALS
    if not final_sha:
        return NO_GO_MISSING_FINAL_SHA_PROOF
    if not current_sha or current_sha != final_sha:
        return NO_GO_FINAL_SHA_MISMATCH
    if not local_proof_exists:
        return NO_GO_MISSING_LOCAL_PROOF
    return GO


def run_production_pypi_publish_gate(
    repo_root: Path,
    *,
    env: Mapping[str, str] | None = None,
    current_sha: str | None = None,
    final_sha: str | None = None,
    local_proof: str | None = None,
) -> ProductionPyPIGateResult:
    repo_root = repo_root.resolve()
    gate_env = dict(os.environ if env is None else env)
    package_version = read_package_version(repo_root)
    release_version = gate_env.get("RELEASE_VERSION")
    missing, mismatched = approval_state(
        gate_env,
        expected_release_version=package_version,
    )
    proof_state = credential_or_trust_state(gate_env)
    proof_path, proof_exists = resolve_local_proof(repo_root, local_proof)
    resolved_current_sha = current_sha or current_git_sha(repo_root)
    decision = decide_gate(
        missing_approval_flags=missing,
        mismatched_approval_flags=mismatched,
        credential_or_trust_proof=proof_state,
        current_sha=resolved_current_sha,
        final_sha=final_sha,
        local_proof_exists=proof_exists,
    )
    return ProductionPyPIGateResult(
        decision=decision,
        package_version=package_version,
        release_version=release_version,
        current_sha=resolved_current_sha,
        final_sha=final_sha,
        local_proof=proof_path,
        local_proof_exists=proof_exists,
        missing_approval_flags=missing,
        mismatched_approval_flags=mismatched,
        credential_or_trust_proof=proof_state,
    )


def result_payload(result: ProductionPyPIGateResult) -> dict[str, object]:
    return {
        "kind": "qa_z.production_pypi_publish_gate",
        "decision": result.decision,
        "exit_code": result.exit_code,
        "upload_allowed": result.upload_allowed,
        "production_pypi_upload_executed": False,
        "registry_upload_executed": False,
        "package_version": result.package_version,
        "release_version": result.release_version,
        "current_sha": result.current_sha,
        "final_sha": result.final_sha,
        "local_proof": result.local_proof,
        "local_proof_exists": result.local_proof_exists,
        "missing_approval_flags": list(result.missing_approval_flags),
        "mismatched_approval_flags": list(result.mismatched_approval_flags),
        "credential_or_trust_proof": result.credential_or_trust_proof,
        "secret_value_keys_reported": [],
        "safe_next_commands": list(SAFE_NEXT_COMMANDS),
        "forbidden_commands": list(FORBIDDEN_COMMANDS),
        "next_actions": next_actions(result),
    }


def next_actions(result: ProductionPyPIGateResult) -> list[str]:
    if result.upload_allowed:
        return [
            "Run the protected production PyPI publish workflow or upload packet under release-owner control.",
            "Capture production PyPI URL/version proof plus pip, pipx, and uv install smoke before changing README install claims.",
        ]
    if result.decision == NO_GO_MISSING_APPROVAL:
        return [
            "Record release-owner approval flags before any production PyPI upload packet.",
            "Keep README on the GitHub source install path until production PyPI proof exists.",
        ]
    if result.decision == NO_GO_MISSING_CREDENTIALS:
        return [
            "Record PyPI Trusted Publishing proof or an out-of-band credential proof without printing secret values.",
        ]
    if result.decision in {NO_GO_MISSING_FINAL_SHA_PROOF, NO_GO_FINAL_SHA_MISMATCH}:
        return [
            "Freeze and record the exact release SHA, then rerun this gate against that SHA.",
        ]
    return [
        "Refresh local build, twine check, and installed-package smoke proof before rerunning this gate.",
    ]


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Classify the production PyPI publish-execution gate without uploading."
    )
    parser.add_argument(
        "--final-sha",
        help="Approved final release SHA that must match the current HEAD.",
    )
    parser.add_argument(
        "--current-sha",
        help="Override current SHA for deterministic tests or recorded proof replay.",
    )
    parser.add_argument(
        "--local-proof",
        help="Path to refreshed build/twine/install-smoke proof.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable gate evidence.",
    )
    return parser.parse_args(argv)


def _print_human(payload: Mapping[str, object]) -> None:
    print(f"Decision: {payload['decision']}")
    print(f"Upload allowed: {payload['upload_allowed']}")
    print(
        f"Production PyPI upload executed: {payload['production_pypi_upload_executed']}"
    )
    next_actions_payload = payload.get("next_actions")
    if isinstance(next_actions_payload, list) and next_actions_payload:
        print("Next actions:")
        for index, action in enumerate(next_actions_payload, start=1):
            print(f"{index}. {action}")


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    result = run_production_pypi_publish_gate(
        Path.cwd(),
        current_sha=args.current_sha,
        final_sha=args.final_sha,
        local_proof=args.local_proof,
    )
    payload = result_payload(result)
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        _print_human(payload)
    return result.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
