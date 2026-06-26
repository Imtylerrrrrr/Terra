"""
POST /extract — 사진/텍스트 → 품목·수량(activities, CONTRACT §1). Bedrock 멀티모달 추출.

의존성 0(표준 라이브러리만). AWS Lambda(API Gateway proxy) 핸들러 + 로컬 데모 서버 겸용:
  - Lambda : handler(event, context)          # API Gateway proxy in/out
  - 로컬   : python3 -m terra_ai.api.extract_handler   # http://localhost:8000/extract

입력(JSON 본문):
  {"image_base64": "<b64>", "media_type": "image/jpeg"}   # 식판·영수증 사진
  {"text": "학식: 밥, 제육볶음, 김치"}                      # 전력·수동 텍스트
출력: CONTRACT §1 — {"activities":[...], "confidence":..., "needs_review":...}

MOCK=1 이면 AWS 없이 스키마 흐름 검증(데모/CI). 라이브는 AWS 자격증명 + Bedrock 모델 액세스 필요.
⚠️ 인증 없음(데모용). 운영 노출 시 API Gateway 인증/요청크기 제한 필수.
"""
import base64
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from terra_ai.bedrock.extract import extract_from_image_bytes, extract_from_text


def _extract(body):
    """JSON 본문 dict → activities. text 우선, 없으면 image_base64."""
    if body.get("text"):
        return extract_from_text(body["text"])
    if body.get("image_base64"):
        img = base64.b64decode(body["image_base64"])
        return extract_from_image_bytes(img, body.get("media_type", "image/jpeg"))
    raise ValueError("image_base64 또는 text 필요")


def handler(event, context=None):
    """AWS Lambda — API Gateway proxy 통합 (POST /extract)."""
    try:
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw).decode()
        body = json.loads(raw) if isinstance(raw, str) else raw
        result = _extract(body)
        code = 200
    except (ValueError, json.JSONDecodeError) as e:
        result, code = {"error": str(e)}, 400
    return {"statusCode": code,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps(result, ensure_ascii=False)}


def _serve(port):
    """로컬 데모용 stdlib HTTP 서버 (POST /extract)."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/extract":
                self.send_error(404, "use POST /extract")
                return
            n = int(self.headers.get("Content-Length", 0))
            raw = self.rfile.read(n).decode() or "{}"
            try:
                result, code = _extract(json.loads(raw)), 200
            except (ValueError, json.JSONDecodeError) as e:
                result, code = {"error": str(e)}, 400
            payload = json.dumps(result, ensure_ascii=False).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_):
            pass

    print(f"POST http://localhost:{port}/extract  (MOCK={os.environ.get('MOCK', '0')})")
    HTTPServer(("", port), H).serve_forever()


if __name__ == "__main__":
    _serve(int(os.environ.get("PORT", 8000)))
