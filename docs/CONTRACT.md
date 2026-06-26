# Terra JSON 계약 (1일차 최우선 — 민지·주영·연성 합의용)

> 역할플랜·프론트컨벤션 둘 다 "JSON 형식 합의 = 1일차 최대 병목"이라고 못박음.
> 이 파일이 **추출(민지) → 계산엔진(주영) → 3D 행성(연성)** 사이의 단일 진실.
> 합의 후 프론트는 `types.ts`, 백엔드는 모델 클래스로 이 스키마를 박제.

## 1) 추출 출력 = 계산엔진 입력  (민지 → 주영)

Bedrock 멀티모달이 식판/영수증/이동을 정규화한 결과. **숫자(탄소)는 없음** — 계산은 엔진이.

```json
{
  "activities": [
    { "type": "menu",      "name": "제육덮밥" },
    { "type": "food",      "item": "돼지고기", "grams": 120 },
    { "type": "transport", "item": "시내버스", "amount": 4.2 },
    { "type": "energy",    "item": "전력_가정용체감", "amount": 1.5 }
  ],
  "confidence": 0.82,
  "needs_review": false
}
```

- `type`: `menu` | `food` | `transport` | `energy`
- `name`/`item`: 반드시 `data/*.csv`에 존재하는 키 (menu_recipes / food_factors / energy_transport_factors)
- `grams`(food, g) · `amount`(transport=인-km, energy=kWh)
- `needs_review: true` → UI가 "확인 필요" 배지

## 2) 계산엔진 출력 = 3D 행성 입력  (주영 → 연성)

```json
{
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
  "best_alternative": { "name": "비건비빔밥", "grams_co2e": 570.0, "saving_grams": 615.0 }
}
```

- `tier`: 행성 비주얼(색·숲·빙하) 매핑 키 — 아래 임계값
- `best_alternative`: 코칭/매직모먼트용 — "내일 비건 시 −0.6kg"

## 3) 행성 tier 임계값 (gCO2e / 1끼)  ← 민지가 계수로 산출, 재튜닝 가능

엔진 실측 기준 (data/menu_recipes.csv):

| tier | 범위 (gCO2e) | 예시 | 행성 상태 |
|---|---|---|---|
| `low`  | ≤ 700      | 비건비빔밥 570 · 잔치국수 305 | 숲 무성·빙하 두꺼움 |
| `mid`  | 700–2500   | 김치찌개 1065 · 치킨마요 1140 · 제육 1185 | 중간 |
| `high` | > 2500     | **소불고기 8150** | 숲 시들·빙하 녹음 |

> 데모 킬샷: **소불고기 8,150g vs 비건비빔밥 570g = 14배.** 행성이 눈에 띄게 변함.
> 프론트컨벤션 §5의 `--color-emission-low/mid/high` 토큰이 이 tier에 1:1 매핑.

## 4) 합의 체크리스트 (1일차)
- [ ] 주영: 엔진이 이 출력 형태로 반환 (현재 `carbon_engine.compute()`가 거의 일치 — `tier`/`best_alternative`만 추가)
- [ ] 민지: 추출 LLM이 `activities` 스키마로만 출력 (classify.md 준수)
- [ ] 연성: `tier` → 행성 색/상태, `best_alternative` → 코칭 말풍선
