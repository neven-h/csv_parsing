from __future__ import annotations

import pandas as pd

from bank_csv_normalizer.normalize.dates import parse_date_to_iso
from bank_csv_normalizer.normalize.amounts import parse_amount
from bank_csv_normalizer.normalize.text import clean_description
from bank_csv_normalizer.profiles.base import BaseProfile, ProfileMatch


class DiscountBankVisaV1(BaseProfile):
    """
    Discount Bank (דיסקונט) Visa debit/credit card export (.xlsx).

    Layout (0-indexed rows, no header=None read):
      Row 0  – account title   (merged cell, skip)
      Row 1  – empty           (skip)
      Row 2  – section total   (skip)
      Row 3  – column headers  ← actual header
      Row 4+ – transactions
      Last 2 – empty + footer  (dropped by convert_df)

    Columns used (by name, with newline-stripped keys):
      col 0  – תאריך עסקה  (transaction date, already a datetime)
      col 1  – שם בית עסק  (description)
      col 2  – סכום עסקה   (original purchase amount – may differ for FX)
      col 3  – סכום חיוב   (charged amount in ILS ← preferred)
      col 4  – סוג עסקה    (transaction type, e.g. מיידית / רגילה / החזר)

    Account number is extracted from the title row (row 0, col 0).

    Signature: header row contains both "שם בית עסק" and "סכום חיוב".
    These two together are unique to this bank's export format.
    """

    name = "discount_bank_visa_v1"

    # Signatures checked AFTER the library strips newlines from column names.
    # The header row has "תאריך\nעסקה" etc. – our loader normalises them.
    header_signatures = [
        ["שם בית עסק", "סכום חיוב", "סוג\nעסקה"],
        ["שם בית עסק", "סכום חיוב"],
    ]

    # ------------------------------------------------------------------ #
    # Override match() to handle Excel pre-processed DataFrames.           #
    # The base class matches against df.columns; for Excel we pre-process  #
    # (header=None, skiprows=3) before calling convert_df, so columns are  #
    # already the header row values.                                        #
    # ------------------------------------------------------------------ #
    def match(self, df: pd.DataFrame) -> ProfileMatch:
        # Normalise column names: strip whitespace AND embedded newlines
        cols = [str(c).replace("\n", " ").strip() for c in df.columns]
        colset = set(cols)

        best = 0.0
        best_reasons: list[str] = []
        best_sig_len = 0

        for sig in self.header_signatures:
            # Also normalise signature entries the same way
            norm_sig = [s.replace("\n", " ").strip() for s in sig]
            hits = [x for x in norm_sig if x in colset]
            conf = len(hits) / max(1, len(norm_sig))
            if conf > best or (conf == best and len(norm_sig) > best_sig_len):
                best = conf
                best_sig_len = len(norm_sig)
                best_reasons = [
                    f"Matched {len(hits)}/{len(norm_sig)} signature headers: {hits}"
                ]

        return ProfileMatch(name=self.name, confidence=best, reasons=best_reasons)

    # ------------------------------------------------------------------ #
    # extract_canonical                                                    #
    # ------------------------------------------------------------------ #
    def extract_canonical(self, df: pd.DataFrame) -> pd.DataFrame:
        # Normalise column names once so we can look them up safely
        df = df.copy()
        df.columns = [str(c).replace("\n", " ").strip() for c in df.columns]

        def _col(preferred: str, fallback_idx: int) -> pd.Series:
            if preferred in df.columns:
                return df[preferred].astype(str)
            if len(df.columns) > fallback_idx:
                return df.iloc[:, fallback_idx].astype(str)
            return pd.Series([""] * len(df))

        date_raw = _col("תאריך עסקה", 0).fillna("").astype(str)
        desc_raw = _col("שם בית עסק", 1).fillna("").astype(str)
        amt_raw = _col("סכום חיוב", 3).fillna("").astype(str)   # charged amount (ILS)

        # account_number: not a per-row column in this format.
        # Left empty — account_number is optional in the canonical schema.
        account = pd.Series([""] * len(df))

        def _parse_date(val: str) -> str:
            # pandas read_excel already parses dates as Timestamp strings like
            # "2025-11-30 00:00:00"; strip the time part first.
            val = val.split(" ")[0].strip()
            return parse_date_to_iso(val)

        out = pd.DataFrame(
            {
                "account_number": account,
                "transaction_date": date_raw.map(_parse_date),
                "description": desc_raw.map(clean_description),
                "amount": amt_raw.map(lambda x: str(parse_amount(x) or "")),
            }
        )

        return out
