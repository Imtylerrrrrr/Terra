"""
POST /coach — PersonalResult(§2-A) → 코칭 문장 {planet_line, next_action, expected_saving_grams, tone}.

의존성 0(표준 라이브러리만). AWS Lambda(API Gateway proxy) 핸들러 + 로컬 데모 서버 겸용:
  - Lambda : handler(event, context)          # API Gateway proxy in/out
  - 로컬   : python3 -m terra_ai.api.coach_handler   # http://localhost:8001/coach

입력(JSON 본문):
  {"result": <PersonalResult>,                 # /compute 응답 그대로 (숫자=코드, 환각 차단)
   "user_dept": "컴퓨터공학과",                 # 선택: 행성 문구용 학과 표시명(기본 "우리 학과")
   "cumulative_saving_grams": 1800}            # 선택: 주면 next_action에 다음 도감 해금 넛지 추가

출력: docs/CONTRACT.md §2-A 보조 — {"planet_line","next_action","expected_saving_grams","tone"}

설계(계약 명시): 숫자(절감량·tier)는 코드, 문장만 Claude Sonnet. 라이브 실패·MOCK=1 → 규칙기반 폴백.
MOCK=1 이면 키 없이 규칙기반 흐름 검증(데모/CI). 라이브는 환경변수 ANTHROPIC_API_KEY 필요.
⚠️ 인증 없음(데모용). 운영 노출 시 API Gateway 인증/요청크기 제한 필수.
"""
import base64
import json
import pathlib
import sys

try:   # 모노레포: terra_ai 패키지 경유
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
    from terra_ai.bedrock.coach import coach
except ModuleNotFoundError as e:   # Lambda(CodeUri=terra_ai/): 형제 패키지로
    if e.name and not e.name.startswith("terra_ai"):
        raise   # terra_ai 외 의존성 누락(anthropic 등)은 폴백으로 숨기지 않고 표면화
    print("[coach_handler] terra_ai 패키지 미탐지 → 형제 패키지(bedrock.*) 폴백", file=sys.stderr)
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
    from bedrock.coach import coach


def _coach(body):
    """JSON 본문 dict → 코칭(계약 §2-A 보조). result 필수, user_dept·cumulative 선택."""
    result = body.get("result")
    if not isinstance(result, dict) or "total_grams_co2e" not in result:
        raise ValueError("result(PersonalResult, total_grams_co2e 포함)가 필요합니다.")
    user_dept = body.get("user_dept") or "우리 학과"
    cumulative = body.get("cumulative_saving_grams")
    if cumulative is not None:
        try:
            cumulative = float(cumulative)
        except (TypeError, ValueError):
            raise ValueError("cumulative_saving_grams 는 숫자여야 합니다.")
    return coach(result, user_dept, cumulative_saving_grams=cumulative)


def _error(code, message):
    """CONTRACT §5 에러 형식 {"error":{"code","message"}}."""
    return {"error": {"code": code, "message": str(message)}}


def handler(event, context=None):
    """AWS Lambda — API Gateway proxy 통합 (POST /coach)."""
    try:
        raw = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            raw = base64.b64decode(raw).decode()
        body = json.loads(raw) if isinstance(raw, str) else raw
        result = _coach(body)
        code = 200
    except (ValueError, json.JSONDecodeError) as e:
        result, code = _error("invalid_json" if isinstance(e, json.JSONDecodeError) else "bad_request", e), 400
    except Exception as e:   # coach 는 내부에서 규칙기반 폴백 → 여기 도달은 예기치 못한 오류
        result, code = _error("coach_failed", e), 502
    return {"statusCode": code,
            "headers": {"Content-Type": "application/json; charset=utf-8"},
            "body": json.dumps(result, ensure_ascii=False)}


def _serve(port):
    """로컬 데모용 stdlib HTTP 서버 (POST /coach)."""
    from http.server import BaseHTTPRequestHandler, HTTPServer

    class H(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/coach":
                self.send_error(404, "use POST /coach")
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

    import os
    print(f"POST http://localhost:{port}/coach  (MOCK={os.environ.get('MOCK', '0')})")
    HTTPServer(("", port), H).serve_forever()


if __name__ == "__main__":
    import os
    _serve(int(os.environ.get("PORT", 8001)))
