from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Invoice:
    id: str
    owner_id: str


def can_view_invoice(
    actor_id: str | None,
    invoice: Invoice,
    *,
    is_admin: bool = False,
) -> bool:
    if is_admin:
        return True
    if actor_id is None:
        return False

    return actor_id == invoice.owner_id
