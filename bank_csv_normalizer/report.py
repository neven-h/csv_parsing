from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List
import json


@dataclass
class ConversionReport:
    profile: str
    confidence: float
    rows_in: int
    rows_out: int
    dropped_rows: int
    warnings: List[str]

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)
