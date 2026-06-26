# 배출계수 출처 (데이터활용성 10점 — "공공 실연동 + 출처 명시")

원칙: **숫자는 공공데이터, 계산은 코드.** 모든 계수에 출처·연도 명시.

## 입력 4종 × 계수 출처
> 🔑 엔진 `factors.seed.json` 키 ↔ 아래 CSV 행의 **1:1 매핑·단위환산·갭**은 [KEYMAP.md](./KEYMAP.md) 참조(§4-A 값교체용).

| 입력 | 계수 파일 | 출처 | 상태 |
|---|---|---|---|
| ④ 전력 | energy_transport_factors.csv | **KEITI 환경성적표지 평가계수(2021)** 0.4951 / kcen 0.4781 / GIR 2023 0.4173 | ✅ 공인 |
| ② 스크린타임 | digital_factors.csv | **기기 소비전력(W) × kcen 478.1 × IEA 네트워크보정(÷0.72)**. 기기전력=Energuide(노트북45W·PC150W)·스마트폰<3W. IEA 영상 1h=36g(기기:전송:DC=72:23:5) | ✅ 공인근거+환산 |
| ③ 영수증 | product_factors.csv | **KEITI 환경성적표지 유효 인증현황(2025.07)** — 진라면0.164·컵라면0.39·생수0.099 등 28품목 | ✅ 공인 |
| ① 식단 | food_factors.csv | **소고기·쌀밥=한끼밥상(한국일보, 정부연구 종합) 국내값** / 나머지 Poore&Nemecek 2018 시드 | 🟡 일부 국내, 잔여 보강 |

> ③ 영수증: KEITI EPD 3,002개 중 편의점/매점 소비재 28개 추출. 미매칭 품목은 금액기반 대체.
> ③ purchase 아메리카노: KEITI EPD에 커피 항목 부재 → **문헌값** 채택. Berners-Lee 2010 『How Bad Are Bananas?』 블랙커피 1잔 21 gCO₂e(물 끓임 + 원두 운송·가공 포함). 동일값 인용 [New Scientist](https://www.newscientist.com/letter/mg21729030-900-hold-the-milk/) · [8 Billion Trees](https://8billiontrees.com/carbon-offsets-credits/coffee-carbon-footprint/). (라이선스 준수 위해 재서술)

## 그린AI 추정 근거 (윤리성 — net-negative 주장용)
- AI 분석 비용 ~0.3 gCO2e/건: 보수 추정. GPT-4o 1천토큰 교환 ≈0.38g([Vanderbilt 2025](https://wp0.vanderbilt.edu/youngscientistjournal/article/a-token-level-framework-for-quantifying-chatgpts-environ-mental-impacts-and-a-browser-based-intervention-for-reducing-prompt-resource-use)), Gemini 텍스트 ≈0.03g([Google 2025](https://cloud.google.com/blog/products/infrastructure/measuring-the-environmental-impact-of-ai-inference)). 우리는 더 작은 Haiku 사용 → 범위 이하. (출처 내용은 라이선스 준수 위해 재구성)

## 못 쓰는 자료 (참고)
- **농림식품 녹색인증 정보**(농기평): 인증목록(기술명·번호·날짜)일 뿐 **탄소발자국 없음** → 계수 불가. "녹색인증 제품" 신뢰도 배지로만 활용 가능.
- **GIR 국가 인벤토리**: 분야×연도 국가 총배출량(kt) → 계수 아님, 거시 맥락(문제 인식)용.

## 남은 것
- ① **국내 식품계수 + 실제 학식 주간메뉴** — [DATA_NEEDS.md](./DATA_NEEDS.md) ①.
