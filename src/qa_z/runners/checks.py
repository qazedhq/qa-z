"""Fast-check configuration resolution for supported languages."""

from __future__ import annotations

from typing import Any

from qa_z.config import get_nested
from qa_z.runners.models import CheckSpec
from qa_z.runners.python import default_spec_for_name as default_python_spec_for_name
from qa_z.runners.python import coerce_timeout
from qa_z.runners.typescript import (
    default_spec_for_name as default_typescript_spec_for_name,
)


def resolve_fast_checks(config: dict[str, Any]) -> list[CheckSpec]:
    """Resolve configured fast checks into concrete subprocess specs."""
    specs: list[CheckSpec] = []
    for item in configured_fast_checks(config):
        spec = resolve_check_item(item)
        if spec is not None and spec.enabled:
            specs.append(spec)
    return specs


def configured_fast_checks(config: dict[str, Any]) -> list[Any]:
    """Return explicit fast checks, falling back to bootstrap legacy config."""
    fast_config = config.get("fast")
    if isinstance(fast_config, dict) and "checks" in fast_config:
        checks = fast_config.get("checks") or []
        return checks if isinstance(checks, list) else []

    legacy = get_nested(config, "checks", "fast", default=[]) or []
    return legacy if isinstance(legacy, list) else []


def resolve_check_item(item: Any) -> CheckSpec | None:
    """Resolve one config item to a built-in or custom check spec."""
    if isinstance(item, str):
        return default_spec_for_name(item)
    if not isinstance(item, dict):
        return None

    check_id = str(item.get("id", "")).strip()
    if not check_id:
        return None

    default = default_spec_for_name(check_id)
    command = item.get("run")
    if command is None:
        command = default.command if default else None
    if not isinstance(command, list) or not all(
        isinstance(part, str) for part in command
    ):
        return None

    return CheckSpec(
        id=check_id,
        command=list(command),
        kind=str(item.get("kind", default.kind if default else default_kind(check_id))),
        enabled=bool(item.get("enabled", True)),
        no_tests=str(item.get("no_tests", default.no_tests if default else "warn")),
        timeout_seconds=(
            coerce_timeout(item.get("timeout_seconds"))
            if "timeout_seconds" in item
            else (default.timeout_seconds if default else None)
        ),
    )


def default_spec_for_name(name: str) -> CheckSpec | None:
    """Return a copy of a built-in check spec by id or alias."""
    return default_python_spec_for_name(name) or default_typescript_spec_for_name(name)


def default_kind(check_id: str) -> str:
    """Infer a check kind from a known check id."""
    default = default_spec_for_name(check_id)
    if default:
        return default.kind
    return "custom"
