# 런북: /extract 라이브까지 (AI 레인 100%)

민지 코드는 머지·검증 완료. 아래는 **라이브 동작까지** 남은 사람/권한 단계. 순서대로.

## 1. PR 머지 — 주영
- [ ] **PR #28** 머지 (`/extract` Lambda·라우트 + Bedrock 클라이언트 교정). 머지돼야 `template.yaml`에 `/extract`가 들어감.

## 2. SafeRole 권한 — 관리자/주영
- [ ] `SafeRole-netzero-12` 에 **`bedrock:InvokeModel`** 추가 (없으면 라이브 추출 403/AccessDenied).
  - 리전 us-east-1, 모델: Claude Haiku 4.5(추출). 모델 액세스도 콘솔에서 활성화 확인.

## 3. 배포 — 주영
- [ ] 리포 루트에서 `sam build && sam deploy`
  - `ExtractFunction`은 `CodeUri: terra_ai/` → `terra_ai/requirements.txt`(anthropic[bedrock]·boto3) 자동 설치.
  - 라이브 모델 ID가 추론프로파일을 요구하면 `TERRA_EXTRACT_MODEL`(예: `us.anthropic.claude-haiku-4-5-...`) 주입.
- [ ] 출력 `ApiUrl` 확보.

## 4. 라이브 검증 — 민지/주영
- [ ] `TERRA_API="<ApiUrl>" python3 terra_ai/scripts/live_check.py`
  - ① /extract 라이브(Bedrock) ② /extract fixture ③ /extract→/compute 종단 = **OK** 확인.
- 실패 시: 403=2번 권한, ImportError=requirements/모델ID, 타임아웃=ExtractFunction Timeout(현재 30s).

## 5. 데모 리허설 — 팀
- [ ] 골든패스(식판→탄소→행성) 1회 소리내어 리허설(시간측정).
- [ ] **폴백 연습**: 라이브 글리치 대비 `{"fixture":"소불고기덮밥"}` 또는 env `TERRA_DEMO_FALLBACK` 즉시 전환.
- [ ] 킬샷 수치 확인: 소불고기덮밥 **6021g** vs 비건비빔밥 **285g**.

---
검증 기준(회귀): `terra_ai/scripts/smoke_extract.py`·`smoke_integration.py` PASS · `backend` 13 tests OK.
