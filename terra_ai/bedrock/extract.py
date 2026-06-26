"""
Terra 입력 해석 — Claude API(Anthropic) 멀티모달로 식판/영수증/이동을 품목·수량 JSON으로.
설계: 해석만 LLM, 숫자(탄소)는 안 만든다 → CONTRACT.md §1 스키마로 출력 → 주영 엔진이 계산.

⚠️ 대회 Bedrock 사용 불가 → Anthropic 직접 API로 전환. SDK·messages.create 시그니처는 동일,
   클라이언트(AnthropicBedrock→Anthropic)·모델 ID('anthropic.' 접두사 제거)만 다름.

모델 라우팅(그린AI · 저전력):
  - 분류/비전 추출 = Claude Haiku 4.5  (싸고 빠름, 이미지 지원)
  - 코칭(별도) = Claude Sonnet 4.6     (coach.py에서)

Claude API 모델 ID(접두사 없음): claude-haiku-4-5-20251001 / claude-sonnet-4-6
인증: 환경변수 ANTHROPIC_API_KEY (Anthropic SDK가 자동 인식).

API 키 전이면 MOCK=1 로 스키마만 검증하며 개발 가능.
"""
import base64
import json
import os
import re
import pathlib

PROMPTS = pathlib.Path(__file__).resolve().parent.parent / "prompts"
SYSTEM = (PROMPTS / "classify.md").read_text(encoding="utf-8")

# 비전·분류 (저전력 라우팅). 모델 ID 변경 시 TERRA_EXTRACT_MODEL 로 오버라이드.
HAIKU = os.environ.get("TERRA_EXTRACT_MODEL", "claude-haiku-4-5-20251001")


def _client():
    """Anthropic Claude API 클라이언트 (api_key=환경변수 ANTHROPIC_API_KEY 자동 인식)."""
    from anthropic import Anthropic
    return Anthropic()


_VALID_TYPES = {"menu", "food", "purchase", "screentime", "energy"}


def _normalize(out):
    """LLM 출력 방어 — 계약 §1 타입만 남기고, 버린 항목이 있으면 needs_review."""
    if not isinstance(out, dict):
        return {"activities": [], "needs_review": True}
    acts = out.get("activities", [])
    acts = acts if isinstance(acts, list) else []
    kept = [a for a in acts if isinstance(a, dict) and a.get("type") in _VALID_TYPES]
    if len(kept) != len(acts):
        out["needs_review"] = True
    out["activities"] = kept
    return out


def _parse_json(text):
    """LLM 응답에서 JSON만 안전 추출 (마크다운 코드펜스 제거) + 계약 §1 정규화."""
    text = re.sub(r"```(?:json)?|```", "", text)
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return _normalize(json.loads(m.group(0)) if m else {"activities": [], "needs_review": True})
    except json.JSONDecodeError:
        return {"activities": [], "needs_review": True}


def _first_text(resp):
    """응답에서 첫 text 블록(없으면 빈 문자열). text 블록 부재 시 StopIteration→500 방지."""
    return next((b.text for b in resp.content if b.type == "text"), "")


def extract_from_image_bytes(image_bytes, media_type="image/jpeg"):
    """이미지 바이트 → CONTRACT.md §1 activities JSON. (엔드포인트·업로드용)"""
    if os.environ.get("MOCK") == "1":
        return _mock("image")
    b64 = base64.standard_b64encode(image_bytes).decode()
    resp = _client().messages.create(
        model=HAIKU,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": [
            {"type": "image",
             "source": {"type": "base64", "media_type": media_type, "data": b64}},
            {"type": "text", "text": "이 캠퍼스 입력을 스키마대로 분류해. JSON만."},
        ]}],
    )
    return _parse_json(_first_text(resp))


def extract_from_image(image_path, media_type="image/jpeg"):
    """식단·영수증 사진 파일 → CONTRACT.md §1 activities JSON. (Claude API 비전 통일, Textract 미사용)"""
    if os.environ.get("MOCK") == "1":
        return _mock(image_path)
    return extract_from_image_bytes(pathlib.Path(image_path).read_bytes(), media_type)


def extract_from_text(text):
    """전력·수동 입력 텍스트 → activities JSON. (사진=extract_from_image · 스크린타임=screentime.py)"""
    if os.environ.get("MOCK") == "1":
        return _mock(text)
    resp = _client().messages.create(
        model=HAIKU,
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": f"입력: {text}\n스키마대로 분류해. JSON만."}],
    )
    return _parse_json(_first_text(resp))


def _mock(_):
    """라이브 추출 없이 파이프라인·스키마 검증용."""
    return {"activities": [{"type": "menu", "name": "제육덮밥"}],
            "confidence": 0.82, "needs_review": False}


if __name__ == "__main__":
    # MOCK=1 python3 terra_ai/bedrock/extract.py  로 스키마 흐름 확인
    out = extract_from_text("학식: 밥, 빨간 양념 고기볶음, 김치")
    print(json.dumps(out, ensure_ascii=False, indent=2))
