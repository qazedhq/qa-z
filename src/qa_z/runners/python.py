"""Python fast-check configuration for QA-Z."""

from __future__ import annotations

from typing import Any

from qa_z.config import get_nested
from qa_z.runners.models import CheckSpec

PYTHON_FAST_DEFAULTS: dict[str, CheckSpec] = {
    "py_lint": CheckSpec(
        id="py_lint",
        command=["ruff", "check", "."],
        kind="lint",
        timeout_seconds=60,
    ),
    "py_format": CheckSpec(
        id="py_format",
        command=["ruff", "format", "--check", "."],
        kind="format",
        timeout_seconds=60,
    ),
    "py_type": CheckSpec(
        id="py_type",
        command=["mypy", "src", "tests"],
        kind="typecheck",
        timeout_seconds=180,
    ),
    "py_test": CheckSpec(
        id="py_test",
        command=["pytest", "-q"],
        kind="test",
        no_tests="warn",
        timeout_seconds=300,
    ),
}

LEGACY_FAST_ALIASES = {
    "lint": "py_lint",
    "format": "py_format",
    "format-check": "py_format",
    "type": "py_type",
    "typecheck": "py_type",
    "unit": "py_test",
    "test": "py_test",
    "tests": "py_test",
    "py_lint": "py_lint",
    "py_format": "py_format",
    "py_type": "py_type",
    "py_test": "py_test",
}


def resolve_python_fast_checks(config: dict[str, Any]) -> list[CheckSpec]:
    """Resolve configured Python fast checks into concrete subprocess specs."""
    configured = configured_fast_checks(config)
    specs: list[CheckSpec] = []

    for item in configured:
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
    """Resolve one config item to a Python check spec."""
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
    """Return a copy of a built-in Python check spec by id or legacy alias."""
    check_id = LEGACY_FAST_ALIASES.get(name)
    if check_id is None:
        return None
    default = PYTHON_FAST_DEFAULTS[check_id]
    return CheckSpec(
        id=default.id,
        command=list(default.command),
        kind=default.kind,
        enabled=default.enabled,
        no_tests=default.no_tests,
        timeout_seconds=default.timeout_seconds,
    )


def default_kind(check_id: str) -> str:
    """Infer a check kind from a known check id."""
    default = default_spec_for_name(check_id)
    if default:
        return default.kind
    return "custom"


def coerce_timeout(value: Any) -> int | None:
    """Coerce timeout config to a positive integer."""
    if value is None:
        return None
    try:
        timeout = int(value)
    except (TypeError, ValueError):
        return None
    return timeout if timeout > 0 else None
