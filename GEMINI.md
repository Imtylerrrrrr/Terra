# Terra — AI 에이전트 지침

> 캠퍼스 일상(식단·통학·전력)을 탄소배출량으로 환산하고 학과별 3D 행성으로 시각화하는 AWS 해커톤 프로젝트. 5명이 병렬로 작업한다.

## 커밋 규칙 (필수)

이 레포에서 **git 커밋을 만들 때는 반드시** 아래 형식을 따른다 — `git commit -m "..."` 으로 직접 커밋할 때도 동일하게:

```
type(scope): 설명
```

- **설명**: 한글/영어 모두 허용 · 50자 이내 · 끝에 마침표 없음
- **type**: `feat`(새 기능) · `fix`(버그) · `docs`(문서) · `style`(포맷, 동작 변화 X) · `refactor`(리팩터, 동작 동일) · `chore`(설정·잡일)
- **scope** (생략 가능): `ai` · `be` · `fe` · `3d` · `data` · `design` · `infra` · `docs`
- 예시
  - `feat(be): 계산엔진 배출량 산출 API 추가`
  - `fix(ai): fix missing quantity in extraction`

## 브랜치 규칙

- `main`은 **항상 시연 가능 상태** — 깨진 코드를 push 하지 않는다.
- 작업은 `<type>/<scope>-<short-desc>` 브랜치에서 (영어 권장): 예 `feat/ai-extraction`.
- 완료되면 **PR 생성 → 주영(통합 담당)이 확인 후 머지**.

전체 규칙·브랜치 전략은 레포 루트의 **CONTRIBUTING.md** 참고.
