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
- 단위: `grams`(food, g) · `qty`(purchase, 개 — 금액기반 ₩ 계수도 가능, **확인 필요**) · `minutes`(screentime, 분) · `kwh`(energy, kWh)
- `needs_review: true` → UI가 "확인 필요" 배지
- ⚠️ **스크린타임·영수증 계수는 확인 필요** (공공/추정 출처 — 민지)

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
- `unlocks`: 탄소 절감 시 모으는 **도감** 항목(동물·풍력발전소 등) — **해금 규칙 확인 필요**

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

## 4) 합의 체크리스트 (1일차)
- [ ] 주영: 엔진이 **개인 결과(2-A) + 집계 결과(2-B)** 둘 다 반환 (현재 `carbon_engine.compute()`에 `tier`·`best_alternative`·집계/참여율 추가)
- [ ] 민지: 추출 LLM이 `activities` **5-type 스키마**로만 출력(classify.md 준수) + 스크린타임·영수증 계수 확보
- [ ] 연성: 개인 `tier`→개인 행성 / `participation_rate`→학과·캠퍼스 행성 **크기** / `avg_grams_co2e`→**깨끗함** / `best_alternative`→코칭 / `unlocks`→도감
