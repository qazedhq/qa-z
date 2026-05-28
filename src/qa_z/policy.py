"""Local merge policy pack helpers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

BUILTIN_POLICY_PACKS: dict[str, dict[str, Any]] = {
    "default": {
        "name": "default",
        "source": "builtin",
        "block_on": ["failed_unit", "failed_security", "missing_contract"],
        "require_review": ["generated_code_change", "dependency_change"],
        "severity_mapping": {
            "ERROR": "block",
            "WARNING": "review",
            "INFO": "allow",
        },
    },
    "strict": {
        "name": "strict",
        "source": "builtin",
        "block_on": [
            "auth_regression",
            "owner_check_removed",
            "secret_leak",
        ],
        "require_review": [
            "generated_code_change",
            "dependency_change",
        ],
        "severity_mapping": {
            "ERROR": "block",
            "WARNING": "review",
            "INFO": "review",
        },
    },
}


def resolve_policy_pack(
    config: dict[str, Any], requested_policy: str | None = None
) -> dict[str, Any]:
    """Resolve a builtin or configured merge policy pack."""
    if requested_policy:
        if requested_policy in BUILTIN_POLICY_PACKS:
            return deepcopy(BUILTIN_POLICY_PACKS[requested_policy])
        configured = configured_policy(config)
        if configured and configured.get("name") == requested_policy:
            return configured
        return {
            "name": requested_policy,
            "source": "missing",
            "block_on": [],
            "require_review": [],
        }

    configured = configured_policy(config)
    if configured:
        return configured
    return deepcopy(BUILTIN_POLICY_PACKS["default"])


def configured_policy(config: dict[str, Any]) -> dict[str, Any] | None:
    """Return the repo-configured merge policy, when present."""
    policy = config.get("merge_policy")
    if not isinstance(policy, dict):
        return None
    resolved = dict(policy)
    resolved.setdefault("name", "configured")
    resolved["source"] = "config"
    resolved.setdefault("require_review", [])
    resolved.setdefault("severity_mapping", {})
    return resolved


def validate_policy_pack(policy: dict[str, Any]) -> list[str]:
    """Return deterministic validation errors for a policy pack."""
    errors: list[str] = []
    name = policy.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("merge_policy.name must be a non-empty string.")
    if policy.get("source") == "missing":
        errors.append(f"unknown policy pack: {name}")

    block_on = policy.get("block_on")
    if not isinstance(block_on, list) or not block_on:
        errors.append("merge_policy.block_on must contain at least one rule id.")
    elif not all(isinstance(item, str) and item.strip() for item in block_on):
        errors.append("merge_policy.block_on entries must be non-empty strings.")

    require_review = policy.get("require_review")
    if not isinstance(require_review, list):
        errors.append("merge_policy.require_review must be a list.")
    elif not all(isinstance(item, str) and item.strip() for item in require_review):
        errors.append("merge_policy.require_review entries must be non-empty strings.")

    severity_mapping = policy.get("severity_mapping")
    if severity_mapping is not None and not isinstance(severity_mapping, dict):
        errors.append("merge_policy.severity_mapping must be a mapping.")
    return errors


def validation_payload(policy: dict[str, Any]) -> dict[str, Any]:
    """Build the stable policy validation payload."""
    errors = validate_policy_pack(policy)
    return {
        "kind": "qa_z.policy_validation",
        "schema_version": 1,
        "status": "invalid" if errors else "valid",
        "policy": public_policy(policy),
        "errors": errors,
    }


def public_policy(policy: dict[str, Any]) -> dict[str, Any]:
    """Return only stable, non-secret policy fields."""
    return {
        "name": str(policy.get("name") or ""),
        "source": str(policy.get("source") or "config"),
        "block_on": list(policy.get("block_on") or []),
        "require_review": list(policy.get("require_review") or []),
        "severity_mapping": dict(policy.get("severity_mapping") or {}),
    }
