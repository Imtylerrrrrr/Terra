# 입력 4종 데이터 맵 (식단 · 스크린타임 · 영수증 · 전력)

각 입력별 **필요 계수 + 출처 링크 + 확보 상태**.
태그: ✅확보(제가 받아옴) · 🟡일부(시드/추정) · 🔗포털다운로드(팀 클릭 필요) · 👥팀확보

---

## ① 식단 → 탄소  (데모 핵심 · ★★★)
입력: 학식 식판 사진 → (Claude API 비전) 메뉴/식재료 → 식품계수 × 질량.

| 필요 | 상태 | 출처 |
|---|---|---|
| 식품 탄소발자국(kg CO₂/kg: 쌀·돼지·소·닭·채소…) | 🟡 Poore&Nemecek 2018 전지구평균 시드 적용 | (글로벌, 출처명시 방어 가능) |
| 국내 식품계수(권장 교체) | 🔗 | [농촌진흥청 공공데이터](https://www.rda.go.kr/board/board.do?mode=html&prgId=oda_opendata) · [공공데이터포털 "식품 탄소"](https://www.data.go.kr/tcs/dss/selectDataSetList.do?keyword=식품%20탄소) · [kcen 탄소계산기](https://www.kcen.kr/tanso/intro.green) |
| 실제 학식 주간메뉴 | 👥 | 경기대/인하대 학식 앱·식당 게시 (메뉴→레시피 매핑) |

## ② 스크린타임 → 탄소  ✅ 확보
입력: **안드로이드 `UsageStatsManager`**(앱별 사용시간, 프론트 수집) → `app_categories.csv` 매핑 → 4버킷(엔터테인먼트·소셜·게임·정보생산성) → 시간 × 계수. ⚠️ **안드로이드 네이티브 전용**(웹·iOS 미지원 = 플랫폼 제약), 스크린샷·비전 미사용.

| 필요 | 상태 | 출처 |
|---|---|---|
| 엔터테인먼트 36 gCO₂e/h | ✅ 공인 | [IEA 2020 (Carbon Brief 정리)](https://www.carbonbrief.org/factcheck-what-is-the-carbon-footprint-of-streaming-video-on-netflix/) |
| 이메일 4g/통, 통화 3.6g/분 | ✅ 공인 | [환경부·대한민국 정책브리핑](https://www.korea.kr/news/policyNewsView.do?newsId=148896769) |
| 소셜·게임·정보 카테고리 계수 | ✅ 근거화 | 모바일 데이터 ~17–25 gCO₂e/GB + 데이터레이트 추정 (게임=로컬 기기전력 위주) |

→ `digital_factors.csv` 생성 완료. ⚠️ 환경부 "동영상 1MB=11g"은 과학적 추정(시간당 36g)보다 **과대** → 체감모드 한정 표기(윤리성·정확성 가점).

## ③ 영수증 → 탄소  ✅ 확보
입력: 영수증 사진 → (**Claude API 비전**, Textract X) 품목 → 제품/식품 계수 매칭. 미매칭 시 금액기반 대체.

| 필요 | 상태 | 출처 |
|---|---|---|
| **제품별 탄소발자국**(식품·음료·생활소비) | ✅ **받음** — KEITI EPD 28품목 → product_factors.csv | KEITI 환경성적표지 유효 인증현황(2025.07) [data.go.kr](https://www.data.go.kr/data/15089157/fileData.do) |
| 식음료 품목 | ✅ ①의 food_factors 재사용 | — |
| 금액기반 대체계수(원당 kgCO₂) | 🟡 미매칭 품목용(선택) | [환경성적표지·저탄소제품](https://www.greenproduct.go.kr/epd/epd/lowCarbonIntro.do) |

## ④ 전력 → 탄소  ✅ 완료
입력: 기숙사/자취 kWh → 전력계수.

| 필요 | 상태 | 출처 |
|---|---|---|
| 전력계수 0.4951 / 0.4781 / 0.4173 | ✅ 확보 | KEITI 환경성적표지(2021) / kcen / GIR 2023 |

추가 불필요. (선택) 실제 기숙사 kWh 샘플 → 시나리오 현실성 ↑ (👥 팀).

---

## 제가 받아온 것 vs 남은 것
- ✅ **받아옴**: 전력(KEITI) · 디지털(환경부·IEA → digital_factors.csv) · **영수증 제품 28품목(KEITI EPD → product_factors.csv)** · 식품 글로벌 시드
- 👥 **팀만 가능**: 실제 학식 주간메뉴 (메뉴→레시피)
- 🟡 **선택 보강**: 국내 식품계수(①), 스크린타임 SNS/웹/게임 카테고리 보정(②)

> 4종 중 ②③④ 공인 실데이터 완료. 남은 핵심은 ① **실제 학식메뉴**(데모 설득력).
