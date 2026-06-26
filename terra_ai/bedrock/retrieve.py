"""
계수 RAG 조회 — Bedrock Knowledge Base(S3 Vectors) 의미검색 + 코드 결정적 보정(하이브리드).

왜 하이브리드:
  - KB(의미검색): 3,036개 대용량·오타("오모리김치찌개라면")에 강함 → Cloud 활용(20점) RAG
  - code match: 결정적·환각0 → KB 저신뢰 시 보정 (그린AI: 보정엔 추론 안 함)
숫자는 KB metadata/CSV에서만 → LLM이 계수를 생성하지 않음(환각 차단).
MOCK=1 또는 KB 미배포면 코드매칭으로만 동작(개발용).
"""
import os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))
from terra_ai.bedrock.match import match_product  # 코드 폴백

KB_ID = os.environ.get("TERRA_KB_ID")          # 주영 KB 배포 후 주입
REGION = os.environ.get("AWS_REGION", "us-east-1")

def _kb_retrieve(query, k=3):
    import boto3
    c = boto3.client("bedrock-agent-runtime", region_name=REGION)
    r = c.retrieve(
        knowledgeBaseId=KB_ID,
        retrievalQuery={"text": query},
        retrievalConfiguration={"vectorSearchConfiguration": {"numberOfResults": k}},
    )
    return r.get("retrievalResults", [])

def resolve(name, qty=1, min_score=0.5):
    """품목명 → 계수(gCO2e). KB 우선, 저신뢰/미배포 시 코드매칭."""
    if KB_ID and os.environ.get("MOCK") != "1":
        try:
            hits = _kb_retrieve(name)
            if hits and hits[0].get("score", 0) >= min_score:
                md = hits[0]["metadata"]
                f = float(md["factor"])
                g = f * 1000 * qty if str(md["unit"]).lower().startswith("kg") else f * qty
                return {"label": name, "matched": md["item"], "grams_co2e": round(g, 1),
                        "source": md["source"], "method": f"kb({hits[0]['score']:.2f})",
                        "needs_review": False}
        except Exception as e:
            print(f"[KB 조회 실패 → 코드매칭 폴백] {e}")
    return match_product(name, qty)   # 결정적 보정


if __name__ == "__main__":
    os.environ["MOCK"] = "1"   # KB 없이 폴백 경로 확인
    for t in ["진라면순한맛", "오모리김치찌개라면", "핫식스"]:
        r = resolve(t)
        print(f"  {t:14s} → {r['matched'] or '추정':28s} {r['grams_co2e']:7.1f}g [{r['method']}]")
