"""로컬 라이브 추출 점검 — Claude API로 추출을 직접 호출(배포·주영·SafeRole 불필요).

전제:
  1) pip install -r terra_ai/requirements.txt
  2) 환경변수 ANTHROPIC_API_KEY=sk-ant-... (대회 발급 키)
사용:
  python3 terra_ai/scripts/live_extract_local.py 식판.jpg            # 이미지(데모 경로·권장)
  python3 terra_ai/scripts/live_extract_local.py --text "학식: 제육볶음, 밥"
필요 시: TERRA_EXTRACT_MODEL=claude-haiku-4-5-20251001 (모델 오버라이드)
"""
import json
import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

if os.environ.get("MOCK") == "1":
    sys.exit("MOCK=1 은 라이브가 아닙니다 — MOCK 해제 후 실행하세요.")

from terra_ai.bedrock.extract import extract_from_image, extract_from_text


def main(argv):
    if not argv:
        sys.exit('사용: live_extract_local.py <이미지경로>  |  --text "문장"')
    try:
        out = extract_from_text(" ".join(argv[1:])) if argv[0] == "--text" \
            else extract_from_image(argv[0])
    except ModuleNotFoundError as e:
        sys.exit(f"의존성 없음 → pip install -r terra_ai/requirements.txt   ({e})")
    except Exception as e:
        m = str(e).lower()
        if "authentication" in m or "api_key" in m or "401" in m or "x-api-key" in m:
            hint = "→ ANTHROPIC_API_KEY 환경변수 확인(sk-ant-...)"
        elif "model" in m or "not_found" in m or "404" in m:
            hint = "→ 모델 ID 확인 / TERRA_EXTRACT_MODEL 오버라이드"
        else:
            hint = "→ 메시지 확인"
        sys.exit(f"라이브 호출 실패: {e}\n{hint}")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n라이브 추출 OK ✅ — Anthropic 클라이언트·모델·프롬프트 동작 확정")


if __name__ == "__main__":
    main(sys.argv[1:])
