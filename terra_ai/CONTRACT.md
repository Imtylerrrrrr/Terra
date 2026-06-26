# Terra JSON 계약 v2 (입력 4종 · 행성 3계층 — README v2 반영)

> 추출(민지) → 계산엔진(주영) → 3D 행성(연성) 사이의 단일 진실.
> 변경(v1→v2): `transport` 제거, `product`(영수증)·`digital`(스크린타임) 추가, 행성 3계층 집계.
> 입력 경로: 식단·영수증=**Bedrock 비전**(Textract X) · 스크린타임=**안드로이드 UsageStatsManager**(비전 아님) · 전력=수치.

## 1) 추출 출력 = 계산엔진 입력  (민지 → 주영)

입력 4종을 정규화. **숫자(탄소)는 없음** — 계산은 엔진이.

```json
{
  "activities": [
    { "type": "menu",    "name": "제육덮밥" },
    { "type": "food",    "item": "돼지고기", "grams": 120 },
    { "type": "product", "item": "아메리카노", "qty": 1, "krw": 4500 },
    { "type": "digital", "item": "동영상스트리밍", "hours": 2 },
    { "type": "energy",  "item": "전력_KEITI", "kwh": 1.5 }
  ],
  "confidence": 0.82,
  "needs_review": false
}
```

| 입력 | type | 수치 필드 | 계수 파일 |
|---|---|---|---|
| 식단 | `menu`/`food` | grams | menu_recipes / food_factors |
| 영수증 | `product`(식음료는 food) | qty·krw | product_factors(+금액기반 대체) |
| 스크린타임 | `digital` | hours | digital_factors |
| 전력 | `energy` | kwh | energy_transport_factors |

## 2) 통합 출력 = 3D 행성 입력  (민지 `resolve()` → 주영)

엔진/Lambda는 §1 activities를 **`resolve()` 한 줄**로 처리 → 항목별 gCO2e + 합계:

```python
from terra_ai.resolve import resolve
out = resolve(activities)
```
```json
{
  "total_grams_co2e": 2300.0,
  "items": [
    { "type": "menu",    "label": "제육덮밥",     "grams_co2e": 1080.0, "source": "...", "breakdown": [] },
    { "type": "digital", "label": "엔터테인먼트", "grams_co2e": 78.1,   "source": "..." },
    { "type": "product", "label": "진라면순한맛", "grams_co2e": 328.2,  "source": "...", "needs_review": false }
  ],
  "by_type": { "menu": 1080, "digital": 149, "product": 328, "energy": 743 }
}
```
- 라우팅: menu/food/energy=엔진 · product=KB하이브리드(폴백 코드매칭) · digital=시간×계수. 숫자는 계수파일에서만(환각0).
- **주영**: 이 결과에 `tier`(§4) 추가 + §3 집계·저장.

### 코칭 (민지 `coach()`)
```python
from terra_ai.bedrock.coach import coach
coach(out, user_dept="컴퓨터공학과")   # → {planet_line, next_action, expected_saving_grams, tone}
```
`best_alternative`(최저탄소 메뉴 대안)는 **코드 계산**, 문장만 Bedrock Sonnet(폴백=규칙기반).

## 3) 행성 3계층 집계 (README 행성 규칙)

개인 → 학과 → 캠퍼스 행성계. 각 노드:

```json
{
  "level": "dept",
  "id": "컴퓨터공학과",
  "size_ratio": 0.42,
  "avg_grams_co2e": 980.0,
  "tier": "mid"
}
```

- **행성 크기 = `size_ratio`(참여율 = 참여인원/전체)**
- **깨끗한 정도 = `avg_grams_co2e`(참여인원 평균) → `tier`로 색·숲·빙하 매핑**
- 집계는 DynamoDB Streams(학과·캠퍼스 평균, README 🔵플러스)

## 4) tier 임계값 (gCO2e / 1건·끼 또는 노드 평균)

| tier | 범위 | 예시 | 행성 |
|---|---|---|---|
| `low`  | ≤ 700      | 비건비빔밥 465 · 잔치국수 305 | 숲 무성·빙하 두꺼움 |
| `mid`  | 700–2500   | 김치찌개 960 · 제육 1080 | 중간 |
| `high` | > 2500     | **소불고기 6056** | 숲 시들·빙하 녹음 |

> 데모 킬샷: 소불고기 6,056g vs 비건비빔밥 465g = **13배**.
> 프론트컨벤션 §5 `--color-emission-low/mid/high` 토큰이 tier에 1:1.

## 5) 도감(키우기) — 선택
배출↓·참여↑ 시 동물·풍력발전소 등 unlock(도감 수집). **unlock 규칙은 프론트**, 계산엔진은 `tier`·`avg_grams_co2e`만 제공.

## 6) 1일차 합의 체크리스트
- [ ] 주영: 엔진/Lambda가 `resolve()` 호출 → `tier` 추가 + §3 집계 노드(`size_ratio`·`avg_grams_co2e`·`tier`)
- [ ] 민지: 추출/매핑이 §1 `activities`(menu/food/product/digital/energy) 산출 — ✅ resolve()·coach() 제공
- [ ] 연성: `size_ratio`→크기, `tier`→색, `coach()`→코칭 말풍선, unlock→도감
