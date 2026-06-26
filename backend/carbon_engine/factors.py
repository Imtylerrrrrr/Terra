"""배출계수 시드 로더.

factors.seed.json(임시 추정, 주영 관리)을 읽어 엔진에 공급한다.
민지 정식 계수는 같은 키/단위/형식으로 값만 교체하면 됨 (CONTRACT.md §4-A).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_SEED_PATH = Path(__file__).with_name("factors.seed.json")


@dataclass(frozen=True)
class Factors:
    """계수 테이블 묶음. 키는 CONTRACT.md §1 의 계수 테이블 이름과 일치."""

    menu_recipes: dict[str, list[dict[str, Any]]]
    food_factors: dict[str, float]      # gCO2e / g
    purchase_factors: dict[str, float]  # gCO2e / 개
    screentime_factor: dict[str, float]  # gCO2e / 분
    energy_factors: dict[str, float]    # gCO2e / kWh

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "Factors":
        return cls(
            menu_recipes=raw.get("menu_recipes", {}),
            food_factors=raw.get("food_factors", {}),
            purchase_factors=raw.get("purchase_factors", {}),
            screentime_factor=raw.get("screentime_factor", {}),
            energy_factors=raw.get("energy_factors", {}),
        )


def load_factors(path: str | Path | None = None) -> Factors:
    """시드 JSON에서 계수를 로드. path 미지정 시 패키지 동봉 시드 사용."""
    p = Path(path) if path is not None else _SEED_PATH
    with open(p, encoding="utf-8") as f:
        raw = json.load(f)
    return Factors.from_dict(raw)
