"""coach 엔드포인트 핸들러 스모크 — handler() 를 MOCK(규칙기반)으로 검증 (AWS 불필요).

사용: MOCK=1 python3 terra_ai/scripts/smoke_coach_handler.py   (PASS면 exit 0)
계약: POST /coach {result, user_dept?, cumulative_saving_grams?}
      → 200 {planet_line, next_action, expected_saving_grams, tone} | 400 {error}
"""
import json
import os
import pathlib
import sys

os.environ["MOCK"] = "1"
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from terra_ai.api.coach_handler import handler

fails = []


def check(name, cond):
    print(f"  {'✅' if cond else '❌'} {name}")
    if not cond:
        fails.append(name)


def call(body):
    resp = handler({"body": json.dumps(body, ensure_ascii=False)})
    return resp["statusCode"], json.loads(resp["body"])


# 1) 정상 — high tier + 대안 → 200, 계약 4필드, 절감량은 코드값 그대로
st, r = call({
    "result": {"total_grams_co2e": 6021.0, "tier": "high",
               "best_alternative": {"name": "비건비빔밥", "grams_co2e": 285.0, "saving_grams": 5736.0}},
    "user_dept": "컴퓨터공학과",
})
check("정상 200", st == 200)
check("계약 4필드", set(r) == {"planet_line", "next_action", "expected_saving_grams", "tone"})
check("expected_saving_grams=코드값(5736)", r.get("expected_saving_grams") == 5736.0)
check("tone(high)=gentle", r.get("tone") == "gentle")
check("next_action에 대안 반영", "비건비빔밥" in r.get("next_action", ""))

# 2) 넛지 — cumulative 주면 next_action에 다음 해금 결정적 추가
st2, r2 = call({
    "result": {"total_grams_co2e": 1050.0, "tier": "mid",
               "best_alternative": {"name": "비건비빔밥", "grams_co2e": 285.0, "saving_grams": 765.0}},
    "user_dept": "컴퓨터공학과",
    "cumulative_saving_grams": 200,
})
check("넛지 200", st2 == 200)
check("넛지: '여우'+'4종' 포함", "여우" in r2.get("next_action", "") and "4종" in r2.get("next_action", ""))

# 3) result 누락 → 400 bad_request
st3, r3 = call({"user_dept": "기계공학과"})
check("result 누락 → 400", st3 == 400)
check("400 에러 형식", "error" in r3 and r3["error"].get("code") == "bad_request")

# 4) cumulative 비숫자 → 400
st4, r4 = call({
    "result": {"total_grams_co2e": 285.0, "tier": "low"},
    "cumulative_saving_grams": "abc",
})
check("cumulative 비숫자 → 400", st4 == 400)

# 5) invalid JSON → 400 invalid_json
resp = handler({"body": "{not json"})
check("깨진 JSON → 400 invalid_json",
      resp["statusCode"] == 400 and json.loads(resp["body"])["error"]["code"] == "invalid_json")

print(f"\n{'전부 PASS ✅' if not fails else f'실패 {len(fails)}건: {fails}'}")
sys.exit(1 if fails else 0)
