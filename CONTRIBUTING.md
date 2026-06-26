# 기여 가이드 — Terra 🌱

Terra 팀(5명)이 무박 2일 동안 깔끔하게 협업하기 위한 **커밋 규칙 & 브랜치 전략**입니다.
복잡한 도구 없이 약속만 지키면 됩니다.

---

## 1. 커밋 메시지 규칙

### 형식
```
type(scope): 설명
```
- **설명은 한글 / 영어 둘 다 OK** — 각자 편한 쪽, 한 커밋 안에서는 일관성 유지
- 제목 한 줄 **50자 이내**, 끝에 **마침표 X**
- 본문은 선택 — 필요할 때만 빈 줄 후 "왜"를 적기

### type (6종)
| type | 의미 |
|---|---|
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 (README·가이드 등) |
| `style` | 포맷·세미콜론 등 — **동작 변화 없음** |
| `refactor` | 리팩터 — **동작 동일** |
| `chore` | 설정·빌드·잡일 |

### scope (작업 영역 = 누가 어디를 건드렸는지) — **생략 가능**
| scope | 영역 | 주 담당 |
|---|---|---|
| `ai` | Bedrock 멀티모달·RAG·계수 매핑 | 민지 |
| `be` | Lambda·API Gateway·계산엔진·통합 | 주영 |
| `fe` | Kiro 화면·입력 UX | 연성 |
| `3d` | three.js 행성·캠퍼스 우주 | 연성 |
| `data` | 가상 학생·식단·통학 데이터 | 관성 |
| `design` | 화면 설계·비주얼·발표 | 승빈 |
| `infra` | AWS 설정·배포 | 주영 |
| `docs` | 프로젝트 문서 | 전원 |

> 영역이 모호하거나 전체에 걸치면 scope 생략 → `docs: README 갱신`
> 필요하면 scope는 자유롭게 추가하세요.

### 예시
```
feat(be): 계산엔진 배출량 산출 API 추가
feat(be): add emission calculation API
fix(ai): 품목 추출 수량 누락 수정
fix(ai): fix missing quantity in extraction
feat(3d): 학과 행성 로우폴리 모델 추가
docs: README 데이터 흐름도 갱신
chore: .gitignore에 .env 추가
```

---

## 2. 브랜치 전략 (경량 PR)

```
main ──────●───────●───────●     ← 항상 시연·발표 가능 상태 (직접 push 지양)
      feat/be-calc │       │
              ●────┘       │
      fix/ai-qty-bug       │
                   ●───────┘     ← 작업 브랜치 → PR → 머지
```

- **`main` 규칙**: 항상 데모 가능해야 함. 깨진 코드 올리지 않기. (통합 담당 주영 기준)
- **작업 브랜치명**: `<type>/<scope>-<short-desc>` — **영어 권장** (터미널·도구 호환)
  ```
  feat/be-calc-engine
  fix/ai-qty-bug
  feat/3d-planet-model
  ```
- **흐름**
  1. `main`에서 분기 → 작업
  2. 작업 중 **자주** `git pull origin main` (충돌 조기 해소)
  3. 완료되면 **PR 생성** → **주영이 가볍게 확인 후 머지**

```bash
git checkout main && git pull
git checkout -b feat/be-calc-engine
# ...작업...
git push -u origin feat/be-calc-engine
# GitHub에서 PR 생성 → 주영 머지
```

---

## 3. 커밋 템플릿 설정 (각자 1회만)

`git commit` 시 에디터에 양식이 자동으로 떠서 규칙을 안 봐도 됩니다.
clone 후 한 번만 실행하세요:

```bash
git config commit.template .gitmessage
```

> ⚠️ 이 설정은 clone마다 따로 — 각 팀원이 각자 자기 환경에서 1회 실행해야 적용됩니다.

---

## 4. AI 툴로 커밋할 때

> `.gitmessage` 템플릿은 **사람이 직접 `git commit` 할 때만** 뜹니다.
> AI 툴은 보통 `git commit -m "..."` 으로 바로 커밋해서 템플릿을 안 거치므로,
> 같은 규칙을 각 AI가 자동으로 읽는 파일에도 넣어뒀습니다 (내용 동일):

| AI 툴 | 자동으로 읽는 파일 |
|---|---|
| Claude (Code/Pro) | `CLAUDE.md` |
| Gemini | `GEMINI.md` |
| Kiro | `.kiro/steering/commit-convention.md` |

AI에게 커밋을 시켜도 위 형식(`type(scope): 설명`)을 따르게 됩니다.
규칙을 바꾸면 **이 4개 파일(`CONTRIBUTING.md`·`CLAUDE.md`·`GEMINI.md`·Kiro steering)** 을 함께 수정하세요.
