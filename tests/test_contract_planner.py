"""Tests for contract planner check extraction."""

from __future__ import annotations

from qa_z.planner.contracts import collect_checks


def test_collect_checks_reads_deep_checks_config() -> None:
    fast, deep = collect_checks(
        {
            "fast": {"checks": [{"id": "py_test", "enabled": True}]},
            "deep": {"checks": [{"id": "sg_scan", "enabled": True}]},
        }
    )

    assert fast == ["py_test"]
    assert deep == ["sg_scan"]


def test_collect_checks_prefers_deep_checks_over_legacy_checks_deep() -> None:
    _fast, deep = collect_checks(
        {
            "deep": {"checks": [{"id": "sg_scan"}]},
            "checks": {"deep": ["legacy_security"]},
        }
    )

    assert deep == ["sg_scan"]


def test_collect_checks_ignores_disabled_deep_checks() -> None:
    _fast, deep = collect_checks(
        {
            "deep": {
                "checks": [
                    {"id": "sg_scan", "enabled": False},
                    {"id": "custom_deep", "enabled": True},
                ]
            }
        }
    )

    assert deep == ["custom_deep"]
