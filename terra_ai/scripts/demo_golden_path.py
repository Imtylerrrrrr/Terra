"""데모 골든패스 — 한 사이클을 한 번에 보여주는 시연 대본 (MOCK, AWS·배포 불필요).

흐름:  fixture → /extract → compute(엔진) → coach(대안 추천) → 대안 전환(절감 누적)
       → gamify 도감 해금(매직모먼트) → coach 넛지(다음 해금까지)

숫자는 전부 엔진/모듈에서 **파생**(하드코딩 X) — "해석=LLM, 숫자=코드, 계산=코드" 원칙 실연.
배포 없이도 전체 파이프라인이 도는 것을 증명하는 리허설/회귀 스크립트.

사용: python3 terra_ai/scripts/demo_golden_path.py   (PASS면 exit 0)
"""
import json
import os
import sys
import pathlib

os.environ.setdefault("MOCK", "1")
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))              # terra_ai (추출·gamify·coach)
sys.path.insert(0, str(ROOT / "backend"))  # carbon_engine (엔진, 주영)

from terra_ai.api.extract_handler import handler
from carbon_engine import compute
from terra_ai.gamify import newly_unlocked, progress, unlocked_ids
from terra_ai.bedrock.coach import coach

# 도감 id → 한글명 (예쁜 출력용)
_CATALOG = {
    it["id"]: it["name"]
    for it in json.loads(
        (ROOT / "terra_ai" / "data" / "collection.json").read_text(encoding="utf-8")
    )["items"]
}

fails = []


def check(name, cond):
    if not cond:
        fails.append(name)
    return cond


def names(ids):
    return ", ".join(f"{_CATALOG.get(i, i)}({i})" for i in ids)


print("=" * 64)
print("  Terra 골든패스 데모 — 입력 → 계산 → 코칭 → 도감 해금")
print("=" * 64)

# ── 1) 입력: 학식 사진(소불고기덮밥) → /extract ──────────────────────────────
print("\n[1] 📸 학식 입력 → /extract (Claude API 추출 · 여기선 fixture 폴백)")
r = handler({"body": json.dumps({"fixture": "소불고기덮밥"})})
ext = json.loads(r["body"])
menu = ext["activities"][0].get("name")
print(f"    추출: {json.dumps(ext['activities'], ensure_ascii=False)}")
check("extract 200 + 메뉴", r["statusCode"] == 200 and menu == "소불고기덮밥")

# ── 2) 계산: compute(엔진) → 개인 결과 ───────────────────────────────────────
print("\n[2] 🧮 compute (엔진 × 공공계수) → 탄소 + tier")
res = compute(ext, "u_demo", "cs")
total = res["total_grams_co2e"]
alt = res["best_alternative"]
print(f"    {menu} = {total:.0f}g  → tier={res['tier']} (행성 황폐 🌫️)")
print(f"    더 나은 선택: {alt['name']} = {alt['grams_co2e']:.0f}g "
      f"(−{alt['saving_grams']:.0f}g)")
check("소불고기덮밥 high (킬샷)", res["tier"] == "high")
check("best_alternative 존재", bool(alt.get("saving_grams")))

# ── 3) 코칭: coach (대안 추천, 누적 0) ───────────────────────────────────────
print("\n[3] 🌱 coach (문장=LLM·여기선 규칙기반 / 숫자=코드)")
c0 = coach(res, "컴퓨터공학과")
print(f"    planet : {c0['planet_line']}")
print(f"    action : {c0['next_action']}")
check("coach 4필드 + tone", set(c0) >= {"planet_line", "next_action", "tone"})

# ── 4) 행동: 대안으로 전환 → 절감 누적 ───────────────────────────────────────
saved = alt["saving_grams"]
print(f"\n[4] ✅ 사용자가 '{alt['name']}'로 전환 → 누적 절감 +{saved:.0f}g")
before, after = 0.0, saved

# ── 5) 매직모먼트: 도감 해금 ─────────────────────────────────────────────────
print("\n[5] 🎉 도감 해금 (누적 절감 → CONTRACT §2-A unlocks)")
fresh = newly_unlocked(before, after)
prog = progress(after)
print(f"    누적 {after / 1000:.2f}kg → 새로 해금 {len(fresh)}종: {names(fresh)}")
print(f"    도감 진행: {len(prog['unlocked'])}/{prog['total']}종 수집")
check("절감으로 도감 해금됨", len(fresh) > 0)
check("unlocks가 카탈로그 id와 정합", set(prog["unlocked"]) <= set(_CATALOG))
# 프론트 연동: 이 배열을 그대로 applyUnlocks(ids) 에 전달
print(f"    → 프론트 applyUnlocks({json.dumps(unlocked_ids(after))})")

# ── 6) 넛지: 다음 해금까지 (coach + 누적) ────────────────────────────────────
print("\n[6] 🧭 coach 넛지 (누적 절감 전달 → 다음 해금 유도)")
nxt = prog["next"]
c1 = coach(res, "컴퓨터공학과", cumulative_saving_grams=after)
print(f"    action : {c1['next_action']}")
if nxt:
    check("넛지에 다음 해금 종 포함", nxt["name"] in c1["next_action"])
    print(f"    (다음: {nxt['name']} — {nxt['remaining_grams'] / 1000:.1f}kg 남음)")
else:
    check("전종 해금 시 넛지 생략", "해금" not in c1["next_action"])

print("\n" + "=" * 64)
print(f"  {'골든패스 PASS ✅ — 배포 없이 전체 사이클 동작' if not fails else f'실패 {len(fails)}건: {fails}'}")
print("=" * 64)
sys.exit(1 if fails else 0)
