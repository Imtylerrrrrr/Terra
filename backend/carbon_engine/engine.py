"""계산엔진 — 추출 결과 × 계수 → 개인 결과(2-A) / 집계 결과(2-B).

형식 단일 진실: docs/CONTRACT.md.
- compute()   : 한 사용자의 ExtractionResult → PersonalResult
- aggregate() : 여러 PersonalResult → AggregateResult(학과/캠퍼스)
"""

from __future__ import annotations

from typing import Any, Iterable

from .factors import Factors, load_factors
from .tiers import tier_from_grams

_SEED_SOURCE = "factors.seed(임시추정)"


# ── 활동 1건 → (배출 breakdown 목록, needs_review) ────────────────────────────
def _activity_breakdown(act: dict[str, Any], f: Factors) -> tuple[list[dict[str, Any]], bool]:
    t = act.get("type")

    if t == "menu":
        name = act.get("name", "")
        recipe = f.menu_recipes.get(name)
        if recipe is None:
            return [], True  # 미매핑 메뉴 → 확인 필요
        rows: list[dict[str, Any]] = []
        review = False
        for part in recipe:
            item, grams = part["item"], part["grams"]
            factor = f.food_factors.get(item)
            if factor is None:
                review = True
                continue
            rows.append({"label": item, "grams_co2e": round(grams * factor, 1), "source": _SEED_SOURCE})
        return rows, review

    if t == "food":
        item, grams = act.get("item", ""), act.get("grams", 0)
        factor = f.food_factors.get(item)
        if factor is None:
            return [], True
        return [{"label": item, "grams_co2e": round(grams * factor, 1), "source": _SEED_SOURCE}], False

    if t == "purchase":
        item, qty = act.get("item", ""), act.get("qty", 0)
        factor = f.purchase_factors.get(item)
        if factor is None:
            return [], True
        return [{"label": item, "grams_co2e": round(qty * factor, 1), "source": _SEED_SOURCE}], False

    if t == "screentime":
        item, minutes = act.get("item", ""), act.get("minutes", 0)
        factor = f.screentime_factor.get(item)
        if factor is None:
            return [], True
        return [{"label": item, "grams_co2e": round(minutes * factor, 1), "source": _SEED_SOURCE}], False

    if t == "energy":
        item, kwh = act.get("item", ""), act.get("kwh", 0)
        factor = f.energy_factors.get(item)
        if factor is None:
            return [], True
        return [{"label": item, "grams_co2e": round(kwh * factor, 1), "source": _SEED_SOURCE}], False

    # 알 수 없는 type
    return [], True


def _item_name(act: dict[str, Any]) -> str:
    return act.get("name") or act.get("item") or act.get("type", "unknown")


def _menu_total(name: str, f: Factors) -> float | None:
    """menu_recipes 의 한 메뉴 총 배출량(없거나 계수 누락이면 None)."""
    recipe = f.menu_recipes.get(name)
    if recipe is None:
        return None
    total = 0.0
    for part in recipe:
        factor = f.food_factors.get(part["item"])
        if factor is None:
            return None
        total += part["grams"] * factor
    return total


def _best_alternative(total: float, f: Factors) -> dict[str, Any] | None:
    """코칭용: 시드 메뉴 중 가장 낮은 메뉴가 현재보다 낮으면 추천."""
    best_name, best_total = None, None
    for name in f.menu_recipes:
        mt = _menu_total(name, f)
        if mt is None:
            continue
        if best_total is None or mt < best_total:
            best_name, best_total = name, mt
    if best_name is None or best_total is None or best_total >= total:
        return None
    return {
        "name": best_name,
        "grams_co2e": round(best_total, 1),
        "saving_grams": round(total - best_total, 1),
    }


def compute(
    extraction: dict[str, Any],
    user_id: str,
    dept_id: str,
    factors: Factors | None = None,
) -> dict[str, Any]:
    """ExtractionResult(§1) → PersonalResult(§2-A)."""
    f = factors or load_factors()
    activities = extraction.get("activities", [])

    items: list[dict[str, Any]] = []
    total = 0.0
    needs_review = bool(extraction.get("needs_review", False))

    for act in activities:
        rows, review = _activity_breakdown(act, f)
        needs_review = needs_review or review
        item_total = round(sum(r["grams_co2e"] for r in rows), 1)
        total += item_total
        items.append(
            {
                "name": _item_name(act),
                "total_grams_co2e": item_total,
                "breakdown": rows,
                "sources": sorted({r["source"] for r in rows}),
            }
        )

    total = round(total, 1)
    result: dict[str, Any] = {
        "user_id": user_id,
        "dept_id": dept_id,
        "total_grams_co2e": total,
        "tier": tier_from_grams(total),
        "items": items,
        # unlocks: 누적 절감 이력 필요 → 엔진 단독 산출 불가. 마일스톤 적용은 호출측/DB 집계.
        "unlocks": [],
    }
    alt = _best_alternative(total, f)
    if alt is not None:
        result["best_alternative"] = alt
    if needs_review:
        result["needs_review"] = True
    return result


# ── 집계 (2-B) ───────────────────────────────────────────────────────────────
def _mean(values: list[float]) -> float:
    return round(sum(values) / len(values), 1) if values else 0.0


def aggregate(
    personal_results: Iterable[dict[str, Any]],
    dept_meta: dict[str, dict[str, Any]],
    campus_id: str,
) -> dict[str, Any]:
    """여러 PersonalResult → AggregateResult(§2-B).

    dept_meta: { dept_id: { "name": str, "total_students": int } }
    행성 크기 = participation_rate, 깨끗함 = avg tier.
    """
    results = list(personal_results)

    by_dept: dict[str, list[float]] = {}
    for r in results:
        by_dept.setdefault(r["dept_id"], []).append(r["total_grams_co2e"])

    departments: list[dict[str, Any]] = []
    for dept_id, grams_list in by_dept.items():
        meta = dept_meta.get(dept_id, {})
        total_students = int(meta.get("total_students", 0))
        participants = len(grams_list)
        rate = round(participants / total_students, 4) if total_students > 0 else 0.0
        avg = _mean(grams_list)
        departments.append(
            {
                "dept_id": dept_id,
                "name": meta.get("name", dept_id),
                "participants": participants,
                "total_students": total_students,
                "participation_rate": rate,
                "avg_grams_co2e": avg,
                "tier": tier_from_grams(avg),
            }
        )

    departments.sort(key=lambda d: d["dept_id"])

    total_participants = sum(d["participants"] for d in departments)
    total_students_all = sum(d["total_students"] for d in departments)
    campus_rate = round(total_participants / total_students_all, 4) if total_students_all > 0 else 0.0
    campus_avg = _mean([g for grams in by_dept.values() for g in grams])

    return {
        "campus_system": {
            "campus_id": campus_id,
            "participation_rate": campus_rate,
            "avg_grams_co2e": campus_avg,
            "tier": tier_from_grams(campus_avg),
            "departments": departments,
        }
    }
