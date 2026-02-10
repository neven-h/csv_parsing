from __future__ import annotations

import pandas as pd

from bank_csv_normalizer.normalize.amounts import parse_amount
from bank_csv_normalizer.normalize.dates import parse_date_to_iso
from bank_csv_normalizer.normalize.text import clean_description
from bank_csv_normalizer.profiles.base import BaseProfile


class IsraeliCardsAggregateV1(BaseProfile):
    """
    Israeli card export with columns like:
    כרטיס, בית עסק, תאריך עסקה, סכום העסקה, ..., תאריך החיוב, סכום החיוב, ...
    """

    name = "israeli_cards_aggregate_v1"

    header_signatures = [
        ["כרטיס", "בית עסק", "תאריך עסקה", "סכום העסקה"],
        ["כרטיס", "בית עסק", "תאריך החיוב", "סכום החיוב"],
        ["כרטיס", "תאריך עסקה", "סכום העסקה"],
    ]

    def extract_canonical(self, df: pd.DataFrame) -> pd.DataFrame:
        def col(name: str) -> pd.Series:
            if name in df.columns:
                return df[name].astype(str)
            return pd.Series([""] * len(df), dtype=str)

        account = col("כרטיס")

        merchant = col("בית עסק")
        details = col("פירוט")

        # Prefer transaction date; fallback to billing date
        date_raw = col("תאריך עסקה")
        if date_raw.eq("").all():
            date_raw = col("תאריך החיוב")

        # Prefer billed amount; fallback to transaction amount
        amt_raw = col("סכום החיוב")
        if amt_raw.eq("").all():
            amt_raw = col("סכום העסקה")

        # Description: merchant + optional details
        desc = merchant.fillna("").astype(str).str.strip()
        det = details.fillna("").astype(str).str.strip()
        desc = desc.where(det == "", desc + " — " + det)

        out = pd.DataFrame(
            {
                "account_number": account.fillna("").astype(str).str.strip(),
                "transaction_date": date_raw.fillna("").astype(str).map(parse_date_to_iso),
                "description": desc.map(clean_description),
                "amount": amt_raw.fillna("").astype(str).map(parse_amount),
            }
        )

        out["amount"] = out["amount"].map(lambda d: "" if d is None else str(d))
        return out
