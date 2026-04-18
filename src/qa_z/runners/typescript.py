"""TypeScript fast-check configuration for QA-Z."""

from __future__ import annotations

from qa_z.runners.models import CheckSpec

TYPESCRIPT_FAST_DEFAULTS: dict[str, CheckSpec] = {
    "ts_lint": CheckSpec(
        id="ts_lint",
        command=["eslint", "."],
        kind="lint",
    ),
    "ts_type": CheckSpec(
        id="ts_type",
        command=["tsc", "--noEmit"],
        kind="typecheck",
    ),
    "ts_test": CheckSpec(
        id="ts_test",
        command=["vitest", "run"],
        kind="test",
        no_tests="warn",
    ),
}

TYPESCRIPT_FAST_ALIASES = {
    "ts_lint": "ts_lint",
    "typescript_lint": "ts_lint",
    "ts_type": "ts_type",
    "typescript_type": "ts_type",
    "typescript_typecheck": "ts_type",
    "ts_test": "ts_test",
    "typescript_test": "ts_test",
}


def default_spec_for_name(name: str) -> CheckSpec | None:
    """Return a copy of a built-in TypeScript check spec by id or alias."""
    check_id = TYPESCRIPT_FAST_ALIASES.get(name)
    if check_id is None:
        return None
    default = TYPESCRIPT_FAST_DEFAULTS[check_id]
    return CheckSpec(
        id=default.id,
        command=list(default.command),
        kind=default.kind,
        enabled=default.enabled,
        no_tests=default.no_tests,
        timeout_seconds=default.timeout_seconds,
    )
