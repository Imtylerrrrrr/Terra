# Terra JSON 계약 (1일차 최우선 — 민지·주영·연성 합의용)

> 역할플랜·프론트컨벤션 둘 다 "JSON 형식 합의 = 1일차 최대 병목"이라고 못박음.
> 이 파일이 **추출(민지) → 계산엔진(주영) → 3D 행성(연성)** 사이의 단일 진실.
> 합의 후 프론트는 `types.ts`, 백엔드는 모델 클래스로 이 스키마를 박제.
>
> 🔄 **제품 방향 반영 (2026-06-26):** 입력 4종 = **식단·스크린타임·영수증·전력** / 행성 **3계층**(캠퍼스계→학과→개인) / 크기=**참여율**·깨끗함=**평균 배출량** / **도감 수집**(동물·풍력발전소 등).

## 1) 추출 출력 = 계산엔진 입력  (민지 → 주영)

Bedrock 멀티모달이 식판·영수증·스크린타임·전력을 정규화한 결과. **숫자(탄소)는 없음** — 계산은 엔진이.

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
  "total_grams_co2e": 1185.0,
  "tier": "mid",
  "items": [
    {
      "name": "제육덮밥",
      "total_grams_co2e": 1185.0,
      "breakdown": [
        { "label": "돼지고기", "grams_co2e": 840.0, "source": "Poore&Nemecek2018..." },
        { "label": "쌀밥",     "grams_co2e": 315.0, "source": "..." }
      ],
      "sources": ["..."]
    }
  ],
  "best_alternative": { "name": "비건비빔밥", "grams_co2e": 570.0, "saving_grams": 615.0 },
  "unlocks": []
}
```
- `tier`: 개인 행성 비주얼(색·숲·빙하) — §3 임계값
- `best_alternative`: 코칭/매직모먼트용 — "내일 비건 시 −0.6kg"
- `unlocks`: 해금된 **도감** 항목 id 배열(`string[]`). **해금 규칙(확정)**: 누적 절감량 마일스톤 — 0.5 / 2 / 5 / 10 kg CO2e 누적 절감마다 1종 해금. (항목 목록·비주얼은 디자인 협의 — §4-B)

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
| `low`  | ≤ 700      | 비건비빔밥 570 · 잔치국수 305 | 숲 무성·빙하 두꺼움 |
| `mid`  | 700–2500   | 김치찌개 1065 · 치킨마요 1140 · 제육 1185 | 중간 |
| `high` | > 2500     | **소불고기 8150** | 숲 시들·빙하 녹음 |

> 데모 킬샷: **소불고기 8,150g vs 비건비빔밥 570g = 14배.** 행성이 눈에 띄게 변함.
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
| `POST /extract` | 이미지(S3 key) 또는 텍스트 | §1 `ExtractionResult` | 민지 (Bedrock) |
| `POST /compute` | `{ user_id, dept_id, extraction: §1, campus_id? }` | §2-A `PersonalResult` (+ `persisted`) | 주영 (엔진) |
| `GET /campus/{campus_id}` | — | §2-B `AggregateResult` | 주영 (집계) |

- 인프라: **API Gateway HTTP API + Lambda**, JSON 입출력.
- 인증: 코어는 `user_id`를 바디/헤더로 전달. Cognito(플러스) 붙으면 토큰 `sub`로 대체.
- 에러 응답: `{ "error": { "code": string, "message": string } }` + 적절한 HTTP status.
- `campus_id`는 선택(기본 `"main"`). `/compute`는 계산 후 결과를 DynamoDB에 저장(집계용)하고 응답에 `persisted: bool` 포함.

## 6) DynamoDB 스키마 (주영 확정 — 단일 테이블)

`POST /compute` 저장 → `GET /campus/{id}` 집계의 백킹 스토어. 환경변수 `TERRA_TABLE`.

| PK | SK | 용도 | 주요 속성 |
|---|---|---|---|
| `CAMPUS#{campus_id}` | `RESULT#{dept_id}#{user_id}` | 개인 결과 | `total_grams_co2e` · `tier` · `dept_id` · `user_id` |
| `CAMPUS#{campus_id}` | `DEPT#{dept_id}` | 학과 메타 | `name` · `total_students` |

- 캠퍼스 1건 **Query(PK)** 로 결과 + 학과 메타를 한 번에 조회 → `aggregate()`.
- 학과 메타(`total_students`)는 관성 가상데이터에서 미리 적재(`put_dept_meta`).
- 코드: `backend/store/` (Dynamo / InMemory 동일 인터페이스).
