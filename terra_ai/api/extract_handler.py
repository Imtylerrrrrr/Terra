"""
POST /extract — 사진/텍스트 → 품목·수량(activities, CONTRACT §1). Claude API 멀티모달 추출.

의존성 0(표준 라이브러리만). AWS Lambda(API Gateway proxy) 핸들러 + 로컬 데모 서버 겸용:
  - Lambda : handler(event, context)          # API Gateway proxy in/out
  - 로컬   : python3 -m terra_ai.api.extract_handler   # http://localhost:8000/extract

입력(JSON 본문):
  {"image_base64": "<b64>", "media_type": "image/jpeg"}   # 식판·영수증 사진(라이브 Claude API)
  {"image_s3_key": "uploads/abc.jpg"}                      # S3 업로드 사진(CONTRACT §5). 버킷=env TERRA_UPLOAD_BUCKET 고정, media_type=확장자 추론
  {"text": "학식: 밥, 제육볶음, 김치"}                      # 텍스트(라이브 Claude API)
  {"fixture": "소불고기덮밥"}                               # 데모 결정적 폴백(라이브·키 불필요)
출력: CONTRACT §1 — {"activities":[...], "confidence":..., "needs_review":...}

데모 폴백: 라이브 추출 실패 시 자동폴백은 env `TERRA_DEMO_FALLBACK=<fixture명>` (opt-in).
fixture 목록: data/demo_fixtures.json.

MOCK=1 이면 키 없이 스키마 흐름 검증(데모/CI). 라이브는 환경변수 ANTHROPIC_API_KEY 필요.
⚠️ 인증 없음(데모용). 운영 노출 시 API Gateway 인증/요청크기 제한 필수.
"""
import base64
import json
import os
import pathlib
import sys

try:   # 모노레포: terra_ai 패키지 경유
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
    from terra_ai.bedrock.extract import extract_from_image_bytes, extract_from_text
except ModuleNotFoundError as e:   # Lambda(SAM CodeUri=terra_ai/): 형제 패키지로
    if e.name and not e.name.startswith("terra_ai"):
        raise   # terra_ai 외 의존성 누락(anthropic 등)은 폴백으로 숨기지 않고 표면화
    print("[extract_handler] terra_ai 패키지 미탐지 → 형제 패키지(bedrock.*) 폴백", file=sys.stderr)
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from bedrock.extract import extract_from_image_bytes, extract_from_text

# 데모 폴백 fixture (계약 §1). '_' 접두 메타키는 제외.
_FIXTURES = {
    k: v for k, v in json.loads(
        (pathlib.Path(__file__).resolve().parent.parent / "data" / "demo_fixtures.json")
        .read_text(encoding="utf-8")
    ).items() if not k.startswith("_")
}


# S3 이미지 입력 가드(요청크기 우회 방지). 확장자→media_type 추론 표.
_MAX_IMAGE_BYTES = int(os.environ.get("TERRA_MAX_IMAGE_BYTES", 5 * 1024 * 1024))  # 5MB
_S3_MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
             ".webp": "image/webp", ".gif": "image/gif"}


def _media_type_from_key(key, default="image/jpeg"):
    """S3 key 확장자 → media_type (Claude 비전이 png/heic 등 오독하지 않게)."""
    return _S3_MEDIA.get(pathlib.Path(key).suffix.lower(), default)


def _s3_image_bytes(key):
    """S3 객체(업로드 사진) → 바이트. CONTRACT §5 이미지(S3 key) 입력 경로.

    버킷은 env TERRA_UPLOAD_BUCKET 고정(클라이언트 지정 불가 — 권한 스코프 밖 객체 접근 차단).
    ContentLength 로 다운로드 전 사이즈 가드(API GW 한도 우회 방지). 조회 실패는 ValueError(→400).
    MOCK=1 → 다운로드 생략. boto3 는 Lambda 런타임 기본 제공.
    """
    if os.environ.get("MOCK") == "1":
        return b""  # MOCK: 네트워크 없이 스키마 흐름만 (extract_from_image_bytes가 무시)
    bucket = os.environ.get("TERRA_UPLOAD_BUCKET")
    if not bucket:
        raise ValueError("S3 업로드 버킷 미설정 (env TERRA_UPLOAD_BUCKET)")
    import boto3   # Lambda 런타임 기본 포함 → requirements 불필요
    from botocore.exceptions import ClientError
    try:
        obj = boto3.client("s3").get_object(Bucket=bucket, Key=key)
    except ClientError as e:
        raise ValueError(f"S3 객체 조회 실패: {key} ({e.response['Error'].get('Code')})")
    size = obj.get("ContentLength", 0)
    if size > _MAX_IMAGE_BYTES:
        raise ValueError(f"이미지 용량 초과: {size}B > {_MAX_IMAGE_BYTES}B (TERRA_MAX_IMAGE_BYTES)")
    return obj["Body"].read()


def _extract(body):
    """JSON 본문 dict → activities(계약 §1). 우선순위: fixture > text > image_base64 > image_s3_key.

    `fixture`: 데모 결정적 모드 — 라이브 추출 없이 사전 추출 결과 반환(폴백·리허설).
    """
    if body.get("fixture"):
        fx = _FIXTURES.get(body["fixture"])
        if fx is None:
            raise ValueError(f"알 수 없는 fixture: {body['fixture']} (가능: {list(_FIXTURES)})")
        return fx
    if body.get("text"):
        return extract_from_text(body["text"])
    if body.get("image_base64"):
        img = base64.b64decode(body["image_base64"])
        return extract_from_image_bytes(img, body.get("media_type", "image/jpeg"))
    if body.get("image_s3_key"):
        key = body["image_s3_key"]
        return extract_from_image_bytes(_s3_image_bytes(key), _media_type_from_key(key))
    raise ValueError("fixture · text · image_base64 · image_s3_key 중 하나 필요")


def _error(code, message):
    """CONTRACT §5 에러 형식 {"error":{"code","message"}}."""
    return {"error": {"code": code, "message": str(message)}}


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
        result, code = _error("invalid_json" if isinstance(e, json.JSONDecodeError) else "bad_request", e), 400
    except Exception as e:   # 라이브 추출 실패 → 데모 폴백 (opt-in: TERRA_DEMO_FALLBACK)
        fb = os.environ.get("TERRA_DEMO_FALLBACK")
        if fb and fb in _FIXTURES:
            result, code = {**_FIXTURES[fb], "_fallback": fb}, 200
        else:
            result, code = _error("extraction_failed", e), 502
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
            raw = self.rfile.read(n).decode()
            resp = handler({"body": raw})   # Lambda 핸들러 재사용 → 폴백·에러 처리 일치
            payload = resp["body"].encode()
            self.send_response(resp["statusCode"])
            for k, v in resp["headers"].items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *_):
            pass

    print(f"POST http://localhost:{port}/extract  (MOCK={os.environ.get('MOCK', '0')})")
    HTTPServer(("", port), H).serve_forever()


if __name__ == "__main__":
    _serve(int(os.environ.get("PORT", 8000)))
