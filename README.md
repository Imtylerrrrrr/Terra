# Terra — 캠퍼스의 안부 🌱

> 캠퍼스의 일상(식단·스크린타임·영수증·전력)을 탄소배출량으로 환산하고,
> **캠퍼스 행성계 → 학과 행성 → 개인 행성**으로 시각화하는 **앱**.

AWS 해커톤(무박 2일) 출품작입니다.

---

## 핵심 아이디어

1. **입력** — 캠퍼스 활동을 입력: **식단 · 스크린타임 · 영수증 · 전력**
2. **AI 추출** — Claude(멀티모달) API가 식단·영수증 등에서 품목·수량을 추출
3. **계산엔진** — 추출 결과 × 배출계수(식품·전력 등)로 탄소배출량 산출
4. **시각화** — three.js로 **캠퍼스 행성계 → 학과 행성 → 개인 행성**에 결과를 반영
5. **수집/육성** — 탄소를 줄이면 동물·풍력발전소 등을 **도감으로 수집**하는 **키우기 게임 감성**

배출계수는 공공 데이터와 생성형 AI 기반 가상 데이터를 함께 사용하는 하이브리드 방식입니다.

### 행성 규칙
- **캠퍼스별 행성계 → 학과별 행성 → 개인 자기만의 행성** (3계층)
- 행성 **크기 = 인원당 참여 비율(참여율)**
- 행성 **깨끗한 정도 = 참여 인원의 평균(배출량 평균)**

## 기술 스택 (AWS-max · 현장 확정)

> 원칙: 브라우저에서 도는 three.js만 빼고 **백엔드·AI·데이터·호스팅은 전부 AWS 서비스**로 채운다 (대회 점수 = AWS 활용도).

| 층 | 서비스 | 역할 | AWS |
|---|---|---|:---:|
| 호스팅 | Amplify Hosting (or S3 + CloudFront) | 웹앱 배포·CDN | ✅ |
| 프론트 렌더링 | three.js + React/Vite | 3D 행성·도감 (브라우저 실행) | — |
| 인증 | Cognito | 로그인·학과 소속 관리 | ✅ |
| API 입구 | API Gateway (HTTP API) | 프론트 ↔ 백엔드 | ✅ |
| 백엔드 로직 | Lambda (서버리스) | 입력 처리 + 계산엔진 + 조회 | ✅ |
| AI 추출 | **Claude API**(Anthropic 직접) | 식단·영수증 사진 → 품목·수량 | — \* |
| 배출계수 | `factors.seed.json`(공공계수·민지) | 식품·전력 매핑 | — \*\* |
| DB | DynamoDB | 사용자·학과·캠퍼스·배출량·도감 | ✅ |
| 파일 저장 | S3 | 업로드 사진 원본(`/extract` image_s3_key) | ✅ |
| 로그·모니터링 | CloudWatch | Lambda 로그·지표(자동) | ✅ |
| 데이터 | 공공 배출계수 + AI 가상데이터 | 하이브리드 | — |

\* 대회 제한계정에서 **Bedrock 사용 불가** → Anthropic Claude API 직접 호출(키=Lambda 환경변수)로 전환.
\*\* Bedrock Knowledge Base(계수 RAG)는 스트레치였으나 미채택 — 계수는 코드 시드(`factors.seed.json`)로 직접 사용.

**🟢 현재 라이브 배포:** S3 · Lambda · API Gateway(HTTP API) · DynamoDB + Claude API 추출 → **입력→추출→계산→저장→3D 한 사이클 동작**(SAM `template.yaml`, us-east-1).
**🔵 플러스(미배포·여유 시 점수+):** Cognito 인증 · Amplify/S3+CloudFront 호스팅 · Step Functions · DynamoDB Streams · SQS/EventBridge.

> ⚠️ 플러스 욕심내다 코어 안 돌면 0점 — **코어 한 사이클 먼저**. 사진 추출은 Claude API 멀티모달로 통일(Textract 중복 주의).

## 팀 & 역할

| 구분 | 담당 | 역할 |
|---|---|---|
| AI/데이터 | 민지 | Claude 멀티모달 추출·정식 배출계수 매핑, 데이터 파이프라인 |
| PM/백엔드 | 주영 | PM·기획·발표 총괄, 백엔드·AWS·계산엔진·전체 통합 |
| 프론트엔드 | 연성 | Kiro 화면 구현, three.js 3D, 입력 UX |
| 데이터+화면 | 관성 | 가상 학생·식단·스크린타임·영수증·전력 데이터 생성, 입력→결과 화면 |
| UX·발표 | 승빈 | 화면 설계·비주얼, 발표자료·시연영상 |

발표: 5분 + Q&A 3분 (발표자: 심주영)

## 데이터 흐름

```
입력(식단·스크린타임·영수증·전력)
        ┌─ AI (품목·수량 추출) ──┐
   ─────┤                       ├──→ 계산엔진(×계수 / 집계) ──→ 행성 반영 (개인→학과→캠퍼스계) + 도감 수집
        └─ 가상데이터 / DB ──────┘
                                      ↑
                           프론트 연결 / 디자인
```

## 문서

- [docs/CONTRACT.md](./docs/CONTRACT.md) — **JSON 단일 진실** (추출→엔진→3D · API 엔드포인트 · DynamoDB 스키마)
- [backend/README.md](./backend/README.md) — 백엔드 계산엔진·저장계층·핸들러
- [CONTRIBUTING.md](./CONTRIBUTING.md) — 커밋·브랜치·PR 규칙
- [docs/Terra_역할_플랜.md](./docs/Terra_역할_플랜.md) — 역할 분담 & 진행 플랜
- `docs/Terra_아이디어노트_검증반영_v3.docx` — 아이디어 노트

## 상태

🚧 해커톤 진행 중 — **입력→추출→계산→저장→3D 한 사이클이 라이브로 동작**. 백엔드·AI·3D·통합 데모까지 구현·배포 완료, 남은 건 코칭 라우트 배포·학과 메타 풀시드·리허설.

**구현 완료**
- [x] JSON 계약 확정 — [docs/CONTRACT.md](./docs/CONTRACT.md) §1~6 (추출·출력·tier·API·DynamoDB)
- [x] 계산엔진 — `compute()`(개인)·`aggregate()`(집계), tier 700/2500 · 단위 테스트 13건 통과
- [x] 정식 배출계수 — `factors.seed.json` (공공계수·민지) 반영
- [x] 저장 계층 — DynamoDB 단일 테이블(`TERRA_TABLE`) / InMemory 동일 인터페이스
- [x] AI 추출 — `POST /extract` Claude API 멀티모달(식단·영수증 사진→품목·수량), S3 업로드 경로 · **라이브 배포·동작 확인**
- [x] **AWS 배포** — SAM `template.yaml`(Lambda · API Gateway HTTP API · DynamoDB · S3) 프로비저닝, API 라이브(us-east-1)
- [x] Lambda 핸들러 — `POST /compute` · `GET /campus/{id}` · `POST /extract` (라이브)
- [x] 3D 행성 렌더링 — three.js: 캠퍼스 은하 → 학과 행성 → 개인 아바타 행성 + 도감 14종 (`frontend/demo/planet.html`)
- [x] 데모 데이터 — 시드 6학과(`campus=demo` 라이브 적재) + 탄소입력 4종(식단/스크린타임/영수증/전력) 화면
- [x] **통합 데모** — `frontend/presentation/` (폰 프레임 + 라이브 `/compute`·`/extract`·`/campus` 연동), `start-presentation.bat` 으로 실행
- [x] 프론트 계약 계층 — 도메인 타입(`contract.ts`) · API 클라이언트(`api.ts`: `postCompute`/`getCampus`) · React+Vite+TS 스캐폴딩

**남은 작업**
- [ ] 코칭 라이브화 — `POST /coach` SAM 라우트 추가 + 재배포 (핸들러는 구현됨)
- [ ] 학과 메타 풀시드 — 참여율·총원(현재 공개시드라 0) → `put_dept_meta` 풀시드로 행성 크기 실값화
- [ ] (플러스) Cognito 인증 · Amplify/S3+CloudFront 호스팅 · CloudWatch
- [ ] 2일차 — 전체 리허설 + 시연영상
