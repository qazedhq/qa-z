"""Intentionally broken invoice access service for repair-packet demos."""

from __future__ import annotations

from typing import Any


def read_invoice(user: dict[str, str], invoice_owner_id: str) -> dict[str, Any]:
    """Return a buggy response that ignores the invoice owner."""
    return {
        "status_code": 200,
        "invoice": {
            "id": "inv_demo",
            "owner_id": invoice_owner_id,
            "viewer_id": user.get("id"),
        },
    }
