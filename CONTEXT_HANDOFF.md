# Terra 작업 핸드오프 (프론트 데모 UX 다듬기)

> 새 세션은 이 파일 읽고 이어가면 됨. **커밋 금지 — 로컬에서 계속 작업 중.**
> 셸: PowerShell(`&&` 대신 `;`). 데모 서버: 레포 루트에서 `python -m http.server 8012` → http://localhost:8012/frontend/demo/

## 브랜치 / PR
- 작업 브랜치: `feat/fe-demo-ux-polish` (← 지금 이 브랜치에서 작업)
- 원격 tip: `origin/feat/fe-demo-ux-polish` = `036a327` (push 됨)
- **PR**: `feat/fe-demo-ux-polish` → `main` 으로 생성되어 있음 (gh CLI 없음 → PR은 브라우저에서 관리)

## ⚠️ 미커밋 변경 (지금 워킹트리에 있음 — 이어서 작업할 부분)
1. `frontend/demo/planet.html` (M) — ⓐ 좌측 세로 스택(`.side-actions`)에 `📖 정령 도감` 버튼 추가 → `terra_dex.html`. ⓑ **모바일(≤600px) UX**: 좌측 3버튼(AI코치/탄소/정령도감)을 `☰ 메뉴` 토글(`.side-toggle`, `#sideToggle`)로 접고 누르면 `.side-actions.open`으로 펼침. ⓒ 모바일에서 `.avatar-btn`(학과뷰)·`.dex-toggle`(아바타뷰)을 **로그아웃 버튼 아래**(top:52px,right:14px)로 이동. ⓓ **갤럭시뷰**: `.brand`(TERRA) 숨김 + `.addbox2`(캠퍼스 추가) top:12px(=TERRA 자리). ⓔ **☰ 메뉴를 뷰별로 배치**: 갤럭시 top:52px(캠퍼스추가 아래)·학과 top:100px(학과추가 아래)·아바타 top:52px(뒤로가기 아래) — `body[data-view] .side-actions` 모바일 규칙.
2. `frontend/demo/terra_dex.html` (M) — **main 신버전(오픈북 UI, design-dex) 채택**(684줄) + 좌상단 `← 행성으로`(`.planet-back`) 재이식. (구버전 1995f3f 폐기)
3. `frontend/demo/dex_book.png` (신규) — 신버전 오픈북 배경(~1.4MB)
4. `frontend/demo/terra_coaching.html` (M) — **모바일(≤600px)**: `.brand`(TERRA.) 숨김 · `.cta`("이 제안들을 실천할게요!") 숨김 · 말풍선(`.speech-bubble`) 숨김 → 마스코트 클릭 팁을 **마스코트 왼쪽 `.tip-side`(`#tipSide`)** 에 표시(`showTip()`이 양쪽에 set). tip-side는 **박스 없이 텍스트만**(배경/테두리/패딩 제거, text-shadow만). 데스크톱은 기존 말풍선 유지.
5. `CONTEXT_HANDOFF.md` — 이 파일

> 검증(2026-06-27, 모바일 375px, computed style): planet 메뉴 토글·버튼 재배치 OK / coaching TERRA·실천버튼·말풍선 숨김+tip-side OK. **스크린샷 도구가 캔버스 때문에 실패** → 시각 확인은 사용자 폰에서. **미세조정 후보: `.tip-side` 위치(left:1%,width:40%)가 마스코트 왼쪽 빈공간에 잘 맞는지.**

## 이미 커밋됨 (브랜치 `feat/fe-demo-ux-polish`, push 완료, 036a327까지)
- `feat(fe)`: planet 로그아웃 버튼 + 도감 동물 **클릭/탭으로 추가**(모바일 드래그 대체)
- `feat(fe)`: planet **AI 코치 진입 버튼**(🤖, 탄소 위) + 코칭 페이지 `← 행성으로`
- `fix(fe)`: **모바일 터치로 은하·행성 위치 이동**(터치가 회전만 되던 버그)
- `feat(fe)`: 탄소측정 홈 뒤로가기 화살표 → **`행성으로`** 텍스트(카테고리 `‹`는 유지)
- `fix(fe)`: 도감 **배지 정합성**(스폰 성공 시에만 부착·drop도 tryRelease 경유) + **아바타 뷰에서 동물 우클릭/길게눌러 제거**(`removeCreature`, GLB 캐시라 dispose 안 함·재추가 스케일 보정)
  - = 주영 PR 리뷰 반영분. (로그아웃 세션 정리는 → 로그인이 localStorage 미사용이라 변경 불필요로 확인)

## 데모 구조 (`frontend/demo/`)
- `index.html`=로그인(세션 저장 없음) → `planet.html`(메인 3D, 좌측 버튼 스택·우상단 로그아웃/📖 도감 패널) → `carbon.html`(탄소측정) / `terra_coaching.html`(AI 코치) / `terra_dex.html`(정령 도감)
- 좌측 버튼 스택 순서: 🤖 AI 코치 · 🌿 탄소 측정 · 📖 정령 도감

## ⚠️ 꼭 알아둘 것 (충돌/중복 주의)
- **terra_dex 버전 충돌 = 해결됨**: main 신버전(오픈북, `dex_book.png`)을 채택해 로컬 `terra_dex.html`을 교체하고 `← 행성으로` 버튼만 재이식. 구버전(1995f3f) 폐기. → 새 main 위로 rebase 시 terra_dex.html은 거의 동일(내 추가는 `<body>` 직후 `.planet-back` 블록뿐)이라 충돌 최소.
- 브랜치가 옛 main 기반 → 머지 전 **새 main 위로 rebase 권장**. (rebase/push 시 `.git/rebase-merge` 삭제 실패 메시지는 OneDrive 잠금 탓·무해 → `Remove-Item -Recurse -Force .git\rebase-merge`로 정리)
- **도감 진입점 2개**: 우상단 `📖 도감`(planet 내장 해금 패널) + 좌측 `📖 정령 도감`(풀 페이지). 의도된 것이나 헷갈리면 라벨 조정.

## 다음 액션 후보
1. ✅ 완료: 정령 도감 버튼 + terra_dex(신버전) 흐름 검증 (planet→정령 도감→오픈북→← 행성으로)
2. ✅ 완료: main 신버전 terra_dex.html 채택 + `← 행성으로` 재이식 + `dex_book.png` 반입
3. 남음: 새 main 위로 rebase → 커밋(제안: `feat(fe): planet 좌측 버튼 스택·정령 도감(신버전) 진입`) → PR 푸시
   — **단, 사용자 지시 전까지 커밋 금지** (지금은 로컬 작업만)
