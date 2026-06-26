"""
Terra 코칭 문장 생성 — best_alternative(코드 계산)를 사람 말투 코칭으로.
계약: docs/CONTRACT.md §2-A 보조 — coach(result, user_dept) → {planet_line, next_action, expected_saving_grams, tone}

설계(계약 명시): 숫자(절감량·tier)는 **코드**, 문장(planet_line·next_action)만 **Bedrock Sonnet**.
라이브 Bedrock이 없거나(MOCK=1) 실패하면 **규칙기반 폴백** — 데모는 항상 동작.
best_alternative 는 엔진(주영)이 이미 계산 → coach 는 숫자를 새로 만들지 않는다(환각 차단).

모델 라우팅(extract=Haiku 와 분리): 코칭=Claude Sonnet 4.6.
  주영이 환경에 맞는 ID를 TERRA_COACH_MODEL 로 주입(예: us.anthropic.claude-sonnet-4-6-...).
"""
import json
import os
import re
import sys

SONNET = os.environ.get("TERRA_COACH_MODEL", "anthropic.claude-sonnet-4-6")
REGION = os.environ.get("AWS_REGION", "us-east-1")

# tier → 톤 라벨(코드 결정 · 프론트 코칭 화면 스타일 분기용)
_TONE = {"low": "celebratory", "mid": "encouraging", "high": "gentle"}

SYSTEM = (
    "너는 캠퍼스 탄소 다이어트 코치다. 따뜻하고 짧게, 죄책감 주지 말고 격려해.\n"
    "주어진 사실(tier·총배출·대안 메뉴·절감량)만 사용하고 숫자를 새로 지어내지 마.\n"
    '반드시 JSON 하나만 출력: {"planet_line": "...", "next_action": "..."} — 설명·코드펜스 금지.\n'
    "planet_line=행성 상태 한 줄, next_action=구체적 다음 행동 한 줄. 한국어 반말, 각 40자 이내."
)


def _client():
    """Bedrock 클라이언트 (anthropic SDK, Messages API, 주영의 AWS 자격증명)."""
    from anthropic import AnthropicBedrock
    return AnthropicBedrock(aws_region=REGION)


def _rule_based(total, tier, alt, saving, dept):
    """규칙기반 폴백 — 라이브 Sonnet 없이도 계약 형식 문장 보장."""
    if tier == "low":
        planet = f"🌳 {dept} 행성에 숲이 우거졌어 — 오늘 {total:.0f}g, 아주 좋아."
    elif tier == "high":
        planet = f"🌫️ {dept} 행성에 안개가 꼈어 — 오늘 {total:.0f}g, 같이 줄여보자."
    else:
        planet = f"🌱 {dept} 행성이 회복 중 — 오늘 {total:.0f}g."
    if alt and saving > 0:
        action = f"다음 끼니를 {alt}(으)로 바꾸면 약 {saving:.0f}g 줄일 수 있어."
    else:
        action = "지금처럼 가벼운 선택을 이어가면 돼 — 좋은 흐름이야."
    return planet, action


def _parse(text):
    """Sonnet 응답에서 두 문장만 안전 추출(코드펜스 제거). 실패 시 None → 폴백."""
    text = re.sub(r"```(?:json)?|```", "", text)
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        return d.get("planet_line"), d.get("next_action")
    except json.JSONDecodeError:
        return None


def coach(result, user_dept="우리 학과"):
    """PersonalResult(§2-A) → 코칭 {planet_line, next_action, expected_saving_grams, tone}.

    숫자는 result(코드 계산)에서만 — expected_saving_grams = best_alternative.saving_grams.
    문장은 Sonnet 생성(실패·MOCK=1 → 규칙기반).
    """
    total = float(result.get("total_grams_co2e", 0) or 0)
    tier = result.get("tier", "mid")
    alt_obj = result.get("best_alternative") or {}
    alt = alt_obj.get("name")
    saving = float(alt_obj.get("saving_grams", 0) or 0)
    tone = _TONE.get(tier, "encouraging")

    planet, action = _rule_based(total, tier, alt, saving, user_dept)

    if os.environ.get("MOCK") != "1":
        try:
            facts = (
                f"학과={user_dept}, tier={tier}, 총배출={total:.0f}g, "
                f"대안메뉴={alt or '없음'}, 절감량={saving:.0f}g"
            )
            resp = _client().messages.create(
                model=SONNET,
                max_tokens=300,
                system=SYSTEM,
                messages=[{"role": "user", "content": f"사실: {facts}\n위 사실로 코칭 JSON을 만들어."}],
            )
            text = next((b.text for b in resp.content if b.type == "text"), "")
            parsed = _parse(text)
            if parsed and parsed[0] and parsed[1]:
                planet, action = parsed
        except Exception as e:
            # 폴백=규칙기반 (라이브 Bedrock 부재/실패 시 데모 보호).
            # silent 금지 — 라이브 경로가 가려지지 않게 stderr 경고 1줄(검증·디버깅용).
            print(f"[coach] Sonnet 호출 실패 → 규칙기반 폴백: {type(e).__name__}: {e}", file=sys.stderr)

    return {
        "planet_line": planet,
        "next_action": action,
        "expected_saving_grams": round(saving, 1),
        "tone": tone,
    }


if __name__ == "__main__":
    # MOCK=1 python3 terra_ai/bedrock/coach.py  로 규칙기반 흐름 확인
    demo = {
        "total_grams_co2e": 6021.0,
        "tier": "high",
        "best_alternative": {"name": "비건비빔밥", "grams_co2e": 285.0, "saving_grams": 5736.0},
    }
    print(json.dumps(coach(demo, "컴퓨터공학과"), ensure_ascii=False, indent=2))
