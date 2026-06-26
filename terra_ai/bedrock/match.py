"""
영수증 품목 매칭 — OCR(Bedrock 비전)이 읽은 messy 품목명을
product_factors.csv(KEITI EPD 정식 품목명)에 매핑해 gCO2e 산출.

설계: **코드 기반 퍼지매칭**(결정적·환각 차단). 작은 표(28품목)엔 의미검색보다 우수.
흐름: extract.py(product activities) → match.py → 그램값 → 엔진 합산.
미매칭은 카테고리 평균(추정) + needs_review=True (정직 처리).
"""
import json
import re
import pathlib
from difflib import SequenceMatcher
from collections import defaultdict

DATA = pathlib.Path(__file__).resolve().parent.parent / "data"

PRODUCTS = json.loads((DATA / "factors.json").read_text(encoding="utf-8"))["product"]  # 단일 진실

# 브랜드/판매처 접두어·용량·괄호 제거 → 핵심 품명만 비교
_VENDOR = re.compile(r"유어스\)?|노브랜드|광동|오늘의차|스카트|크리넥스|t스탠다드|보솜이", re.I)
_UNIT = re.compile(r"\d+\s*(ml|g|매|개|l|kg|t|x\d+)?", re.I)
_STOP = re.compile(r"pet|대컵|컵|리필형|캡형|휴대형|온라인|e-?pack|뉴", re.I)

def norm(s):
    s = _VENDOR.sub("", s)
    s = _STOP.sub("", s)
    s = _UNIT.sub("", s)
    s = re.sub(r"[\[\](){}·,\.\s\-_]", "", s)
    return s.lower()

def _score(a, b):
    na, nb = norm(a), norm(b)
    if not na or not nb:
        return 0.0
    ratio = SequenceMatcher(None, na, nb).ratio()
    if na in nb or nb in na:          # 포함이면 우대하되, 동점은 가까운(짧은) 품명이 이김
        return 0.8 + 0.2 * ratio
    return ratio

_BY_CAT = defaultdict(list)
for _r in PRODUCTS:
    _BY_CAT[_r["category"]].append(float(_r["factor_kgco2e_per_unit"]))
_ALL_MEAN = sum(float(r["factor_kgco2e_per_unit"]) for r in PRODUCTS) / len(PRODUCTS)

def match_product(name, qty=1, krw=None, threshold=0.6):
    """messy 품목명 → {grams_co2e, matched, source, needs_review}."""
    best, bs = None, 0.0
    for r in PRODUCTS:
        s = _score(name, r["item_ko"])
        if s > bs:
            best, bs = r, s
    if best and bs >= threshold:
        g = float(best["factor_kgco2e_per_unit"]) * 1000 * qty
        return {"label": name, "matched": best["item_ko"], "grams_co2e": round(g, 1),
                "source": best["source"], "method": f"fuzzy({bs:.2f})", "needs_review": False}
    # 미매칭 → 전체 평균 추정(정직 표기)
    return {"label": name, "matched": None, "grams_co2e": round(_ALL_MEAN * 1000 * qty, 1),
            "source": "product_factors 평균(추정)", "method": "fallback_mean", "needs_review": True}

def match_receipt(activities):
    """extract.py의 product activities 리스트 → 매칭 결과 + 합계."""
    out = [match_product(a["item"], a.get("qty", 1), a.get("krw")) for a in activities]
    return {"total_grams_co2e": round(sum(o["grams_co2e"] for o in out), 1), "items": out}


if __name__ == "__main__":
    # 실제 영수증 OCR처럼 messy하게 넣어 매칭 검증
    tests = ["진라면순한맛", "오모리김치찌개라면", "옥수수수염차500", "지리산샘물 500ml",
             "공화춘 자장", "물티슈100매", "아이스아메리카노"]  # 마지막은 미수록→fallback
    for t in tests:
        r = match_product(t)
        tag = r["matched"] or "—(추정)"
        print(f"  {t:18s} → {tag[:28]:28s} {r['grams_co2e']:7.1f}g  [{r['method']}]")
