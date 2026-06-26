"""도감 해금 로직 — 누적 절감량(gCO2e) → 해금 도감 id (CONTRACT §2-A·§4-A).

해금 규칙(계약 §4-A 확정): 누적 절감 **0.5 / 2 / 5 / 10 kg** 마일스톤마다 1종 해금.
- 숫자=코드(환각0): 누적 절감은 호출측(엔진/DB)이 넘겨주고, 여기선 마일스톤 비교만.
- 카탈로그(항목 id/이름/마일스톤) 단일 진실 = terra_ai/data/collection.json.
  ⚠️ 3D 에셋·비주얼 확정은 이슈 #9(승빈·연성) — 이 모듈은 id/마일스톤만 다룬다.

엔진(주영)은 `unlocks: []`(stateless)를 반환 → 호출측이 누적 절감을 들고 이 모듈로 채운다.
"""
from __future__ import annotations

import json
import pathlib
from functools import lru_cache
from typing import Any

_CATALOG_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "collection.json"


@lru_cache(maxsize=1)
def _catalog() -> list[dict[str, Any]]:
    """collection.json items를 마일스톤 오름차순으로 로드(캐시)."""
    raw = json.loads(_CATALOG_PATH.read_text(encoding="utf-8"))
    items = raw.get("items", [])
    return sorted(items, key=lambda it: it["milestone_kg"])


def _grams(milestone_kg: float) -> float:
    """마일스톤 kg → gCO2e (엔진 단위와 통일)."""
    return milestone_kg * 1000.0


def unlocked_ids(cumulative_saving_grams: float) -> list[str]:
    """누적 절감(gCO2e) 기준 해금된 도감 id (마일스톤 오름차순).

    CONTRACT §2-A `unlocks` 채움용. 마일스톤 이상이면 해금.
    """
    saving = float(cumulative_saving_grams or 0)
    return [it["id"] for it in _catalog() if saving >= _grams(it["milestone_kg"])]


def newly_unlocked(prev_saving_grams: float, new_saving_grams: float) -> list[str]:
    """이번 절감으로 **새로** 해금된 id — 데모 매직모먼트("해금!")용.

    prev < 마일스톤 <= new 구간의 항목만. prev>=new면 빈 배열.
    """
    before = set(unlocked_ids(prev_saving_grams))
    after = unlocked_ids(new_saving_grams)
    return [i for i in after if i not in before]


def next_milestone(cumulative_saving_grams: float) -> dict[str, Any] | None:
    """다음 해금까지 남은 양 — coach 넛지("앞으로 0.3kg 더!")용.

    아직 안 해금된 가장 가까운 항목 {id, name, milestone_kg, remaining_grams}.
    모두 해금했으면 None.
    """
    saving = float(cumulative_saving_grams or 0)
    for it in _catalog():
        threshold = _grams(it["milestone_kg"])
        if saving < threshold:
            # 같은 마일스톤을 공유하는 종 수(0.5kg=4종 등) — 넛지가 복수 해금을 정확히 알리도록.
            count = sum(1 for x in _catalog() if x["milestone_kg"] == it["milestone_kg"])
            return {
                "id": it["id"],
                "name": it["name"],
                "milestone_kg": it["milestone_kg"],
                "remaining_grams": round(threshold - saving, 1),
                "count": count,
            }
    return None


def progress(cumulative_saving_grams: float) -> dict[str, Any]:
    """도감 진행 요약 — 프론트 바인딩 한 번에.

    {unlocked: id[], total: int, next: {…}|None}
    """
    unlocked = unlocked_ids(cumulative_saving_grams)
    return {
        "unlocked": unlocked,
        "total": len(_catalog()),
        "next": next_milestone(cumulative_saving_grams),
    }
