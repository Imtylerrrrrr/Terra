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
   ├─ compute_handler.py   # POST /compute  (계산 + 저장)
   └─ campus_handler.py    # GET /campus/{campus_id}  (저장소 → 집계)
```

`store/` — 결과 저장 계층 (단일 테이블, CONTRACT §6):

```
backend/store/
├─ base.py     # ResultStore 인터페이스(Protocol)
├─ memory.py   # InMemoryResultStore (로컬/테스트)
└─ dynamo.py   # DynamoResultStore (boto3, env TERRA_TABLE)
```

| PK | SK | 속성 |
|---|---|---|
| `CAMPUS#{campus_id}` | `RESULT#{dept_id}#{user_id}` | total_grams_co2e · tier |
| `CAMPUS#{campus_id}` | `DEPT#{dept_id}` | name · total_students |

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

## 배포 (SAM)

루트 `template.yaml` — Lambda(`/compute`, `/campus/{id}`) + DynamoDB 단일 테이블 + HTTP API.

```bash
# SAM CLI 필요: brew install aws-sam-cli
sam build
sam deploy --guided   # 최초 1회 (이후 sam deploy)
```

- 출력 `ApiUrl` → 프론트가 호출할 베이스 URL.
- `TERRA_TABLE` 환경변수는 템플릿이 자동 주입.
- ⚠️ HTTP API에 authorizer 없음 = **공개(미인증) 엔드포인트**. 코어 데모용이며, 운영/플러스는 Cognito JWT Authorizer로 보호.

### 데모 시드 (배포 직후 1회)

갓 배포된 테이블은 비어 있어 `GET /campus/{id}` 가 빈 집계를 반환한다.
`aggregate()` 는 **개인 결과** 기준으로 학과를 만들기 때문에 메타만으론 빈 집계 →
시드 스크립트가 학과 메타 + 샘플 개인 결과를 함께 적재한다.

```bash
# 드라이런: 인메모리에 적재 → §2-B 집계를 출력(AWS 불필요)
python scripts/seed.py

# 실제 적재: 배포된 DynamoDB 테이블로 (boto3 + AWS 자격증명 필요)
pip install boto3
TERRA_TABLE=<출력 TableName> python scripts/seed.py --campus main
```

- `scripts/seed.py` 의 인원·메뉴는 **임시 데모값**(관성 가상데이터로 교체 예정).

## 남은 통합 작업 (주영)
- DynamoDB 테이블 프로비저닝(`TERRA_TABLE`) + API Gateway/Lambda 배포(SAM/CDK).
- `unlocks`(도감 해금)는 누적 절감 이력이 필요 → DB 집계 단계에서 마일스톤(0.5/2/5/10kg) 적용.
- 계수 정식값: 민지가 `factors.seed.json` 값 교체 (키·단위·형식 불변).
- 학과 메타 적재: 관성 가상데이터 → `store.put_dept_meta(campus, dept, name, total_students)`.
