"""
통합 계수 해소 (계수 매핑 레인) — 입력 4종 activities(CONTRACT §1) → 항목별 gCO2e + 합계.

데이터 단일 진실: data/factors.json (scripts/build_factors.py로 CSV→JSON 빌드).
라우팅:
  menu/food/energy → factors.json 직접 계산 (활동량×계수, 결정적·환각0)
  product          → retrieve.resolve (KB 하이브리드 / 폴백=코드 퍼지매칭) — Cloud RAG
  digital          → factors.json digital (시간×계수)

출력은 CONTRACT §2 형태. tier·학과/캠퍼스 집계·저장은 주영(엔진/Lambda)이 이 결과로 처리.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from terra_ai.bedrock.retrieve import resolve as resolve_product

FACTORS = json.loads((ROOT / "data" / "factors.json").read_text(encoding="utf-8"))
FOOD = FACTORS["food"]
ENERGY = FACTORS["energy_transport"]
RECIPES = FACTORS["menu_recipes"]
DIGITAL = FACTORS["digital"]

# verify가 이 집합이면 '공인', 아니면 '시드/추정'(출처는 있되 검증·교체 예정)
CONFIRMED = {"공인값", "국내값", "확정"}


def food_item(item_ko, grams):
    """식재료 1종: 질량(g) × 계수(kg당) → gCO2e."""
    f = FOOD.get(item_ko)
    if not f:
        return None
    g = grams * f["factor_kgco2e_per_kg"]   # (g/1000)×(kg당)×1000 = g×계수
    return {"label": item_ko, "grams_co2e": round(g, 1),
            "source": f["source"], "verify": f["verify"]}


def menu(menu_ko):
    """학식 메뉴명 → 레시피 전개 → 식재료별 합산 (데모 핵심 경로)."""
    recipe = RECIPES.get(menu_ko)
    if not recipe:
        return None
    items = [x for x in (food_item(i["item"], i["grams"]) for i in recipe) if x]
    all_confirmed = all(i["verify"] in CONFIRMED for i in items)
    return {"name": menu_ko,
            "total_grams_co2e": round(sum(i["grams_co2e"] for i in items), 1),
            "breakdown": items,
            "sources": sorted({i["source"] for i in items}),
            "verify": "공인" if all_confirmed else "일부 시드(출처표기)"}


def energy_item(item_ko, amount):
    """전력(kWh)·연료·교통: 활동량 × 계수 → gCO2e."""
    f = ENERGY.get(item_ko)
    if not f:
        return None
    g = amount * f["factor_kgco2e_per_unit"] * 1000.0
    return {"label": item_ko, "grams_co2e": round(g, 1),
            "unit": f["unit"], "source": f["source"], "verify": f["verify"]}


def _one(a):
    t = a.get("type")
    if t == "menu":
        r = menu(a["name"])
        if not r:
            return None
        return {"type": t, "label": r["name"], "grams_co2e": r["total_grams_co2e"],
                "source": "; ".join(r["sources"]), "breakdown": r["breakdown"],
                "verify": r["verify"]}
    if t == "food":
        r = food_item(a["item"], a["grams"])
        return {"type": t, "label": r["label"], "grams_co2e": r["grams_co2e"],
                "source": r["source"], "verify": r["verify"]} if r else None
    if t == "energy":
        amt = a.get("kwh", a.get("amount", 0))
        r = energy_item(a["item"], amt)
        return {"type": t, "label": r["label"], "grams_co2e": r["grams_co2e"],
                "source": r["source"], "verify": r["verify"]} if r else None
    if t == "product":
        r = resolve_product(a["item"], a.get("qty", 1))
        return {"type": t, "label": r["label"], "grams_co2e": r["grams_co2e"],
                "source": r["source"], "matched": r.get("matched"),
                "needs_review": r.get("needs_review", False)}
    if t == "digital":
        f = DIGITAL.get(a["item"])
        if not f:
            return {"type": t, "label": a["item"], "grams_co2e": 0,
                    "source": "미등록", "needs_review": True}
        g = round(f["factor_gco2e_per_unit"] * float(a.get("hours", 0)), 1)
        return {"type": t, "label": a["item"], "grams_co2e": g,
                "source": f["source"], "verify": f["verify"]}
    return None


def resolve(activities):
    """입력 4종 activities → {total_grams_co2e, items[], by_type}. 잘못된 항목 하나가 전체를 깨지 않음."""
    items = []
    for a in activities:
        try:
            r = _one(a)
        except Exception as e:   # 키 누락·잘못된 값 → needs_review로 격리(크래시 방지)
            r = {"type": a.get("type", "?"), "label": str(a)[:40], "grams_co2e": 0,
                 "source": "처리오류", "needs_review": True, "error": str(e)}
        if r:
            items.append(r)
    by_type = {}
    for i in items:
        by_type[i["type"]] = round(by_type.get(i["type"], 0) + i["grams_co2e"], 1)
    return {"total_grams_co2e": round(sum(i["grams_co2e"] for i in items), 1),
            "items": items, "by_type": by_type}


if __name__ == "__main__":
    import os
    os.environ["MOCK"] = "1"   # product=코드매칭 폴백
    # 하루치 4종 입력 한 묶음
    day = [
        {"type": "menu", "name": "제육덮밥"},                       # 식단
        {"type": "digital", "item": "엔터테인먼트", "hours": 2.17},  # 스크린타임
        {"type": "digital", "item": "소셜", "hours": 1.42},
        {"type": "product", "item": "진라면순한맛", "qty": 2},        # 영수증
        {"type": "energy", "item": "전력_KEITI", "kwh": 1.5},        # 전력
    ]
    out = resolve(day)
    print(f"하루 총 배출: {out['total_grams_co2e']} gCO2e")
    print("type별:", json.dumps(out["by_type"], ensure_ascii=False))
    for i in out["items"]:
        print(f"  [{i['type']:8s}] {i['label'][:22]:22s} {i['grams_co2e']:8.1f}g")
