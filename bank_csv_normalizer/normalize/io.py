from __future__ import annotations

import csv
import io
from dataclasses import dataclass
from typing import Tuple

import pandas as pd


@dataclass
class LoadResult:
    df: pd.DataFrame
    encoding: str
    delimiter: str
    header_row_index: int
    raw_text_preview: str


COMMON_ENCODINGS = ["utf-8-sig", "utf-8", "cp1255", "iso-8859-8", "windows-1252"]
COMMON_DELIMS = [",", ";", "\t", "|"]


def _decode_bytes(data: bytes) -> Tuple[str, str]:
    last_err = None
    for enc in COMMON_ENCODINGS:
        try:
            return data.decode(enc), enc
        except Exception as e:
            last_err = e
    raise ValueError(f"Failed to decode input bytes with common encodings. Last error: {last_err}")


def _sniff_delimiter(text: str) -> str:
    sample = text[:50_000]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters="".join(COMMON_DELIMS))
        return dialect.delimiter
    except Exception:
        lines = [ln for ln in sample.splitlines() if ln.strip()][:20]
        scores = {d: sum(ln.count(d) for ln in lines) for d in COMMON_DELIMS}
        return max(scores, key=scores.get) if scores else ","


def _find_header_row(text: str, delimiter: str, min_columns: int = 4) -> int:
    """
    Bank exports often have preambles and even multiple sub-tables.
    We score candidates by keyword hits + width + lookahead for date/amount-like values.
    """

    header_keywords = [
        "תאריך", "סכום", "תיאור", "תאור", "פרטים", "עסקה", "פעולה",
        "שם בית עסק", "אסמכתא", "חובה", "זכות", "מטבע", "מספר חשבון", "יתרה",
        "date", "amount", "description", "details", "transaction", "currency", "account", "balance",
    ]

    def is_date_like(s: str) -> bool:
        s = (s or "").strip()
        if not s:
            return False
        if len(s) >= 8 and any(ch in s for ch in (".", "/", "-")):
            digits = sum(c.isdigit() for c in s)
            seps = sum(c in ".-/" for c in s)
            return digits >= 6 and seps >= 2
        return False

    def is_amount_like(s: str) -> bool:
        s = (s or "").strip()
        if not s:
            return False
        s2 = s.replace("₪", "").replace("$", "").replace("€", "").replace(" ", "")
        if s2.startswith("(") and s2.endswith(")"):
            s2 = s2[1:-1]
        if s2.startswith("+") or s2.startswith("-"):
            s2 = s2[1:]
        s2 = s2.replace(",", "").replace(".", "")
        return s2.isdigit()

    rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    max_scan = min(len(rows), 500)

    best_idx = 0
    best_score = -1

    for i in range(max_scan):
        row = rows[i]
        cells = [str(c).strip().strip('"') for c in row]
        nonempty = [c for c in cells if c]
        if len(nonempty) < min_columns:
            continue

        joined = " ".join(nonempty).lower()
        kw_hits = sum(1 for kw in header_keywords if kw.lower() in joined)

        numeric_like = 0
        for c in nonempty:
            q = (
                c.replace(".", "").replace("/", "").replace("-", "").replace(",", "")
                 .replace("₪", "").replace("$", "").replace("€", "").strip()
            )
            if q.isdigit():
                numeric_like += 1

        numeric_ratio = numeric_like / max(1, len(nonempty))
        if numeric_ratio > 0.7 and kw_hits == 0:
            continue

        base_score = kw_hits * 10 + len(nonempty)

        date_hits = 0
        amt_hits = 0
        for j in range(i + 1, min(i + 41, max_scan)):
            for c in rows[j]:
                if date_hits < 30 and is_date_like(c):
                    date_hits += 1
                if amt_hits < 30 and is_amount_like(c):
                    amt_hits += 1
            if date_hits >= 10 and amt_hits >= 10:
                break

        score = base_score + date_hits * 2 + amt_hits

        if score > best_score:
            best_score = score
            best_idx = i

    return best_idx


def load_csv(path: str) -> LoadResult:
    with open(path, "rb") as f:
        data = f.read()

    text, encoding = _decode_bytes(data)
    delimiter = _sniff_delimiter(text)
    header_row_index = _find_header_row(text, delimiter=delimiter, min_columns=4)

    df = pd.read_csv(
        io.StringIO(text),
        sep=delimiter,
        header=header_row_index,
        dtype=str,
        engine="python",
        keep_default_na=False,
    )

    df.columns = [str(c).strip() for c in df.columns]
    preview = "\n".join(text.splitlines()[:20])

    return LoadResult(
        df=df,
        encoding=encoding,
        delimiter=delimiter,
        header_row_index=header_row_index,
        raw_text_preview=preview,
    )
