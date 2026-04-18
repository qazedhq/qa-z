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

    assert [(spec.id, spec.command, spec.kind, spec.no_tests) for spec in specs] == [
        ("py_lint", ["ruff", "check", "."], "lint", "warn"),
        ("ts_test", ["pnpm", "vitest", "run"], "test", "fail"),
    ]
