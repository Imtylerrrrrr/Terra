"""도감 해금 — 누적 절감량(gCO2e) → 해금 도감 id (CONTRACT §2-A·§4-A).

해금 규칙(§4-A 확정): 누적 절감 **0.5 / 2 / 5 / 10 kg** 마일스톤 이상이면 해당 종 해금.
- 숫자=코드(환각0): 누적 절감은 호출측(핸들러/DB)이 넘겨주고, 여기선 마일스톤 비교만.
- 로직은 terra_ai/gamify/unlocks.py(민지) 와 **의미 1:1**. 단, compute Lambda zip 에
  terra_ai 가 포함되지 않으므로 카탈로그를 carbon_engine 에 미러(dex_catalog.seed.json)한다.
  → 두 카탈로그(items 의 id·milestone_kg)는 항상 일치해야 함(tests 드리프트 가드).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CATALOG_PATH = Path(__file__).with_name("dex_catalog.seed.json")


@lru_cache(maxsize=1)
def _catalog(path: str | None = None) -> list[dict[str, Any]]:
    """카탈로그 items 를 마일스톤 오름차순으로 로드(캐시)."""
    p = Path(path) if path is not None else _CATALOG_PATH
    raw = json.loads(p.read_text(encoding="utf-8"))
    items = raw.get("items", [])
    return sorted(items, key=lambda it: it["milestone_kg"])


def _grams(milestone_kg: float) -> float:
    """마일스톤 kg → gCO2e (엔진 단위와 통일)."""
    return milestone_kg * 1000.0


def unlocked_ids(cumulative_saving_grams: float | None) -> list[str]:
    """누적 절감(gCO2e) 기준 해금된 도감 id (마일스톤 오름차순).

    PersonalResult.unlocks(§2-A) 채움용. 마일스톤 이상이면 해금. None/음수/비숫자는 0 취급.
    """
    try:
        saving = float(cumulative_saving_grams or 0)
    except (TypeError, ValueError):
        saving = 0.0
    if saving < 0:
        saving = 0.0
    return [it["id"] for it in _catalog() if saving >= _grams(it["milestone_kg"])]


def catalog_ids() -> list[str]:
    """카탈로그 전체 id (마일스톤 오름차순) — 드리프트 가드/검증용."""
    return [it["id"] for it in _catalog()]
