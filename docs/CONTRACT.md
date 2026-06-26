# Terra JSON 계약 (1일차 최우선 — 민지·주영·연성 합의용)

> 역할플랜·프론트컨벤션 둘 다 "JSON 형식 합의 = 1일차 최대 병목"이라고 못박음.
> 이 파일이 **추출(민지) → 계산엔진(주영) → 3D 행성(연성)** 사이의 단일 진실.
> 합의 후 프론트는 `types.ts`, 백엔드는 모델 클래스로 이 스키마를 박제.
>
> 🔄 **제품 방향 반영 (2026-06-26):** 입력 4종 = **식단·스크린타임·영수증·전력** / 행성 **3계층**(캠퍼스계→학과→개인) / 크기=**참여율**·깨끗함=**평균 배출량** / **도감 수집**(동물·풍력발전소 등).
>
> 🔗 **#14 통합 (2026-06-26):** 입력 경로 명시(§1) · 민지 AI 헬퍼 `resolve()`/`coach()`(§2-A 보조) · 출력 `by_type`. 입력 타입·tier·엔드포인트·DynamoDB는 **구현 기준 유지** — #14의 `product`/`digital`·tier 6056은 **미채택**(엔진·프론트 코드는 `purchase`/`screentime`, 엔진 실측 소불고기 ≈ 6021(정식계수)).

## 1) 추출 출력 = 계산엔진 입력  (민지 → 주영)

Claude API 멀티모달이 식판·영수증·스크린타임·전력을 정규화한 결과. **숫자(탄소)는 없음** — 계산은 엔진이.

**입력 경로(#14):** 식단·영수증 = **Claude API 비전**(Textract 아님) · 스크린타임 = **안드로이드 UsageStatsManager**(비전 아님 — 앱별 사용시간을 분 단위 수치로) · 전력 = **수치 입력**.

```json
{
  "activities": [
    { "type": "menu",       "name": "제육덮밥" },
    { "type": "food",       "item": "돼지고기", "grams": 120 },
    { "type": "purchase",   "item": "아메리카노", "qty": 1 },
    { "type": "screentime", "item": "스마트폰", "minutes": 320 },
    { "type": "energy",     "item": "전력_가정용체감", "kwh": 1.5 }
  ],
  "confidence": 0.82,
  "needs_review": false
}
```

- `type`: `menu` | `food` | `purchase` | `screentime` | `energy`  (※ 통학 `transport` 제거 — 입력 4종으로 변경)
  - `menu` 식단 메뉴명 · `food` 식단 품목+grams · `purchase` 영수증 품목+qty · `screentime` 사용시간(분) · `energy` 전력(kWh)
- `name`/`item`: 반드시 계수 테이블 키 (menu_recipes / food_factors / **purchase_factors** / **screentime_factor** / energy_factors)
- 단위: `grams`(food, g) · `qty`(purchase, **개수·정수**) · `minutes`(screentime, 분) · `kwh`(energy, kWh)
  - 영수증 계수는 **개당 기준(₩ 금액기반 아님)** 으로 통일 — 금액기반은 코어 제외(후순위 옵션).
- `needs_review: true` → UI가 "확인 필요" 배지

## 2) 계산엔진 출력 (주영 → 연성)

### 2-A) 개인 결과 = **개인 행성** 입력
```json
{
  "user_id": "u_123",
  "dept_id": "cs",
  "total_grams_co2e": 1050.0,
  "tier": "mid",
  "items": [
    {
      "name": "제육덮밥",
      "total_grams_co2e": 1050.0,
      "breakdown": [
        { "label": "돼지고기", "grams_co2e": 840.0, "source": "Poore&Nemecek2018..." },
        { "label": "쌀밥",     "grams_co2e": 210.0, "source": "..." }
      ],
      "sources": ["..."]
    }
  ],
  "best_alternative": { "name": "비건비빔밥", "grams_co2e": 285.0, "saving_grams": 765.0 },
  "unlocks": []
}
```
- `tier`: 개인 행성 비주얼(색·숲·빙하) — §3 임계값
- `best_alternative`: 코칭/매직모먼트용 — "내일 비건 시 −0.8kg"
- `unlocks`: 해금된 **도감** 항목 id 배열(`string[]`). **해금 규칙(확정)**: 누적 절감량 마일스톤 — 0.5 / 2 / 5 / 10 kg CO2e 누적 절감마다 1종 해금. (항목 목록·비주얼은 디자인 협의 — §4-B)

> 🔗 **2-A 보조) 민지 AI 헬퍼 — #14 통합 (제공 예정 · 백엔드 엔진과 별도 모듈):**
> - `resolve(activities)`: §1 activities → §2-A 항목별 gCO2e+합계를 한 번에 산출하는 AI측 헬퍼. 반환에 선택 필드 `by_type`(타입별 합계, 예 `{ "menu": 1080, "screentime": 149, "purchase": 328, "energy": 743 }`) 포함 가능. **주영**이 결과에 `tier`(§3) 추가·저장.
> - `coach(result, user_dept)`: 코칭 출력 `{ planet_line, next_action, expected_saving_grams, tone }`. `best_alternative`는 **코드 계산**, 문장만 Claude API Sonnet(폴백=규칙기반).
>   - 필드 정의(프론트 #26 바인딩용): `planet_line`(행성 상태 한 줄·string)·`next_action`(다음 행동 한 줄·string)·`expected_saving_grams`(number = `best_alternative.saving_grams`, 대안 없으면 0)·`tone`(**enum: `celebratory`(low)·`encouraging`(mid)·`gentle`(high)** — tier에서 코드 결정, UI 스타일 분기용).
> - ⚠️ 위 헬퍼·필드는 아직 main 미구현(민지 AI 모듈 제공 예정). 현재 백엔드 진입점은 §5 `POST /compute`(`compute()`)·`GET /campus`(`aggregate()`).

### 2-B) 집계 결과 = **학과 / 캠퍼스 행성** 입력
행성 **크기 = 참여율**, **깨끗한 정도 = 참여 인원 평균 배출량(tier)**.
```json
{
  "campus_system": {
    "campus_id": "main",
    "participation_rate": 0.38,
    "avg_grams_co2e": 1320.0,
    "tier": "mid",
    "departments": [
      {
        "dept_id": "cs",
        "name": "컴퓨터공학과",
        "participants": 84,
        "total_students": 200,
        "participation_rate": 0.42,
        "avg_grams_co2e": 1185.0,
        "tier": "mid"
      }
    ]
  }
}
```
- `participation_rate` = participants / total_students → **행성 크기**
- `avg_grams_co2e` → **깨끗한 정도**(§3 tier 매핑). 캠퍼스계 = 학과들의 집계.

## 3) 행성 tier 임계값 (gCO2e) ← 민지가 계수로 산출, 재튜닝 가능

개인 행성 = 1끼 기준 / 학과·캠퍼스 행성 = 1인 평균 기준(평균 스케일에 맞춰 임계값 재튜닝 필요).

| tier | 범위 (gCO2e) | 예시 | 행성 상태(깨끗한 정도) |
|---|---|---|---|
| `low`  | ≤ 700      | 비건비빔밥 285 · 잔치국수 310 | 숲 무성·빙하 두꺼움 |
| `mid`  | 700–2500   | 제육 1050 · 김치찌개 1065 · 치킨마요 1140 | 중간 |
| `high` | > 2500     | **소불고기 6021** | 숲 시들·빙하 녹음 |

> 데모 킬샷: **소불고기 6,021g vs 비건비빔밥 285g = 21배.** 행성이 눈에 띄게 변함.
> 프론트컨벤션 §5의 `--color-emission-low/mid/high` 토큰이 이 tier에 1:1 매핑.

## 4) 결정 사항 & 합의 필요

### 4-A) 결정 (주영 확정 — 그대로 구현)
- 입력 4종 · 5-type 추출 스키마 · 출력 2-A/2-B 형식 = 위 §1·§2 그대로.
- `qty` = 개수·정수, 영수증 계수는 **개당 기준**(금액기반 후순위).
- `unlocks` 해금 규칙 = 누적 절감 마일스톤 **0.5 / 2 / 5 / 10 kg**.
- 개인 행성 tier 임계값 = §3(**700 / 2500**) 그대로 사용.
- API 엔드포인트 계약 = §5.
- 프론트 타입(`frontend/src/types/contract.ts`)이 이 문서와 1:1 — **백엔드 모델도 동일 필드로 맞춤**.
- **계수 정책(확정)**: 민지 정식 계수 전까지 엔진은 **임시 추정 시드 계수**(주영 관리)로 동작 — 시드 예: 스크린타임 스마트폰 `0.15`·노트북 `0.5` gCO2e/분, 미매핑 `purchase` 품목은 `needs_review=true`. 민지가 **계수 값만** 정식 교체(키·단위·형식 불변).
- **집계 tier 임계값(확정 초기값)**: 개인과 동일(**700 / 2500**)로 시작 → 데이터 분포 확인 후 **상수만** 재튜닝(형식·코드 불변).

### 4-B) 외부 트래킹
- 🟡 도감 **항목 목록·비주얼**(디자인 협의) → GitHub **[이슈 #9](https://github.com/Imtylerrrrrr/Terra/issues/9)** (승빈·연성). 해금 *규칙*은 4-A 확정, *내용물*만 이슈에서.

## 5) API 엔드포인트 계약 (주영 확정)

| 메서드 · 경로 | 요청 바디 | 응답 | 담당 |
|---|---|---|---|
| `POST /extract` | 이미지(S3 key) 또는 텍스트 | §1 `ExtractionResult` | 민지 (Claude API) |
| `POST /compute` | `{ user_id, dept_id, extraction: §1, campus_id?, request_id? }` | §2-A `PersonalResult` (+ `persisted`) | 주영 (엔진) |
| `GET /campus/{campus_id}` | — | §2-B `AggregateResult` | 주영 (집계) |

- 인프라: **API Gateway HTTP API + Lambda**, JSON 입출력.
- 인증: 코어는 `user_id`를 바디/헤더로 전달. Cognito(플러스) 붙으면 토큰 `sub`로 대체.
- 에러 응답: `{ "error": { "code": string, "message": string } }` + 적절한 HTTP status.
- `campus_id`는 선택(기본 `"main"`). `/compute`는 계산 후 결과를 DynamoDB에 저장(집계용)하고 응답에 `persisted: bool` 포함.
- `request_id`는 선택(멱등키). 같은 `request_id` 재시도·중복 제출은 누적 절감을 **1회만** 반영(도감 과해금 방지). 생략 시 매 호출 누적.
- **`persisted: false` 일 때 `unlocks` 는 신뢰 불가** — 진행상태 로드 실패 시 `unlocks` 는 빈 배열로 내려간다(부분집합 오표시 방지). **FE 는 이 응답으로 도감을 덮어쓰지 말 것**(직전 캐시 유지). `tier`·`total_grams_co2e` 등 계산 결과는 항상 유효.

## 6) DynamoDB 스키마 (주영 확정 — 단일 테이블)

`POST /compute` 저장 → `GET /campus/{id}` 집계의 백킹 스토어. 환경변수 `TERRA_TABLE`.

| PK | SK | 용도 | 주요 속성 |
|---|---|---|---|
| `CAMPUS#{campus_id}` | `RESULT#{dept_id}#{user_id}` | 개인 결과 | `total_grams_co2e` · `tier` · `dept_id` · `user_id` |
| `CAMPUS#{campus_id}` | `DEPT#{dept_id}` | 학과 메타 | `name` · `total_students` |
| `CAMPUS#{campus_id}` | `USER#{user_id}` | 사용자 도감 진행 | `cumulative_saved_grams` · `unlocks`(id 배열) · `processed_requests`(멱등키 최근 N개) |

- 캠퍼스 1건 **Query(PK)** 로 결과 + 학과 메타를 한 번에 조회 → `aggregate()`.
- `load_campus()` 는 `RESULT#`/`DEPT#` 만 취함 → `USER#` 항목은 집계(§2-B)에 영향 없음.
- **도감 해금**: `/compute` 가 `best_alternative.saving_grams` 를 사용자별 `cumulative_saved_grams` 에 누적 → `unlocked_ids(누적)` 으로 `unlocks` 채워 응답·저장. 해금 규칙·카탈로그(14종)는 §4-A·`terra_ai/data/collection.json`(백엔드 미러: `carbon_engine/dex_catalog.seed.json`).
- **멱등·안전 저장**: `request_id` 가 `processed_requests` 에 있으면 누적을 다시 더하지 않음(중복 제출 방어). 진행상태 **로드 실패 시 저장을 스킵**해 기존 누적/해금이 `0` 으로 덮어써지는 것을 방지하고, **응답 `unlocks` 도 빈 배열**로 내려 부분집합 오표시를 막음(둘 다 `persisted=false` 로 surface — FE 는 이때 도감 갱신 금지).
- 학과 메타(`total_students`)는 관성 가상데이터에서 미리 적재(`put_dept_meta`).
- 코드: `backend/store/` (Dynamo / InMemory 동일 인터페이스).
