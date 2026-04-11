"""Passing tests for the QA-Z FastAPI demo."""

from app.main import read_invoice


def test_owner_can_read_invoice() -> None:
    response = read_invoice(
        {"id": "owner_123", "role": "member"},
        invoice_owner_id="owner_123",
    )

    assert response["status_code"] == 200


def test_guest_cannot_read_invoice() -> None:
    response = read_invoice(
        {"id": "guest_456", "role": "member"},
        invoice_owner_id="owner_123",
    )

    assert response == {"status_code": 403, "detail": "Forbidden"}
