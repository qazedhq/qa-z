"""Small invoice access service for the QA-Z demo."""

from __future__ import annotations

from typing import Any

try:
    from fastapi import FastAPI, HTTPException
except ImportError:  # pragma: no cover - optional demo dependency
    FastAPI = None
    HTTPException = None


def can_read_invoice(user: dict[str, str], invoice_owner_id: str) -> bool:
    """Return whether a user may read an invoice."""
    return user.get("role") == "admin" or user.get("id") == invoice_owner_id


def read_invoice(user: dict[str, str], invoice_owner_id: str) -> dict[str, Any]:
    """Return a simple response object for the invoice read path."""
    if not can_read_invoice(user, invoice_owner_id):
        return {"status_code": 403, "detail": "Forbidden"}
    return {
        "status_code": 200,
        "invoice": {"id": "inv_demo", "owner_id": invoice_owner_id},
    }


app = FastAPI() if FastAPI is not None else None

if app is not None:

    @app.get("/invoices/{invoice_id}")
    def get_invoice(
        invoice_id: str, user_id: str, role: str = "member"
    ) -> dict[str, Any]:
        response = read_invoice(
            {"id": user_id, "role": role},
            invoice_owner_id="owner_123",
        )
        if response["status_code"] == 403:
            if HTTPException is None:
                raise RuntimeError("FastAPI HTTPException is unavailable.")
            raise HTTPException(status_code=403, detail=response["detail"])
        return {"id": invoice_id, **response["invoice"]}
