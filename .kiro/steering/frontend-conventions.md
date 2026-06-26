---
inclusion: always
---

# Terra 프론트엔드 컨벤션 (Kiro 스캐폴딩 기준)

> 연성·관성·승빈이 화면/3D를 만들 때 Kiro가 **일관된 코드**를 뽑도록 하는 규칙.
> **값(색·폰트·간격 실수치)의 단일 진실은 `DESIGN.md`** — 승빈이 1일차에 확정.
> 이 문서는 "어떻게 쓸지(구조·규칙)", DESIGN.md는 "무슨 값일지"를 담는다.

## 1. 디자인 토큰 (하드코딩 금지)

- 색·간격·폰트는 **CSS 변수(토큰)** 로만 쓴다. `#1a1a1a`, `16px` 같은 **리터럴 금지**.
- 토큰 이름은 아래 스킴을 따른다. **값은 DESIGN.md 확정 전까지 placeholder** — 승빈이 채운다.

```css
:root {
  /* 기본 — TODO: 승빈/DESIGN.md 확정 */
  --color-bg: ;            /* 캠퍼스 "우주" 배경 (다크 권장) */
  --color-surface: ;       /* 카드·패널 */
  --color-text: ;
  --color-text-muted: ;
  --color-accent: ;        /* 주요 액션/CTA */

  /* 탄소 배출 단계 → 행성 비주얼 매핑 (의미 기반) */
  --color-emission-low: ;
  --color-emission-mid: ;
  --color-emission-high: ;

  /* 간격 — 4px 베이스 스케일 */
  --space-1: 4px;  --space-2: 8px;  --space-3: 12px;
  --space-4: 16px; --space-5: 24px; --space-6: 32px;

  --radius: 8px;           /* TODO 확정 */
  --font-sans: ;           /* TODO 확정 */
}
```

## 2. 컴포넌트 · 파일 규칙

- 컴포넌트는 **작게** — 한 컴포넌트 = 한 책임. 200줄 넘으면 쪼갠다.
- 입력 UX와 3D 씬은 **폴더 분리**: 화면(`input`·`result`)과 3D(`scene`·`planet`)를 섞지 않는다.
- 도메인 타입(품목·수량·배출량 JSON)은 **한 곳에 모아** 백엔드와 형식을 맞춘다 — ⚠️ *JSON 형식 합의가 1일차 최우선 병목*이므로 주영과 계약(타입)부터 고정. → `src/types/contract.ts` (CONTRACT.md 박제).
- 스택 **확정: React + Vite + TypeScript** (README 기준). 3D는 three.js.
- 디렉터리 트리 (`frontend/`):

```
frontend/
├─ package.json
├─ tsconfig.json
└─ src/
   ├─ types/      # 도메인 타입 (CONTRACT.md 박제) — contract.ts
   ├─ lib/        # 순수 로직 (탄소→비주얼 매핑) — emissionVisual.ts
   ├─ styles/     # 디자인 토큰 — tokens.css
   ├─ input/      # 입력 화면·폼 (식단·스크린타임·영수증·전력)
   ├─ result/     # 결과 화면 (수치·코칭)
   ├─ scene/      # three.js 씬·렌더 루프
   └─ planet/     # 행성/도감 3D 컴포넌트
```

## 3. three.js 성능 예산 (로우폴리)

행성이 **데모 노트북에서 버벅이면 치명적**이라 처음부터 지킨다 (`/benchmark`로 검증):

- **로우폴리 유지** + **기존 자산 재활용** (역할 플랜 명시).
- geometry·material은 **재사용**, 학과 행성처럼 같은 게 여러 개면 **InstancedMesh**.
- 컴포넌트 unmount 시 `geometry.dispose()`·`material.dispose()`·`texture.dispose()`.
- 렌더 루프(`requestAnimationFrame`) 안에서 **객체 생성 금지**(GC 스파이크). 라이트 수 최소화.
- 목표: 데모 환경에서 부드러운 프레임 + 빠른 초기 로드.

## 4. 사용성 체크 (심사 10점 직결)

- 입력 폼(**식단·스크린타임·영수증·전력**)은 **로딩 / 에러 / 빈 상태**를 반드시 가진다.
- 색 대비·키보드 포커스·이미지 대체텍스트 등 기본 접근성 충족.
- 결과(3D 행성)는 숫자만이 아니라 **무엇을 의미하는지** 짧게 라벨/설명.
- 시연 해상도(노트북/프로젝터) 기준으로 깨지지 않게.

## 5. 탄소 → 비주얼 매핑

- 배출량을 행성의 **색(emission 토큰)·크기·링** 등으로 표현. 매핑 함수는 한 곳에 모은다.
- 임계값(low/mid/high 경계)은 **계산엔진·계수 확정 후**(주영/민지) 값 채움 — 그 전엔 `TODO`.
