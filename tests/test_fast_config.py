"""Tests for fast check configuration resolution."""

from __future__ import annotations

from qa_z.runners.checks import resolve_fast_checks


def test_resolve_typescript_default_fast_checks_from_ids() -> None:
    specs = resolve_fast_checks(
        {
            "project": {"languages": ["typescript"]},
            "fast": {
                "checks": [
                    "ts_lint",
                    "ts_type",
                    "ts_test",
                ]
            },
        }
    )

    assert [(spec.id, spec.command, spec.kind) for spec in specs] == [
        ("ts_lint", ["eslint", "."], "lint"),
        ("ts_type", ["tsc", "--noEmit"], "typecheck"),
        ("ts_test", ["vitest", "run"], "test"),
    ]
    assert [spec.timeout_seconds for spec in specs] == [60, 180, 300]


def test_resolve_mixed_python_and_typescript_configured_checks() -> None:
    specs = resolve_fast_checks(
        {
            "project": {"languages": ["python", "typescript"]},
            "fast": {
                "checks": [
                    "py_lint",
                    {
                        "id": "ts_test",
                        "enabled": True,
                        "run": ["pnpm", "vitest", "run"],
                        "kind": "test",
                        "no_tests": "fail",
                    },
                ]
            },
        }
    )

    assert [
        (spec.id, spec.command, spec.kind, spec.no_tests, spec.timeout_seconds)
        for spec in specs
    ] == [
        ("py_lint", ["ruff", "check", "."], "lint", "warn", 60),
        ("ts_test", ["pnpm", "vitest", "run"], "test", "fail", 300),
    ]


def test_configured_timeout_overrides_builtin_default() -> None:
    specs = resolve_fast_checks(
        {
            "project": {"languages": ["python"]},
            "fast": {
                "checks": [
                    {
                        "id": "py_test",
                        "run": ["pytest", "-q"],
                        "kind": "test",
                        "timeout_seconds": 12,
                    }
                ]
            },
        }
    )

    assert specs[0].timeout_seconds == 12
