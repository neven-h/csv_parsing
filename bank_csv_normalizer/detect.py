from __future__ import annotations

import pandas as pd

from bank_csv_normalizer.profiles import ALL_PROFILES
from bank_csv_normalizer.profiles.base import ProfileMatch


def detect_profile(df: pd.DataFrame) -> ProfileMatch:
    matches = [p.match(df) for p in ALL_PROFILES]
    matches.sort(key=lambda m: m.confidence, reverse=True)
    return matches[0] if matches else ProfileMatch(name="unknown", confidence=0.0, reasons=["No profiles registered."])
