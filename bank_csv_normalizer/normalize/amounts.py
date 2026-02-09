from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Optional


def _strip_currency_and_spaces(s: str) -> str:
    return (
        (s or "")
        .replace("₪", "")
        .replace("$", "")
        .replace("€", "")
        .replace("\u00a0", " ")
        .strip()
    )


def parse_amount(value: str) -> Optional[Decimal]:
    """Best-effort amount parser for common bank exports."""
    v = _strip_currency_and_spaces(value)
    if not v:
        return None

    negative = False
    if v.startswith("(") and v.endswith(")"):
        negative = True
        v = v[1:-1].strip()

    # If contains both comma and dot, decide which is decimal
    if "," in v and "." in v:
        if v.rfind(",") > v.rfind("."):
            # EU style: 1.234,56
            v = v.replace(".", "")
            v = v.replace(",", ".")
        else:
            # US style: 1,234.56
            v = v.replace(",", "")
    else:
        # Only comma exists: might be decimal comma or thousand sep
        if "," in v and "." not in v:
            parts = v.split(",")
            if len(parts) == 2 and len(parts[1]) in (1, 2):
                v = v.replace(",", ".")
            else:
                v = v.replace(",", "")

    v = v.replace(" ", "")
    if v.startswith("+"):
        v = v[1:]

    try:
        amt = Decimal(v)
        if negative:
            amt = -amt
        return amt
    except (InvalidOperation, ValueError):
        return None
