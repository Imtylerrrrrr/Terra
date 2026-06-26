"""
통합 계수 해소 (계수 매핑 레인) — 입력 4종 activities(CONTRACT §1) → 항목별 gCO2e + 합계.

각 type을 알맞은 계수 소스로 라우팅:
  menu/food/energy → carbon_engine   (식단·전력)
  product          → retrieve.resolve (영수증, KB 하이브리드 / 폴백=코드매칭)
  digital          → digital_factors  (스크린타임, 시간×계수)

출력은 CONTRACT §2 형태. tier·학과/캠퍼스 집계·저장은 주영(엔진/Lambda)이 이 결과로 처리.
스크린타임 시간→gCO2e 계산도 여기서 닫힘(이전엔 어디서도 안 했음).
"""
import csv
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))
from terra_ai.engine.carbon_engine import menu, food_item, energy_transport_item
from terra_ai.bedrock.retrieve import resolve as resolve_product

DATA = ROOT / "data"
_DIG = {r["activity_ko"]: (float(r["factor_gco2e_per_unit"]), r["source"])
        for r in csv.DictReader(open(DATA / "digital_factors.csv", encoding="utf-8"))}


def _one(a):
    t = a.get("type")
    if t == "menu":
        r = menu(a["name"])
        if not r:
            return None
        return {"type": t, "label": r["name"], "grams_co2e": r["total_grams_co2e"],
                "source": "; ".join(r["sources"]), "breakdown": r["breakdown"]}
    if t == "food":
        r = food_item(a["item"], a["grams"])
        return {"type": t, "label": r["label"], "grams_co2e": r["grams_co2e"],
                "source": r["source"]} if r else None
    if t == "energy":
        amt = a.get("kwh", a.get("amount", 0))
        r = energy_transport_item(a["item"], amt)
        return {"type": t, "label": r["label"], "grams_co2e": r["grams_co2e"],
                "source": r["source"]} if r else None
    if t == "product":
        r = resolve_product(a["item"], a.get("qty", 1))
        return {"type": t, "label": r["label"], "grams_co2e": r["grams_co2e"],
                "source": r["source"], "matched": r.get("matched"),
                "needs_review": r.get("needs_review", False)}
    if t == "digital":
        f = _DIG.get(a["item"])
        if not f:
            return {"type": t, "label": a["item"], "grams_co2e": 0,
                    "source": "미등록", "needs_review": True}
        g = round(f[0] * float(a.get("hours", 0)), 1)
        return {"type": t, "label": a["item"], "grams_co2e": g, "source": f[1]}
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
    import os, json
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
