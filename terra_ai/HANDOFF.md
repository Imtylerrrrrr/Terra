# 핸드오프: 민지(AI·데이터) → 주영(엔진/Lambda)

> 한 줄 요약: **`data/factors.json` 한 파일 + `resolve(activities)` 한 줄**이면 입력 4종이 항목별 gCO2e로 나옵니다. 주영은 그 결과에 `tier` 붙이고 집계·저장만.

## 1. 넘기는 것
| 파일 | 역할 | 소유 |
|---|---|---|
| `data/factors.json` | **단일 자산** (food·energy_transport·menu_recipes·digital·product·app_categories) | 민지 |
| `resolve.py` | 입력 4종 → 항목별 gCO2e + 합계 (factors.json 직접 로드, 자립) | 민지 |
| `bedrock/coach.py` | 코칭 문장 (Sonnet, 폴백=규칙기반) | 민지 |
| `bedrock/retrieve.py`·`match.py` | product KB 하이브리드 / 코드 폴백 | 민지 |
| `screentime.py` | 안드로이드 사용시간 → digital activities | 민지 |
| `engine/carbon_engine.py` | 주영 참조 스텁 (CSV 직접 읽음, resolve와 무관) | 주영 |

## 2. 사용법 (이게 전부)
```python
from terra_ai.resolve import resolve
from terra_ai.bedrock.coach import coach

out = resolve(activities)              # ① 계산
c   = coach(out, user_dept="컴퓨터공학과")  # ② 코칭 (선택)
```

- 입력 `activities` = CONTRACT §1 (menu/food/product/digital/energy).
- 출력 `out` = CONTRACT §2 `{total_grams_co2e, items[], by_type}`. **숫자는 계수파일에서만(환각0).**
- 각 item에 **`verify`**(공인/시드) 흐름 — 신뢰도 배지용. product는 `needs_review`. 모두 **additive**라 tier 추가 로직 무영향.
- AWS 미연결/개발 시 환경변수 `MOCK=1` → product=코드매칭, coach=규칙기반으로 동작.

## 3. 주영이 할 일 (CONTRACT §2·§3·§4)
`resolve()` 결과에 **`tier` 추가 + 학과/캠퍼스 집계 + 저장**. 임계값은 `factors.json`의
`meta.tier_thresholds_gco2e`에 박혀 있음(low_max 700 · high_min 2500):

```python
import json, pathlib
TH = json.loads((pathlib.Path("terra_ai/data/factors.json")).read_text(encoding="utf-8")) \
        ["meta"]["tier_thresholds_gco2e"]

def tier(grams):                       # 노드 평균 또는 1건 기준
    if grams <= TH["low_max"]:  return "low"
    if grams >  TH["high_min"]: return "high"
    return "mid"
```
- 집계 노드(§3): `size_ratio`(참여율) · `avg_grams_co2e`(참여인원 평균) · `tier`.
- 집계 트리거: DynamoDB Streams 권장(학과·캠퍼스 평균).

## 4. Lambda 이식 팁
- **factors.json 한 파일만 배포 패키지에 동봉**하면 `resolve.py`는 그대로 돈다(CSV 불필요).
- product KB 쓰려면 환경변수 `TERRA_KB_ID`(KB 배포 후)·`AWS_REGION` 주입. 없으면 코드 퍼지매칭 폴백.
- coach 모델 ID는 `TERRA_COACH_MODEL`(기본 `anthropic.claude-sonnet-4-6`)로 환경 맞춰 주입.

## 5. 데이터 갱신 규칙 (중요)
- **CSV가 원천, factors.json은 빌드 산출물.** CSV 수정 후 반드시:
  ```bash
  python3 terra_ai/scripts/build_factors.py
  ```
  안 돌리면 resolve(JSON)와 carbon_engine(CSV)이 어긋남.

## 6. 검증
```bash
python3 terra_ai/scripts/smoke_test.py     # 전부 PASS여야 함 (무결성 가드)
```
- 기준값(회귀 감시): 하루 데모 총합 **2300.0g** · 소불고기정식 **6056g** · 비건비빔밥 **465g** · 진라면순한맛×2 **328.2g**.
