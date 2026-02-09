from __future__ import annotations

from dataclasses import dataclass
from typing import List

import pandas as pd


@dataclass
class ProfileMatch:
    name: str
    confidence: float
    reasons: List[str]


class BaseProfile:
    name: str = "base"
    header_signatures: List[List[str]] = []

    def match(self, df: pd.DataFrame) -> ProfileMatch:
        cols = [str(c).strip() for c in df.columns]
        colset = set(cols)

        best = 0.0
        best_reasons: List[str] = []
        best_sig_len = 0

        for sig in self.header_signatures:
            hits = [x for x in sig if x in colset]
            conf = len(hits) / max(1, len(sig))
            # tie-break: prefer longer signature
            if conf > best or (conf == best and len(sig) > best_sig_len):
                best = conf
                best_sig_len = len(sig)
                best_reasons = [f"Matched {len(hits)}/{len(sig)} signature headers: {hits}"]

        return ProfileMatch(name=self.name, confidence=best, reasons=best_reasons)

    def extract_canonical(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError
