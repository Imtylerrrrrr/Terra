"""게이미피케이션 lane 스모크 — 도감 해금 로직 검증 (순수, AWS 불필요).

사용: python3 terra_ai/scripts/smoke_gamify.py   (PASS면 exit 0)
계약: CONTRACT §2-A unlocks · §4-A 마일스톤 0.5/2/5/10 kg.
도감 id 단일 진실 = 프론트 3D DEX(이슈 #16) — unlocks가 그 id와 1:1.
숫자(누적 절감)는 호출측 → 이 모듈은 마일스톤 비교만(환각0).
"""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent.parent))

from terra_ai.gamify import newly_unlocked, next_milestone, progress, unlocked_ids

fails = []

# 티어별 종 (collection.json·프론트 DEX와 동일 순서)
T1 = ["red_fox", "otter", "goral", "sika_deer"]              # 0.5kg
T2 = ["least_weasel", "spotted_seal", "lynx", "golden_bat"]  # 2kg
T3 = ["tube_nosed_bat", "musk_deer", "asiatic_black_bear", "wolf"]  # 5kg
T4 = ["leopard", "tiger"]                                    # 10kg


def check(name, cond):
    print(f"  {'✅' if cond else '❌'} {name}")
    if not cond:
        fails.append(name)


# 1) 마일스톤 경계 — 0.5kg=500g 해금, 직전엔 미해금
check("절감 0g → 해금 없음", unlocked_ids(0) == [])
check("절감 499g → 아직 해금 없음", unlocked_ids(499) == [])
check("절감 500g(0.5kg) → 티어1 4종 동시 해금", unlocked_ids(500) == T1)

# 2) 누적 증가 → 티어 누적 해금 (오름차순·중복 없음)
check("절감 2kg → 티어1+2 (8종)", unlocked_ids(2000) == T1 + T2)
check("절감 5kg → 티어1+2+3 (12종)", unlocked_ids(5000) == T1 + T2 + T3)
check("절감 10kg+ → 전종(14)", unlocked_ids(12000) == T1 + T2 + T3 + T4)

# 3) 매직모먼트 — 이번 절감으로 새로 해금된 것만
check("499g→500g: 티어1 새로 해금", newly_unlocked(499, 500) == T1)
check("500g→2000g: 티어2만 새로(티어1 제외)", newly_unlocked(500, 2000) == T2)
check("증가 없음(2000→2000) → 신규 없음", newly_unlocked(2000, 2000) == [])
check("한 번에 0→5kg: 티어1+2+3 동시 해금", newly_unlocked(0, 5000) == T1 + T2 + T3)

# 4) 다음 마일스톤 넛지 — 남은 양(coach용)
nm = next_milestone(200)
check("0.2kg에서 다음=여우(티어1), 남은 300g, 4종 동시",
      nm and nm["id"] == "red_fox" and nm["remaining_grams"] == 300.0 and nm["count"] == 4)
nm2 = next_milestone(2000)
check("2kg 달성 후 다음=티어3 선두(작은관코박쥐), 남은 3000g, 4종",
      nm2 and nm2["id"] == "tube_nosed_bat" and nm2["remaining_grams"] == 3000.0 and nm2["count"] == 4)
check("전종 해금 시 next=None", next_milestone(99999) is None)

# 5) progress 요약 — 프론트 바인딩 형태
p = progress(2000)
check("progress 키(unlocked/total/next)",
      set(p) == {"unlocked", "total", "next"})
check("progress.total = 카탈로그 14종", p["total"] == 14)
check("progress.unlocked = 8종(티어1+2)", p["unlocked"] == T1 + T2)
check("progress.next = 작은관코박쥐(다음 5kg)", p["next"]["id"] == "tube_nosed_bat")

# 6) 숫자 무결성 — None/0 안전
check("None 입력 → 해금 없음(크래시X)", unlocked_ids(None) == [])

print(f"\n{'전부 PASS ✅' if not fails else f'실패 {len(fails)}건: {fails}'}")
sys.exit(1 if fails else 0)
