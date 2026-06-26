"""로컬 라이브 추출 점검 — 내 AWS 계정으로 Bedrock 추출을 직접 호출(배포·주영·SafeRole 불필요).

전제:
  1) pip install -r terra_ai/requirements.txt
  2) AWS 자격증명(내 계정) — aws configure 또는 AWS_ACCESS_KEY_ID/SECRET/AWS_REGION
  3) 해당 리전 Bedrock 콘솔에서 Claude 모델 '액세스 활성화'
사용:
  python3 terra_ai/scripts/live_extract_local.py 식판.jpg            # 이미지(데모 경로·권장)
  python3 terra_ai/scripts/live_extract_local.py --text "학식: 제육볶음, 밥"
필요 시: AWS_REGION=us-east-1  TERRA_EXTRACT_MODEL=us.anthropic.claude-haiku-4-5-...  (추론프로파일)
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
        if "accessdenied" in m or "not authorized" in m or "model" in m:
            hint = "→ Bedrock 콘솔에서 해당 리전 Claude 모델 액세스 활성화 / TERRA_EXTRACT_MODEL(추론프로파일) 확인"
        elif "credential" in m or "token" in m or "region" in m:
            hint = "→ AWS 자격증명·리전 확인 (aws configure / 환경변수)"
        else:
            hint = "→ 메시지 확인"
        sys.exit(f"라이브 호출 실패: {e}\n{hint}")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print("\n라이브 추출 OK ✅ — AnthropicBedrock 클라이언트·모델·프롬프트 동작 확정")


if __name__ == "__main__":
    main(sys.argv[1:])
