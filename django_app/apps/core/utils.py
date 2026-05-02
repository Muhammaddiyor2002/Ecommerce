"""Small utility helpers used across apps."""

from __future__ import annotations

import secrets
import string
from decimal import Decimal


def generate_token(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


def generate_order_number(prefix: str = "NC") -> str:
    """Format: NC-YYYYMMDD-RANDOM6 (URL-safe, sortable, hard to guess)."""
    import datetime as _dt

    today = _dt.datetime.utcnow().strftime("%Y%m%d")
    rand = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    return f"{prefix}-{today}-{rand}"


def money(value: int | float | str | Decimal) -> Decimal:
    """Normalize to two-decimal Decimal for currency arithmetic."""
    return Decimal(str(value)).quantize(Decimal("0.01"))


def safe_dict(obj: object, fields: tuple[str, ...]) -> dict[str, object]:
    return {f: getattr(obj, f, None) for f in fields}
