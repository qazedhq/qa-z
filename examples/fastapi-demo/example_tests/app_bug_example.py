"""Intentional failing test for the QA-Z repair flow demo."""

from app.buggy_main import read_invoice


def test_guest_cannot_read_invoice() -> None:
    response = read_invoice(
        {"id": "guest_456", "role": "member"},
        invoice_owner_id="owner_123",
    )

    assert response["status_code"] == 403, "app/buggy_main.py allowed guest access"
