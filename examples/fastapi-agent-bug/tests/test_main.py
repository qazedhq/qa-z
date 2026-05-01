from __future__ import annotations

from app.main import Invoice, can_read_invoice


def test_owner_can_read_invoice() -> None:
    assert can_read_invoice("user_1", Invoice(id="inv_1", owner_id="user_1"))


def test_admin_can_read_invoice() -> None:
    assert can_read_invoice(
        "support_admin",
        Invoice(id="inv_1", owner_id="user_1"),
        is_admin=True,
    )


def test_non_owner_cannot_read_invoice() -> None:
    assert not can_read_invoice("user_2", Invoice(id="inv_1", owner_id="user_1"))


def test_anonymous_user_cannot_read_invoice() -> None:
    assert not can_read_invoice(None, Invoice(id="inv_1", owner_id="user_1"))
