"""코칭 lane 스모크 — coach() 를 MOCK(규칙기반)으로 검증 (AWS 불필요).

사용: MOCK=1 python3 terra_ai/scripts/smoke_coach.py   (PASS면 exit 0)
계약: docs/CONTRACT.md §2-A 보조 — coach(result, user_dept) → {planet_line, next_action, expected_saving_grams, tone}.
숫자는 코드(best_alternative), 문장만 Sonnet(여기선 MOCK→규칙기반).
"""
import os
import sys
import pathlib

os.environ["MOCK"] = "1"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from terra_ai.bedrock.coach import coach

fails = []


def check(name, cond):
    print(f"  {'✅' if cond else '❌'} {name}")
    if not cond:
        fails.append(name)


# 1) 대안 있음(high tier) → 4필드 + 절감량은 코드값 그대로
r = coach(
    {"total_grams_co2e": 6021.0, "tier": "high",
     "best_alternative": {"name": "비건비빔밥", "grams_co2e": 285.0, "saving_grams": 5736.0}},
    "컴퓨터공학과",
)
check("계약 4필드 존재",
      set(r) == {"planet_line", "next_action", "expected_saving_grams", "tone"})
check("expected_saving_grams = best_alternative.saving_grams(코드값)",
      r["expected_saving_grams"] == 5736.0)
check("tone(high)=gentle", r["tone"] == "gentle")
check("문장 비어있지 않음", bool(r["planet_line"]) and bool(r["next_action"]))
check("next_action에 대안 메뉴 반영", "비건비빔밥" in r["next_action"])

# 2) 대안 없음(이미 최저) → 절감량 0 + 유지 권유
r2 = coach({"total_grams_co2e": 285.0, "tier": "low"}, "기계공학과")
check("대안 없음 → expected_saving_grams=0", r2["expected_saving_grams"] == 0)
check("tone(low)=celebratory", r2["tone"] == "celebratory")
check("문장 형식 유지", bool(r2["planet_line"]) and bool(r2["next_action"]))

# 3) 숫자 무결성 — coach는 절감량을 새로 만들지 않음(환각 차단)
check("절감량은 입력 result에서만 파생", r["expected_saving_grams"] == 5736.0)

print(f"\n{'전부 PASS ✅' if not fails else f'실패 {len(fails)}건: {fails}'}")
sys.exit(1 if fails else 0)
