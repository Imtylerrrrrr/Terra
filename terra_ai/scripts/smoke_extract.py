"""추출 lane 스모크 — POST /extract 핸들러를 MOCK으로 1회 검증 (AWS 불필요).

사용: MOCK=1 python3 terra_ai/scripts/smoke_extract.py   (PASS면 exit 0)
민지 레인 = 추출(/extract) + 정식계수 공급(backend factors.seed.json). 계산은 엔진(주영).
"""
import json
import os
import sys
import pathlib

os.environ["MOCK"] = "1"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from terra_ai.api.extract_handler import handler

CONTRACT_TYPES = {"menu", "food", "purchase", "screentime", "energy"}
fails = []


def check(name, cond):
    print(f"  {'✅' if cond else '❌'} {name}")
    if not cond:
        fails.append(name)


# 1) 텍스트 입력 → 200 + activities
r = handler({"body": json.dumps({"text": "학식: 제육볶음, 밥, 김치"})})
body = json.loads(r["body"])
check("POST /extract 200", r["statusCode"] == 200)
check("activities 존재", isinstance(body.get("activities"), list) and len(body["activities"]) > 0)

# 2) 출력 타입이 계약 §1 범위
types = {a.get("type") for a in body["activities"]}
check("타입이 계약 범위(menu/food/purchase/screentime/energy)", types <= CONTRACT_TYPES)

# 3) 빈 본문 → 400
e = handler({"body": "{}"})
check("빈 본문 400", e["statusCode"] == 400)

# 4) fixture 폴백 (라이브·AWS 없이 결정적)
fr = handler({"body": json.dumps({"fixture": "소불고기덮밥"})})
fb = json.loads(fr["body"])
check("fixture 폴백 200+해당메뉴",
      fr["statusCode"] == 200 and fb["activities"][0].get("name") == "소불고기덮밥")

print(f"\n{'전부 PASS ✅' if not fails else f'실패 {len(fails)}건: {fails}'}")
sys.exit(1 if fails else 0)
