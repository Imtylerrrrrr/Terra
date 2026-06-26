"""
Terra 탄소 계산 엔진 (참조 스텁) — 소유: 주영(계산엔진 담당).
민지가 추출(extract)→계산 end-to-end 검증 + CONTRACT 실행명세로 두는 용도. 운영 구현은 주영.
"숫자는 공공데이터, 계산은 코드"
LLM은 분류/코칭만, 산수는 여기서. Lambda 핸들러로 바로 이식 가능.

입력: 분류 LLM이 뱉은 정규화 아이템 리스트 (classify.md 스키마)
출력: 항목별 + 합계 gCO2e, 출처 포함 (행성 반영/코칭에 그대로 사용)
"""
import csv
import os

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def _load(path, key):
    with open(os.path.join(DATA, path), encoding="utf-8") as f:
        return {row[key]: row for row in csv.DictReader(f)}


FOOD = _load("food_factors.csv", "item_ko")
ENERGY_TRANSPORT = _load("energy_transport_factors.csv", "item_ko")


def _recipes():
    out = {}
    with open(os.path.join(DATA, "menu_recipes.csv"), encoding="utf-8") as f:
        for row in csv.DictReader(f):
            out.setdefault(row["menu_ko"], []).append(
                (row["ingredient_item"], float(row["grams"]))
            )
    return out


RECIPES = _recipes()


def food_item(item_ko, grams):
    """식재료 1종: 질량(g) × 계수(kg당) → gCO2e"""
    f = FOOD.get(item_ko)
    if not f:
        return None
    g = (grams / 1000.0) * float(f["factor_kgco2e_per_kg"]) * 1000.0
    return {"label": item_ko, "grams_co2e": round(g, 1), "source": f["source"]}


def menu(menu_ko):
    """학식 메뉴명 → 레시피 전개 → 식재료별 합산 (데모 핵심 경로)"""
    if menu_ko not in RECIPES:
        return None
    items = [food_item(i, g) for i, g in RECIPES[menu_ko]]
    items = [x for x in items if x]
    return _bundle(menu_ko, items)


def energy_transport_item(item_ko, amount):
    """전력(kWh)·교통(인-km): 활동량 × 계수 → gCO2e"""
    f = ENERGY_TRANSPORT.get(item_ko)
    if not f:
        return None
    g = amount * float(f["factor_kgco2e_per_unit"]) * 1000.0
    return {"label": item_ko, "grams_co2e": round(g, 1),
            "unit": f["unit"], "source": f["source"]}


def _bundle(name, items):
    total = round(sum(i["grams_co2e"] for i in items), 1)
    return {"name": name, "total_grams_co2e": total, "breakdown": items,
            "sources": sorted({i["source"] for i in items})}


def compute(activities):
    """
    전체 입력 묶음 처리. activities = classify LLM 출력.
    각 원소: {"type": "menu"|"food"|"energy"|"transport", "name"/"item", "amount"/"grams"}
    """
    results = []
    for a in activities:
        t = a.get("type")
        if t == "menu":
            r = menu(a["name"])
        elif t == "food":
            r = food_item(a["item"], a["grams"])
        elif t in ("energy", "transport"):
            r = energy_transport_item(a["item"], a["amount"])
        else:
            r = None
        if r:
            results.append(r)
    total = round(sum(r.get("total_grams_co2e", r.get("grams_co2e", 0))
                      for r in results), 1)
    return {"total_grams_co2e": total, "items": results}


if __name__ == "__main__":
    # 데모: 학식 식단 사진 → "제육덮밥"으로 분류됐다고 가정
    demo = compute([{"type": "menu", "name": "제육덮밥"}])
    print(f"제육덮밥 총 배출: {demo['total_grams_co2e']} gCO2e")
    for it in demo["items"][0]["breakdown"]:
        print(f"  - {it['label']}: {it['grams_co2e']} g  ({it['source']})")
    # 비교: 비건비빔밥
    veg = compute([{"type": "menu", "name": "비건비빔밥"}])
    print(f"\n비건비빔밥: {veg['total_grams_co2e']} gCO2e "
          f"(절감 {demo['total_grams_co2e'] - veg['total_grams_co2e']:.0f} g)")
