from __future__ import annotations

import re


def clean_header(h: str) -> str:
    return re.sub(r"\s+", " ", (h or "").strip())


def clean_description(s: str) -> str:
    v = (s or "").strip()
    v = re.sub(r"\s+", " ", v)
    return v
