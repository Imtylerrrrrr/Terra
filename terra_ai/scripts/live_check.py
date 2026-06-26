"""라이브 종단 점검 — 배포된 API에 /extract → /compute 실제 호출(AWS). 의존성 0(urllib).

사용: TERRA_API="https://xxxx.execute-api.us-east-1.amazonaws.com/prod" \
      python3 terra_ai/scripts/live_check.py

전제: PR #28(/extract 라우트) 머지 + SafeRole bedrock:InvokeModel 권한 + sam deploy 완료.
확인: ① 라이브 추출(Bedrock) ② fixture 폴백 ③ 추출→compute 종단.
"""
import json
import os
import sys
import urllib.request
import urllib.error

API = os.environ.get("TERRA_API")
if not API:
    sys.exit("TERRA_API 환경변수에 배포된 API base URL을 넣어주세요 (예: https://...amazonaws.com/prod)")
API = API.rstrip("/")


def post(path, body):
    req = urllib.request.Request(
        API + path, data=json.dumps(body, ensure_ascii=False).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=35) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode() or "{}")
    except Exception as e:
        return None, {"error": str(e)}


print(f"API = {API}")

# 1) 라이브 추출 (실제 Bedrock 비전/분류)
st, ext = post("/extract", {"text": "학식: 제육볶음, 밥, 김치"})
print(f"\n① POST /extract (live)  → {st}")
print("  ", json.dumps(ext, ensure_ascii=False)[:200])

# 2) fixture 폴백 (라이브 실패해도 배포본에서 결정적 동작)
st2, fx = post("/extract", {"fixture": "소불고기덮밥"})
print(f"\n② POST /extract (fixture) → {st2}")
print("  ", json.dumps(fx, ensure_ascii=False)[:200])

# 3) 추출 결과 → /compute 종단 (이음새)
use = ext if (st == 200 and ext.get("activities")) else fx
st3, res = post("/compute", {"user_id": "live_demo", "dept_id": "cs", "extraction": use})
print(f"\n③ POST /compute → {st3}")
if st3 == 200:
    print(f"   total={res.get('total_grams_co2e')}g  tier={res.get('tier')}")

ok = (st == 200 and st3 == 200)
print(f"\n{'라이브 종단 OK ✅' if ok else '⚠️ 일부 실패 — 위 응답/권한(SafeRole bedrock) 확인'}")
sys.exit(0 if ok else 1)
