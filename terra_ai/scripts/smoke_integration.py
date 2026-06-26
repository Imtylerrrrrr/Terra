"""추출↔엔진 이음새 통합 스모크 — /extract 출력 → 주영 compute() 입력 (MOCK, AWS 불필요).

계약 §1(추출 ExtractionResult) → §2-A(PersonalResult) **구조 정합**을 검증한다.
계수 '값'과 무관하게 두 레인이 맞물리는지만 본다(값은 PR #23, 형식은 docs/CONTRACT.md).

사용: python3 terra_ai/scripts/smoke_integration.py   (PASS면 exit 0)
"""
import json
import os
import sys
import pathlib

os.environ["MOCK"] = "1"
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent  # repo root
sys.path.insert(0, str(ROOT))             # terra_ai 패키지 (추출)
sys.path.insert(0, str(ROOT / "backend"))  # carbon_engine (엔진, 주영)

from terra_ai.api.extract_handler import handler
from carbon_engine import compute

CONTRACT_TYPES = {"menu", "food", "purchase", "screentime", "energy"}
fails = []


def check(name, cond):
    print(f"  {'✅' if cond else '❌'} {name}")
    if not cond:
        fails.append(name)


# 1) /extract → §1 activities
r = handler({"body": json.dumps({"text": "학식: 제육볶음, 밥"})})
ext = json.loads(r["body"])
check("extract 200 + activities", r["statusCode"] == 200 and bool(ext.get("activities")))

# 2) 그 출력을 그대로 compute()에 투입 → §2-A 유효 결과
res = compute(ext, "u_demo", "cs")
check("compute total_grams_co2e 수치", isinstance(res.get("total_grams_co2e"), (int, float)))
check("compute tier 유효", res.get("tier") in {"low", "mid", "high"})
check("items 구조", isinstance(res.get("items"), list) and len(res["items"]) > 0)

# 3) 계약 §1 5-type 전체를 추출 형태로 넣어도 엔진이 소화 (seed 존재 키 사용)
full = {"activities": [
    {"type": "menu",       "name": "소불고기덮밥"},
    {"type": "food",       "item": "쌀밥", "grams": 210},
    {"type": "purchase",   "item": "아메리카노", "qty": 1},
    {"type": "screentime", "item": "스마트폰", "minutes": 300},
    {"type": "energy",     "item": "전력_가정용체감", "kwh": 1.5},
], "needs_review": False}
check("5-type 전부 계약 범위", {a["type"] for a in full["activities"]} <= CONTRACT_TYPES)
res2 = compute(full, "u_demo", "me")
check("5-type 합산 > 0", res2["total_grams_co2e"] > 0)
check("소불고기덮밥 = high tier (킬샷)", res2["tier"] == "high")

print(f"\n{'이음새 PASS ✅' if not fails else f'실패 {len(fails)}건: {fails}'}")
sys.exit(1 if fails else 0)
