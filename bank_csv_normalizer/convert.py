from __future__ import annotations

from typing import Optional, List

from bank_csv_normalizer.normalize.io import load_csv
from bank_csv_normalizer.detect import detect_profile
from bank_csv_normalizer.profiles import ALL_PROFILES
from bank_csv_normalizer.report import ConversionReport


CANONICAL_COLS = ["account_number", "transaction_date", "description", "amount"]


def _get_profile_by_name(name: str):
    for p in ALL_PROFILES:
        if p.name == name:
            return p
    return None


def convert(input_path: str, output_path: str, report_path: Optional[str] = None) -> ConversionReport:
    load_res = load_csv(input_path)
    df = load_res.df

    match = detect_profile(df)
    profile = _get_profile_by_name(match.name)

    warnings: List[str] = []
    if profile is None:
        raise ValueError(f"No profile found for detected name '{match.name}'. Reasons: {match.reasons}")

    canonical = profile.extract_canonical(df)

    rows_in = len(df)

    canonical = canonical[CANONICAL_COLS].copy()

    canonical["account_number"] = canonical["account_number"].fillna("").astype(str).str.strip()
    canonical["description"] = canonical["description"].fillna("").astype(str).str.strip()
    canonical["transaction_date"] = canonical["transaction_date"].fillna("").astype(str).str.strip()
    canonical["amount"] = canonical["amount"].fillna("").astype(str).str.strip()

    total_markers = ["סה\"כ", "סה״כ", "TOTAL", "Total", "סך הכל"]
    mask_total = canonical["description"].apply(lambda x: any(m in x for m in total_markers))
    if mask_total.any():
        warnings.append(f"Removed {int(mask_total.sum())} total/footer rows by marker match.")
        canonical = canonical[~mask_total]

    required_mask = (
        (canonical["account_number"] != "")
        & (canonical["transaction_date"] != "")
        & (canonical["description"] != "")
        & (canonical["amount"] != "")
    )
    dropped = int((~required_mask).sum())
    if dropped:
        warnings.append(f"Dropped {dropped} rows missing required canonical fields after parsing.")
    canonical = canonical[required_mask]

    canonical = canonical[CANONICAL_COLS]
    canonical.to_csv(output_path, index=False, encoding="utf-8")

    rep = ConversionReport(
        profile=match.name,
        confidence=match.confidence,
        rows_in=rows_in,
        rows_out=len(canonical),
        dropped_rows=(rows_in - len(canonical)) if rows_in >= len(canonical) else dropped,
        warnings=warnings + match.reasons,
    )

    if report_path:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(rep.to_json())

    return rep
