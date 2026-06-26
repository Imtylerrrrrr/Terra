# Terra — AI·데이터 레인 (민지)

데모 매직모먼트 **"학식 식단 사진 1장 → 5초 탄소 → 학과 행성 반영"**의 AI/데이터 백본.
설계 원칙: **해석은 AI(Bedrock) · 숫자는 공공데이터(RAG) · 계산은 코드(Lambda)**.

## 구성
```
data/
  food_factors.csv              # 식품 배출계수 (kgCO2e/kg) + 출처
  energy_transport_factors.csv  # 전력·교통 계수 (공인: kcen 0.4781 / GIR 0.4173)
  menu_recipes.csv              # 학식 메뉴 → 식재료 전개 (데모용)
engine/
  carbon_engine.py              # 활동량×계수 합산 → gCO2e (Lambda 이식 가능)
prompts/
  classify.md                   # 분류: Haiku, JSON만, 숫자 계산 금지
  coach.md                      # 코칭: Sonnet, 받은 숫자만 인용
```

## 파이프라인 (5단계, 아이디어노트 5-3과 일치)
1. **입력 해석** — 식판/텀블러=Bedrock 비전, 영수증/메뉴=Textract→정규화, 통학=거리
2. **분류** — `classify.md`(Haiku)가 표준 카테고리로 정규화
3. **계수 매핑(RAG)** — `data/*.csv`를 Bedrock Knowledge Base로 적재, 분류키로 검색
4. **계산** — `carbon_engine.py`가 활동량×계수 (LLM에 산수 금지 → 환각 차단)
5. **코칭** — `coach.md`(Sonnet)가 계산값 기반 개인화 문장

## 심사 배점 직접 기여 (당신 담당)
- **데이터활용성 10점** ← `data/`의 공공 실연동 계수 + 가상 소비데이터, 출처 명시
- **기술성 15 / Cloud 20** ← Bedrock(Haiku/Sonnet 라우팅)+Textract+KB(RAG)
- **윤리성 10** ← 그린AI: ①계산은 코드(추론 안 함) ②모델 라우팅 ③RAG로 토큰 절감
  → "이 분석 0.3g vs 절감 615g" net-negative 표시

## 검증 상태 (정직성)
- **공인·확정**: 전력계수 kcen 0.4781 / GIR 0.4173 (아이디어노트 출처 동일)
- **검증 필요(`verify` 컬럼)**: 식품·교통 계수는 Poore&Nemecek 2018(전지구 평균) 시드 →
  **GIR 식품계수·환경부 교통계수로 교체 예정**. "정밀 감사 아닌 출처 있는 상대적 크기" 원칙.

## 실행
```bash
python3 engine/carbon_engine.py
# 제육덮밥 1185g  vs  비건비빔밥 570g  →  절감 615g
```

## 민지 → 팀에 요청할 실데이터 (있으면 정확도↑)
1. 경기대(또는 인하대) **실제 학식 주간 메뉴** → `menu_recipes.csv` 현실화
2. **GIR 식품·교통 배출계수** 원표(있으면 csv) → `verify` 항목 확정
3. 기숙사/강의실 **전력 사용 샘플**(kWh) → 전력 시나리오
