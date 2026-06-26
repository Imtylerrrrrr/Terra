"""
스모크 테스트 — AI/데이터 파이프라인 전체를 MOCK으로 1회 검증 (AWS 불필요).
사용: python3 terra_ai/scripts/smoke_test.py   (전부 PASS면 exit 0)
라이브 Bedrock/KB 검증은 별도(주영) — 이건 로직·데이터 무결성 가드.
"""
import os
import sys
import pathlib

os.environ["MOCK"] = "1"
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))

from terra_ai.resolve import resolve
from terra_ai.bedrock.coach import coach
from terra_ai.bedrock.match import match_product
from terra_ai.screentime import to_activities
from terra_ai.engine.carbon_engine import menu, RECIPES

fails = []

def check(name, cond):
    print(f"  {'✅' if cond else '❌'} {name}")
    if not cond:
        fails.append(name)

# 1) 4종 통합 resolve
day = [{"type": "menu", "name": "제육덮밥"},
       {"type": "digital", "item": "엔터테인먼트", "hours": 2},
       {"type": "product", "item": "진라면순한맛", "qty": 2},
       {"type": "energy", "item": "전력_KEITI", "kwh": 1.5}]
out = resolve(day)
check("resolve 4종 합산 > 0", out["total_grams_co2e"] > 0)
check("by_type에 4종 모두", set(out["by_type"]) == {"menu", "digital", "product", "energy"})

# 2) 신규 메뉴 전부 계산됨
new_menus = ["비빔밥", "돈까스", "카레라이스", "라면", "김밥", "샐러드", "치즈버거"]
check("신규 메뉴 7종 레시피 존재", all(m in RECIPES for m in new_menus))
check("신규 메뉴 전부 양수 배출", all(menu(m)["total_grams_co2e"] > 0 for m in new_menus))

# 3) 코칭
c = coach(out, user_dept="컴퓨터공학과")
check("coach 스키마 키", all(k in c for k in ("planet_line", "next_action", "expected_saving_grams")))

# 4) 스크린타임 매핑
acts = to_activities([{"package": "com.google.android.youtube", "minutes": 60},
                      {"package": "com.unknown.x", "minutes": 30}])
check("screentime 앱→버킷", any(a["item"] == "엔터테인먼트" for a in acts))

# 5) 영수증 매칭
m = match_product("진라면순한맛")
check("영수증 퍼지매칭", m["matched"] is not None and m["grams_co2e"] > 0)

# 6) 견고성 — 잘못된 항목 격리(크래시 없음)
r = resolve([{"type": "food", "item": "돼지고기"}])  # grams 누락
check("malformed 항목 격리", r["items"][0].get("needs_review") is True)

print(f"\n{'전부 PASS ✅' if not fails else f'실패 {len(fails)}건: {fails}'}")
sys.exit(1 if fails else 0)
