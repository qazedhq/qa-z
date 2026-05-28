"""Local team governance artifacts for QA-Z."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from qa_z.artifacts import format_path

BASELINE_PATH = ".qa-z/governance/baseline.json"
WAIVERS_PATH = ".qa-z/governance/waivers.json"


def utc_now() -> str:
    """Return a compact UTC timestamp for governance artifacts."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def create_baseline(root: Path) -> dict[str, Any]:
    """Create the local governance baseline artifact."""
    root = root.expanduser().resolve()
    payload: dict[str, Any] = {
        "kind": "qa_z.governance_baseline",
        "schema_version": 1,
        "status": "created",
        "root": str(root),
        "created_at": utc_now(),
        "summary": {
            "config_exists": (root / "qa-z.yaml").is_file(),
            "latest_run_exists": (root / ".qa-z" / "runs" / "latest").exists(),
            "waivers_file_exists": (root / WAIVERS_PATH).is_file(),
        },
    }
    write_json(root / BASELINE_PATH, payload)
    return payload


def add_waiver(
    *,
    root: Path,
    finding_id: str,
    owner: str,
    reason: str,
    expires: str,
) -> dict[str, Any]:
    """Append a local governance waiver."""
    root = root.expanduser().resolve()
    expires_on = parse_expiration(expires)
    payload: dict[str, Any] = {
        "kind": "qa_z.governance_waiver",
        "schema_version": 1,
        "status": "active" if expires_on >= date.today() else "expired",
        "finding_id": finding_id,
        "owner": owner,
        "reason": reason,
        "expires": expires,
        "created_at": utc_now(),
    }
    store = load_waivers(root)
    store["waivers"].append(payload)
    write_json(root / WAIVERS_PATH, store)
    return payload


def build_governance_report(root: Path) -> dict[str, Any]:
    """Build a local governance report from baseline and waivers."""
    root = root.expanduser().resolve()
    baseline_path = root / BASELINE_PATH
    baseline = read_json_if_exists(baseline_path) or {
        "kind": "qa_z.governance_baseline",
        "status": "missing",
    }
    waivers = load_waivers(root)["waivers"]
    active = sum(1 for item in waivers if item.get("status") == "active")
    expired = sum(1 for item in waivers if item.get("status") == "expired")
    audit_trail = [
        format_path(path, root)
        for path in (baseline_path, root / WAIVERS_PATH)
        if path.exists()
    ]
    return {
        "kind": "qa_z.governance_report",
        "schema_version": 1,
        "status": "warning"
        if active or baseline.get("status") == "missing"
        else "ready",
        "baseline": baseline,
        "waiver_summary": {
            "active": active,
            "expired": expired,
            "total": len(waivers),
        },
        "audit_trail": audit_trail,
    }


def parse_expiration(value: str) -> date:
    """Parse a YYYY-MM-DD waiver expiration."""
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("waiver --expires must use YYYY-MM-DD.") from exc


def load_waivers(root: Path) -> dict[str, Any]:
    """Load the local waiver store."""
    loaded = read_json_if_exists(root / WAIVERS_PATH)
    if not isinstance(loaded, dict):
        return {
            "kind": "qa_z.governance_waivers",
            "schema_version": 1,
            "waivers": [],
        }
    waivers = loaded.get("waivers")
    if not isinstance(waivers, list):
        loaded["waivers"] = []
    return loaded


def read_json_if_exists(path: Path) -> dict[str, Any] | None:
    """Read a JSON object if it exists."""
    if not path.is_file():
        return None
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return loaded if isinstance(loaded, dict) else None


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write stable JSON for governance artifacts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
