from __future__ import annotations

from datetime import datetime
from typing import Optional

DATE_FORMATS = [
    "%d.%m.%Y",
    "%d/%m/%Y",
    "%Y-%m-%d",
    "%d/%m/%y",
    "%d-%m-%Y",
]


def parse_date_to_iso(value: str) -> Optional[str]:
    v = (value or "").strip()
    if not v:
        return None

    # Sometimes includes time; keep only date part
    v = v.split()[0]

    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(v, fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue

    # last resort: "1.9.2025"
    if "." in v:
        parts = v.split(".")
        if len(parts) == 3:
            try:
                d, m, y = (int(parts[0]), int(parts[1]), int(parts[2]))
                dt = datetime(year=y, month=m, day=d)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass

    return None
