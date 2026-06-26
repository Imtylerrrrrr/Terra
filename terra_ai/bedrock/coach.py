"""
코칭 — best_alternative(코드 계산) + Bedrock Sonnet(개인화 문장).
설계: 숫자는 코드가 계산(환각0), Sonnet은 받은 숫자로 문장만. 라우팅=Sonnet(코칭만, 저전력).
입력: resolve.py 출력(하루 items+total). 출력: coach.md 스키마(planet_line·next_action·saving).
MOCK=1 또는 Bedrock 미연결 → 규칙기반 문장(개발용).
"""
import os
import re
import json
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT.parent))
from terra_ai.engine.carbon_engine import menu, RECIPES

SYSTEM = (ROOT / "prompts" / "coach.md").read_text(encoding="utf-8")
# ⚠️ Bedrock 정식 ID는 리전/클라이언트별로 다를 수 있음(날짜·버전·추론프로파일) → 환경변수로 주입
SONNET = os.environ.get("TERRA_COACH_MODEL", "anthropic.claude-sonnet-4-6")
REGION = os.environ.get("AWS_REGION", "us-east-1")


def best_alternative(items):
    """먹은 메뉴 → 가장 저탄소 메뉴 대안 + 절감량 (코드 계산, 결정적)."""
    eaten = next((i for i in items if i["type"] == "menu"), None)
    if not eaten:
        return None
    opts = {m: menu(m)["total_grams_co2e"] for m in RECIPES}
    best = min(opts, key=opts.get)
    saving = round(eaten["grams_co2e"] - opts[best], 1)
    if saving <= 0:
        return None   # 이미 최저
    return {"name": best, "grams_co2e": opts[best], "saving_grams": saving}


def _parse_json(text):
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0)) if m else {}


def _sonnet(payload):
    from anthropic import AnthropicBedrockMantle
    client = AnthropicBedrockMantle(aws_region=REGION)
    resp = client.messages.create(
        model=SONNET, max_tokens=512, system=SYSTEM,
        messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
    )
    return _parse_json(next(b.text for b in resp.content if b.type == "text"))


def _ro(word):
    """조사 '(으)로' — 받침 없음/ㄹ받침이면 '로', 그 외 '으로'."""
    last = word[-1]
    if "가" <= last <= "힣" and (ord(last) - 0xAC00) % 28 in (0, 8):
        return word + "로"
    return word + "으로"


def _mock(payload):
    """규칙기반 폴백 — Sonnet 없이도 동일 스키마."""
    alt = payload["best_alternative"]
    if not alt:
        return {"planet_line": "오늘 우리 학과 행성이 안정적이야 🌱",
                "next_action": "이대로 유지해줘.", "expected_saving_grams": 0, "tone": "encouraging"}
    kg = alt["saving_grams"] / 1000
    return {"planet_line": "오늘 행성의 숲이 조금 옅어졌어 🌱 내일이 있어.",
            "next_action": f"내일 한 끼를 {_ro(alt['name'])} 바꾸면 약 {kg:.1f}kg 줄어들어.",
            "expected_saving_grams": alt["saving_grams"], "tone": "encouraging"}


def coach(resolved, user_dept="우리 학과"):
    """resolve.py 출력 → 코칭 JSON (coach.md 스키마)."""
    items = resolved["items"]
    payload = {
        "today_grams_co2e": resolved["total_grams_co2e"],
        "breakdown": [{"label": i["label"], "grams_co2e": i["grams_co2e"]} for i in items],
        "best_alternative": best_alternative(items),
        "user_dept": user_dept,
    }
    if os.environ.get("MOCK") == "1":
        return _mock(payload)
    try:
        return _sonnet(payload)
    except Exception as e:
        print(f"[Sonnet 실패 → 규칙기반 폴백] {e}")
        return _mock(payload)


if __name__ == "__main__":
    os.environ["MOCK"] = "1"
    from terra_ai.resolve import resolve
    day = [{"type": "menu", "name": "소불고기정식"},
           {"type": "digital", "item": "엔터테인먼트", "hours": 2},
           {"type": "energy", "item": "전력_KEITI", "kwh": 1.5}]
    out = coach(resolve(day), user_dept="컴퓨터공학과")
    print(json.dumps(out, ensure_ascii=False, indent=2))
