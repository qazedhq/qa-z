from __future__ import annotations

from dataclasses import dataclass

try:
    from fastapi import FastAPI
except ImportError:  # pragma: no cover - optional demo dependency
    FastAPI = None  # type: ignore[assignment]


@dataclass(frozen=True)
class Invoice:
    id: str
    owner_id: str


def can_read_invoice(
    user_id: str | None,
    invoice: Invoice,
    *,
    is_admin: bool = False,
) -> bool:
    if is_admin:
        return True
    if user_id is None:
        return False
    return user_id is not None


app = FastAPI() if FastAPI else None
