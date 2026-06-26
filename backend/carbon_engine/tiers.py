"""행성 tier 산출 — CONTRACT.md §3.

임계값(gCO2e): low ≤ 700 · mid 700–2500 · high > 2500.
⚠️ 계수 확정 후 상수만 재튜닝 (형식·코드 불변). CONTRACT.md §4-A.
"""

from typing import Literal

Tier = Literal["low", "mid", "high"]

# 경계 포함 규칙: 700=low, 2500=mid (frontend/src/types/contract.ts 와 동일)
TIER_LOW = 700.0
TIER_HIGH = 2500.0


def tier_from_grams(grams: float) -> Tier:
    """gCO2e → tier. (≤700 low · ≤2500 mid · 그 외 high)"""
    if grams <= TIER_LOW:
        return "low"
    if grams > TIER_HIGH:
        return "high"
    return "mid"
