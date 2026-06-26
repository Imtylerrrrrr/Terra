"""
Terra 코칭 문장 생성 — best_alternative(코드 계산)를 사람 말투 코칭으로.
계약: docs/CONTRACT.md §2-A 보조 — coach(result, user_dept) → {planet_line, next_action, expected_saving_grams, tone}

설계(계약 명시): 숫자(절감량·tier)는 **코드**, 문장(planet_line·next_action)만 **Claude Sonnet**.
라이브 API가 없거나(MOCK=1) 실패하면 **규칙기반 폴백** — 데모는 항상 동작.
best_alternative 는 엔진(주영)이 이미 계산 → coach 는 숫자를 새로 만들지 않는다(환각 차단).

⚠️ 대회 Bedrock 불가 → Anthropic 직접 API. 인증=환경변수 ANTHROPIC_API_KEY.
모델 라우팅(extract=Haiku 와 분리): 코칭=Claude Sonnet 4.6 (claude-sonnet-4-6).
  모델 변경 시 TERRA_COACH_MODEL 로 오버라이드.
"""
import json
import os
import re
import sys

try:   # 도감 넛지(누적 절감→다음 해금). 모노레포 패키지 경유
    from terra_ai.gamify import next_milestone
except ModuleNotFoundError:   # Lambda(CodeUri=terra_ai/): 형제 패키지로
    try:
        from gamify import next_milestone
    except ModuleNotFoundError:
        next_milestone = None

SONNET = os.environ.get("TERRA_COACH_MODEL", "claude-sonnet-4-6")

# tier → 톤 라벨(코드 결정 · 프론트 코칭 화면 스타일 분기용)
_TONE = {"low": "celebratory", "mid": "encouraging", "high": "gentle"}

SYSTEM = (
    "너는 캠퍼스 탄소 다이어트 코치다. 따뜻하고 짧게, 죄책감 주지 말고 격려해.\n"
    "주어진 사실(tier·총배출·대안 메뉴·절감량)만 사용하고 숫자를 새로 지어내지 마.\n"
    '반드시 JSON 하나만 출력: {"planet_line": "...", "next_action": "..."} — 설명·코드펜스 금지.\n'
    "planet_line=행성 상태 한 줄, next_action=구체적 다음 행동 한 줄. 한국어 반말, 각 40자 이내."
)


def _client():
    """Anthropic Claude API 클라이언트 (api_key=환경변수 ANTHROPIC_API_KEY 자동 인식)."""
    from anthropic import Anthropic
    return Anthropic()


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


def _milestone_nudge(cumulative_saving_grams):
    """누적 절감(gCO2e) → 다음 도감 해금까지 넛지 한 줄. 숫자=코드(next_milestone).

    카탈로그 미탑재(import 실패)·전종 해금이면 '' (넛지 없음).
    잔여량은 적응 표기(1kg 미만은 g), 복수 해금은 "OO 등 N종"으로 정확히 알림.
    """
    if next_milestone is None:
        return ""
    nm = next_milestone(cumulative_saving_grams)
    if not nm:
        return ""
    rem = nm["remaining_grams"]
    amount = f"{rem:.0f}g" if rem < 1000 else f"{rem / 1000:.1f}kg"
    species = f"{nm['name']} 등 {nm['count']}종" if nm.get("count", 1) > 1 else nm["name"]
    return f"앞으로 {amount} 더 줄이면 {species} 해금!"


def coach(result, user_dept="우리 학과", cumulative_saving_grams=None):
    """PersonalResult(§2-A) → 코칭 {planet_line, next_action, expected_saving_grams, tone}.

    숫자는 result(코드 계산)에서만 — expected_saving_grams = best_alternative.saving_grams.
    문장은 Sonnet 생성(실패·MOCK=1 → 규칙기반).
    cumulative_saving_grams 주면 다음 도감 해금 넛지를 next_action에 결정적으로 덧붙임(숫자=코드).
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
            # 폴백=규칙기반 (라이브 API 부재/실패 시 데모 보호).
            # silent 금지 — 라이브 경로가 가려지지 않게 stderr 경고 1줄(검증·디버깅용).
            print(f"[coach] Sonnet 호출 실패 → 규칙기반 폴백: {type(e).__name__}: {e}", file=sys.stderr)

    if cumulative_saving_grams is not None:
        nudge = _milestone_nudge(cumulative_saving_grams)
        if nudge:
            action = f"{action} {nudge}"

    return {
        "planet_line": planet,
        "next_action": action,
        "expected_saving_grams": round(saving, 1),
        "tone": tone,
    }


if __name__ == "__main__":
    # MOCK=1 python3 terra_ai/bedrock/coach.py  로 규칙기반 흐름 확인
    # standalone 실행 시 terra_ai 패키지 경로 확보(넛지 import용)
    import pathlib
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
    from terra_ai.gamify import next_milestone  # noqa: F811  (None이었으면 재바인딩)
    demo = {
        "total_grams_co2e": 6021.0,
        "tier": "high",
        "best_alternative": {"name": "비건비빔밥", "grams_co2e": 285.0, "saving_grams": 5736.0},
    }
    # cumulative_saving_grams=1800 → 다음 해금(2kg=무산쇠족제비)까지 0.2kg 넛지
    print(json.dumps(coach(demo, "컴퓨터공학과", cumulative_saving_grams=1800), ensure_ascii=False, indent=2))
