"""
factors.json 빌더 — 민지 레인의 계수 CSV들을 단일 JSON(팀/Lambda 단일 자산)으로 합침.
원칙: CSV가 사람이 편집하는 원천, data/factors.json은 런타임/핸드오프 산출물.
CSV 수정 후: python3 terra_ai/scripts/build_factors.py 로 재생성.
app_categories는 계수가 아니라 라우팅 매핑이지만, 단일 자산 핸드오프를 위해 별도 섹션으로 포함(screentime.py가 사용).
"""
import csv
import json
import pathlib
from collections import defaultdict
from datetime import date

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def _rows(name):
    with open(DATA / name, encoding="utf-8") as f:
        return list(csv.DictReader(f))


food = {r["item_ko"]: {
            "factor_kgco2e_per_kg": float(r["factor_kgco2e_per_kg"]),
            "category": r["category"], "item_en": r["item_en"],
            "source": r["source"], "verify": r["verify"]}
        for r in _rows("food_factors.csv")}

energy_transport = {r["item_ko"]: {
            "unit": r["unit"],
            "factor_kgco2e_per_unit": float(r["factor_kgco2e_per_unit"]),
            "domain": r["domain"], "item_en": r["item_en"],
            "source": r["source"], "verify": r["verify"]}
        for r in _rows("energy_transport_factors.csv")}

menu_recipes = defaultdict(list)
for r in _rows("menu_recipes.csv"):
    menu_recipes[r["menu_ko"]].append(
        {"item": r["ingredient_item"], "grams": float(r["grams"])})

digital = {r["activity_ko"]: {
            "unit": r["unit"],
            "factor_gco2e_per_unit": float(r["factor_gco2e_per_unit"]),
            "mode": r["mode"], "source": r["source"], "verify": r["verify"]}
        for r in _rows("digital_factors.csv")}

product = [{
            "item_ko": r["item_ko"], "category": r["category"],
            "factor_kgco2e_per_unit": float(r["factor_kgco2e_per_unit"]),
            "unit": r["unit"], "source": r["source"], "verify": r["verify"]}
        for r in _rows("product_factors.csv")]

# 계수가 아닌 라우팅 맵(패키지→버킷). 단일 자산을 위해 별도 섹션으로 포함.
app_categories = {r["package"]: {"app_ko": r["app_ko"], "bucket": r["bucket"]}
                  for r in _rows("app_categories.csv")}

factors = {
    "meta": {
        "version": "v2",
        "owner": "민지 (AI·데이터 레인)",
        "principle": "숫자는 공공데이터, 계산은 코드 (LLM 산수 금지)",
        "built": str(date.today()),
        "built_from": ["food_factors.csv", "energy_transport_factors.csv",
                       "menu_recipes.csv", "digital_factors.csv", "product_factors.csv",
                       "app_categories.csv"],
        "tier_thresholds_gco2e": {"low_max": 700, "high_min": 2500},
        "note": "CSV가 원천. 수정 후 scripts/build_factors.py로 재생성.",
    },
    "food": food,
    "energy_transport": energy_transport,
    "menu_recipes": dict(menu_recipes),
    "digital": digital,
    "product": product,
    "app_categories": app_categories,
}

out = DATA / "factors.json"
out.write_text(json.dumps(factors, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"factors.json 생성 → food {len(food)} · energy_transport {len(energy_transport)} "
      f"· menu {len(menu_recipes)} · digital {len(digital)} · product {len(product)} "
      f"· app_categories {len(app_categories)}")
