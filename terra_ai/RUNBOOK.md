# 런북: /extract 라이브까지 (AI 레인 100%)

민지 코드는 머지·검증 완료. 아래는 **라이브 동작까지** 남은 사람/권한 단계.

> ✅ **2026-06-27 라이브 반영됨** — 콘솔 수동 배포로 `/extract` 동작 확인(text 경로 200, Haiku).
> 해커톤 제한계정은 SAM/CloudFormation 불확실 → **§A 콘솔 수동 배포가 실사용 경로**.
> (아래 SAM 절차 §1~§5는 IaC 참고용으로 남겨둠.)

## A. 콘솔 수동 배포 (실사용 · 권장)

### A-1. zip 빌드 (로컬, OS 무관)
```bash
bash scripts/build_extract_zip.sh   # → 리포 루트 terra-extract.zip
```
- `anthropic`+`pydantic-core`(컴파일 휠)를 **Lambda 타깃(manylinux2014_x86_64·cp312)** 으로 받음.
  로컬에서 그냥 `pip install -t .` 하면 mac/arm 휠이 섞여 Lambda 에서 `ImportError` → 반드시 이 스크립트로.

### A-2. Lambda 생성 (콘솔, us-east-1)
- 함수명 `netzero-12-extract` · 런타임 **Python 3.12** · 아키텍처 **x86_64**(빌드와 일치)
- 실행 역할 = **기존 `SafeRole-netzero-12`** (새 역할 생성 금지)
- 코드: `terra-extract.zip` 업로드 · 핸들러 `api.extract_handler.handler`
- 일반 구성: Timeout **29s** · 메모리 256MB
- 환경 변수: `ANTHROPIC_API_KEY=sk-ant-...`(콘솔 직접 입력) · `TERRA_UPLOAD_BUCKET=<업로드 버킷명>`
  - ⚠️ 키는 zip/코드/git 에 절대 넣지 않음 — Lambda env 에만.

### A-3. 라우트 연결 (기존 HTTP API 재사용 — 새 API 만들지 말 것)
- API Gateway → `rg12w8i9md`(HTTP API) → Routes → Create → `POST /extract`
- 해당 라우트 → Attach integration → Lambda `netzero-12-extract` (호출 권한 허용)
- `$default` 자동배포라 보통 즉시 반영.

### A-4. S3 이미지 경로 권한 (image_s3_key 쓸 때만)
- netzero-12 는 IAM 역할 편집 거부(explicit deny) → SafeRole 인라인정책 불가.
- **우회: 업로드 버킷의 버킷 정책**으로 SafeRole 에 읽기 부여:
  ```json
  { "Effect":"Allow",
    "Principal":{"AWS":"arn:aws:iam::842544789367:role/SafeRole-netzero-12"},
    "Action":"s3:GetObject*", "Resource":"arn:aws:s3:::<버킷명>/*" }
  ```
- 데모 핵심(식단/영수증)은 base64·text 경로라 S3 없이 동작 → 블로킹 아님.

### A-5. 검증
```bash
curl -X POST 'https://rg12w8i9md.execute-api.us-east-1.amazonaws.com/extract' \
  -H 'Content-Type: application/json' -d '{"text":"학식: 밥, 제육볶음, 김치"}'
# → {"activities":[...], "confidence":..., "needs_review":...}  (http 200)
```
- 실패 시 CloudWatch: `ImportError`=아키텍처/휠 불일치(A-1 재빌드) · 401=API 키 · 타임아웃=29s.
- 모델: 기본 Haiku(`claude-haiku-4-5-20251001`). `TERRA_EXTRACT_MODEL` env 로 오버라이드.

---

## (참고) SAM/IaC 절차 — 계정이 허용될 때만

### 1. PR 머지 — 주영
- [x] `/extract` Lambda·라우트 + Claude API 클라이언트 머지.

### 2. Claude API 키 — 관리자/주영
- [x] **Claude API 키** 확보(`sk-ant-...`). Bedrock 미사용이라 별도 IAM 불필요.

### 3. 배포 — 주영
- 리포 루트에서 `sam build && sam deploy --parameter-overrides AnthropicApiKey=sk-ant-...`
  - `ExtractFunction` = `CodeUri: terra_ai/` → `requirements.txt`(anthropic) 자동 설치.

### 4. 라이브 검증 — 민지/주영
- `TERRA_API="<ApiUrl>" python3 terra_ai/scripts/live_check.py`
  - ① /extract 라이브 ② /extract fixture ③ /extract→/compute 종단 OK.

### 5. 데모 리허설 — 팀
- 골든패스(식판→탄소→행성) 리허설(시간측정).
- **폴백 연습**: `{"fixture":"소불고기덮밥"}` 또는 env `TERRA_DEMO_FALLBACK` 즉시 전환.
- 킬샷: 소불고기덮밥 **6021g** vs 비건비빔밥 **285g**.

---
검증 기준(회귀): `terra_ai/scripts/smoke_extract.py`·`smoke_integration.py` PASS · `backend` 13 tests OK.
