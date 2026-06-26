# Terra 백엔드 — 계산엔진 (주영)

탄소 계산엔진 + Lambda 핸들러. **Python · 표준 라이브러리만**(런타임 의존성 0).
형식 단일 진실은 [`docs/CONTRACT.md`](../docs/CONTRACT.md).

## 구조

```
backend/
├─ carbon_engine/          # 순수 계산 로직 (Lambda 무관)
│  ├─ engine.py            # compute() 개인(2-A) · aggregate() 집계(2-B)
│  ├─ tiers.py             # tier 임계값 (700/2500)
│  ├─ factors.py           # 시드 계수 로더
│  └─ factors.seed.json    # ⚠️ 임시 추정 계수 — 민지 정식값으로 '값만' 교체
└─ handlers/               # API Gateway HTTP API 진입점 (CONTRACT §5)
   ├─ compute_handler.py   # POST /compute
   └─ campus_handler.py    # GET /campus/{campus_id}  (DB 조회는 TODO)
```

## 실행 / 테스트

```bash
cd backend
python -m unittest discover -s tests -v   # 단위 테스트 (9건)
```

엔진 직접 사용:

```python
from carbon_engine import compute, aggregate
r = compute({"activities": [{"type": "menu", "name": "제육덮밥"}]}, "u1", "cs")
# → {"total_grams_co2e": 1155.0, "tier": "mid", "items": [...], ...}
```

## 남은 통합 작업 (주영)
- `campus_handler._load_personal_results / _load_dept_meta` → DynamoDB 조회로 교체.
- `unlocks`(도감 해금)는 누적 절감 이력이 필요 → DB 집계 단계에서 마일스톤(0.5/2/5/10kg) 적용.
- 계수 정식값: 민지가 `factors.seed.json` 값 교체 (키·단위·형식 불변).
