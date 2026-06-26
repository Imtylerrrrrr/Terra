"""
Terra 입력 해석 — Bedrock Claude 멀티모달로 식판/영수증/이동을 품목·수량 JSON으로.
설계: 해석만 LLM, 숫자(탄소)는 안 만든다 → CONTRACT.md §1 스키마로 출력 → 주영 엔진이 계산.

모델 라우팅(그린AI · 저전력):
  - 분류/비전 추출 = Claude Haiku 4.5  (싸고 빠름, 이미지 지원)
  - 코칭(별도) = Claude Sonnet 4.6     (coach.py에서)

Bedrock 모델 ID는 'anthropic.' 접두사 (claude-api 스킬 확인):
  anthropic.claude-haiku-4-5 / anthropic.claude-sonnet-4-6 / anthropic.claude-opus-4-8

AWS 크레딧/Bedrock 모델 액세스 전이면 MOCK=1 로 스키마만 검증하며 개발 가능.
"""
import base64
import json
import os
import re
import pathlib

PROMPTS = pathlib.Path(__file__).resolve().parent.parent / "prompts"
SYSTEM = (PROMPTS / "classify.md").read_text(encoding="utf-8")

# 비전·분류 (저전력 라우팅). ⚠️ Bedrock은 리전/클라이언트에 따라 정식 ID 필요할 수 있음:
#   anthropic.claude-haiku-4-5-20251001-v1:0  또는 추론프로파일  us.anthropic.claude-haiku-4-5-...
#   → 주영이 환경에 맞는 ID를 TERRA_EXTRACT_MODEL 로 주입.
HAIKU = os.environ.get("TERRA_EXTRACT_MODEL", "anthropic.claude-haiku-4-5")
REGION = os.environ.get("AWS_REGION", "us-east-1")


def _client():
    """Bedrock Mantle 클라이언트 (Messages API, 주영의 AWS 계정 자격증명 사용)."""
    from anthropic import AnthropicBedrockMantle
    return AnthropicBedrockMantle(aws_region=REGION)


def _parse_json(text):
    """LLM 응답에서 JSON만 안전 추출 (마크다운 코드펜스 제거)."""
    text = re.sub(r"```(?:json)?|```", "", text)
    m = re.search(r"\{.*\}", text, re.S)
    try:
        return json.loads(m.group(0)) if m else {"activities": [], "needs_review": True}
    except json.JSONDecodeError:
        return {"activities": [], "needs_review": True}


def extract_from_image(image_path, media_type="image/jpeg"):
    """식단·영수증 사진 → CONTRACT.md §1 activities JSON. (Bedrock 비전 통일, Textract 미사용)"""
    if os.environ.get("MOCK") == "1":
        return _mock(image_path)
    b64 = base64.standard_b64encode(pathlib.Path(image_path).read_bytes()).decode()
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
    return _parse_json(next(b.text for b in resp.content if b.type == "text"))


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
    return _parse_json(next(b.text for b in resp.content if b.type == "text"))


def _mock(_):
    """라이브 Bedrock 없이 파이프라인·스키마 검증용."""
    return {"activities": [{"type": "menu", "name": "제육덮밥"}],
            "confidence": 0.82, "needs_review": False}


if __name__ == "__main__":
    # MOCK=1 python3 terra_ai/bedrock/extract.py  로 스키마 흐름 확인
    out = extract_from_text("학식: 밥, 빨간 양념 고기볶음, 김치")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    # 추출 → 엔진 연결 검증
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
    from terra_ai.engine.carbon_engine import compute
    print("→ 엔진:", compute(out["activities"])["total_grams_co2e"], "gCO2e")
