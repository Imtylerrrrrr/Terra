"""Terra 계산엔진 — 추출 결과 × 배출계수 → 개인/집계 탄소배출량.

단일 진실 형식: docs/CONTRACT.md (§1 입력 · §2 출력 · §3 tier · §5 API).
"""

from .engine import compute, aggregate
from .tiers import tier_from_grams, TIER_LOW, TIER_HIGH
from .factors import load_factors, Factors

__all__ = [
    "compute",
    "aggregate",
    "tier_from_grams",
    "TIER_LOW",
    "TIER_HIGH",
    "load_factors",
    "Factors",
]
