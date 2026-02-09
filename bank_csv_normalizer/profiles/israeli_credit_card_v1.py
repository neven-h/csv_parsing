from __future__ import annotations

import pandas as pd

from bank_csv_normalizer.normalize.dates import parse_date_to_iso
from bank_csv_normalizer.normalize.amounts import parse_amount
from bank_csv_normalizer.normalize.text import clean_description
from bank_csv_normalizer.profiles.base import BaseProfile


class IsraeliCreditCardV1(BaseProfile):
    """Common Israeli credit-card export format."""

    name = "israeli_credit_card_v1"

    header_signatures = [
        ["שם כרטיס", "תאריך", "שם בית עסק", "סכום קנייה"],
        ["תאריך", "שם בית עסק", "סכום קנייה"],
    ]

    def extract_canonical(self, df: pd.DataFrame) -> pd.DataFrame:
        def pick(colname: str, fallback_idx: int):
            return (
                df[colname]
                if colname in df.columns
                else (df.iloc[:, fallback_idx] if len(df.columns) > fallback_idx else "")
            )

        account = pick("שם כרטיס", 0).astype(str)
        date_raw = pick("תאריך", 1).astype(str)
        desc_raw = pick("שם בית עסק", 2).astype(str)
        amt_raw = pick("סכום קנייה", 3).astype(str)

        out = pd.DataFrame(
            {
                "account_number": account.map(lambda x: x.strip()),
                "transaction_date": date_raw.map(parse_date_to_iso),
                "description": desc_raw.map(clean_description),
                "amount": amt_raw.map(lambda x: parse_amount(x)),
            }
        )

        out["amount"] = out["amount"].map(lambda d: ("" if d is None else str(d)))
        return out
