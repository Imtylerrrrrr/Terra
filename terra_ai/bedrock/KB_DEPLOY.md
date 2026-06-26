# 계수 RAG(Bedrock KB) 배포 메모 — AI/데이터 파이프라인용

`retrieve.py`가 쓰는 Bedrock Knowledge Base를 띄우는 기술 절차. (배포는 주영 AWS 계정)

1. `terra_ai/data/kb_factors.jsonl` (3,036 계수 문서) → S3 버킷 업로드
2. Bedrock KB 생성: 데이터소스 = 그 S3, 벡터스토어 = **S3 Vectors** (OpenSearch Serverless는 idle 과금 함정이라 회피)
3. 임베딩 = Titan Text Embeddings v2
4. 생성된 KB ID → 환경변수 `TERRA_KB_ID` 주입 → `retrieve.py`가 자동 사용
5. 미배포/개발 중엔 `MOCK=1` → `match.py` 코드매칭으로 동일 동작

재생성: `python3 terra_ai/scripts/kb_build.py` (계수 CSV 바뀌면 재실행 → 재업로드)
