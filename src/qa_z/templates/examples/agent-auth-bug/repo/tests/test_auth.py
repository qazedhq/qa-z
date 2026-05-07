from __future__ import annotations

from app.auth import Invoice, can_view_invoice


def test_owner_can_view_invoice() -> None:
    invoice = Invoice(id="inv_123", owner_id="user_1")

    assert can_view_invoice("user_1", invoice)


def test_admin_can_view_invoice() -> None:
    invoice = Invoice(id="inv_123", owner_id="user_1")

    assert can_view_invoice("support_admin", invoice, is_admin=True)


def test_non_owner_cannot_view_invoice() -> None:
    invoice = Invoice(id="inv_123", owner_id="user_1")

    assert not can_view_invoice("user_2", invoice)
