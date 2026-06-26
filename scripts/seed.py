#!/usr/bin/env python3
"""데모 시드 — 캠퍼스에 학과 메타 + 샘플 개인 결과 적재.

왜 필요한가:
  aggregate()(§2-B)는 **개인 결과**를 기준으로 departments 를 만든다. 그래서
  학과 메타만 넣으면 집계가 빈 채로 나온다 → 메타 + 샘플 결과를 함께 적재한다.
  배포 직후 1회 실행하면 GET /campus/{id} 가 의미있는 행성 집계를 반환한다.

사용:
  python scripts/seed.py --api https://xxx.execute-api...amazonaws.com  # 공개 /compute로 실 테이블 시드(자격증명 불필요)
  TERRA_TABLE=<테이블명> python scripts/seed.py --campus main           # 로컬→DynamoDB 직접 적재(자격증명 필요)
  python scripts/seed.py                                               # 드라이런(인메모리→집계 출력)

비고:
  - 계수는 carbon_engine 시드값을 그대로 쓴다 → 민지 정식 계수 교체 시 자동 반영.
  - 아래 _DEPTS 의 인원·메뉴는 **임시 데모값**(관성 가상데이터로 교체 예정).
  - DynamoDB 적재는 boto3 + AWS 자격증명 필요(로컬에서 배포 테이블로 직접 쓰기).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

# backend/ 를 import 경로에 추가 (Lambda CodeUri 와 분리 유지 — 시드는 Lambda 에 안 들어감)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backend"))

from carbon_engine import aggregate, compute  # noqa: E402
from store import get_store  # noqa: E402

# (dept_id, name, total_students, [메뉴, ...])  — 메뉴는 factors.seed.json 에 존재하는 것만.
# 가상 데모 데이터: 6개 학과, 학과별 tier 가 low/mid/high 로 갈리도록 메뉴 구성.
# 메뉴 1건 = 참여자 1명(개인 결과). 참여자 수 < 총원 → participation_rate 가 100% 미만으로 자연스럽게.
_DEPTS = [
    ("cs", "컴퓨터공학과", 45, [
        "제육덮밥", "돈까스", "치킨마요덮밥", "비건비빔밥", "라면",
        "제육덮밥", "카레라이스", "비빔밥", "돈까스", "김치찌개",
        "제육덮밥", "치즈버거",
    ]),
    ("design", "디자인학과", 30, [
        "비건비빔밥", "샐러드", "잔치국수", "김밥", "비빔밥",
        "샐러드", "비건비빔밥", "잔치국수", "김밥",
    ]),
    ("mech", "기계공학과", 38, [
        "소불고기덮밥", "제육덮밥", "돈까스", "소불고기덮밥", "제육덮밥",
        "소불고기덮밥", "돈까스", "치즈버거", "소불고기덮밥", "제육덮밥",
    ]),
    ("biz", "경영학과", 60, [
        "김치찌개", "카레라이스", "치즈버거", "비빔밥", "제육덮밥",
        "돈까스", "치킨마요덮밥", "라면", "카레라이스", "비빔밥",
        "김치찌개", "치즈버거", "돈까스", "제육덮밥",
    ]),
    ("chem", "화학공학과", 33, [
        "소불고기덮밥", "돈까스", "김치찌개", "제육덮밥", "돈까스",
        "소불고기덮밥", "카레라이스", "치킨마요덮밥",
    ]),
    ("nursing", "간호학과", 50, [
        "샐러드", "비건비빔밥", "잔치국수", "김밥", "카레라이스",
        "샐러드", "비건비빔밥", "잔치국수", "비빔밥", "김밥", "라면",
    ]),
]


def seed(campus_id: str):
    store = get_store()
    for dept_id, name, total_students, menus in _DEPTS:
        store.put_dept_meta(campus_id, dept_id, name, total_students)
        for i, menu in enumerate(menus, start=1):
            result = compute(
                {"activities": [{"type": "menu", "name": menu}]},
                user_id=f"{dept_id}_u{i}",
                dept_id=dept_id,
            )
            store.save_personal(campus_id, result)
    return store


def seed_via_api(api: str, campus_id: str) -> int:
    """공개 `/compute` API 로 실 테이블 시드(자격증명·콘솔 불필요. urllib만).

    배포된 compute Lambda 가 계산+저장(RESULT#)을 수행 → GET /campus/{id} 집계가 살아난다.
    ⚠️ 한계: dept 메타(학과명·총원)는 put_dept_meta 로만 들어가는데 공개 API 엔 그 경로가
    없다 → 집계의 학과명=dept_id, participation_rate=0 (평균·tier 는 정상). 프론트에서
    dept_id→한글명 매핑으로 가린다.
    """
    import urllib.request

    api = api.rstrip("/")
    posted = 0
    for dept_id, _name, _total, menus in _DEPTS:
        for i, menu in enumerate(menus, start=1):
            body = json.dumps({
                "user_id": f"{dept_id}_u{i}",
                "dept_id": dept_id,
                "campus_id": campus_id,
                "extraction": {"activities": [{"type": "menu", "name": menu}]},
            }, ensure_ascii=False).encode()
            req = urllib.request.Request(
                f"{api}/compute", data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=20) as r:
                ok_ = r.status == 200
            print(f"  {'✅' if ok_ else '❌'} {dept_id}_u{i} ← {menu}")
            posted += 1 if ok_ else 0
    return posted


def main() -> None:
    ap = argparse.ArgumentParser(description="Terra 데모 시드 적재")
    ap.add_argument("--campus", default="main", help='캠퍼스 id (기본 "main")')
    ap.add_argument("--api", help="공개 API base URL 지정 시 /compute 로 실 테이블 시드(자격증명 불필요)")
    args = ap.parse_args()

    if args.api:
        posted = seed_via_api(args.api, args.campus)
        print(f"[seed] backend=LiveAPI campus={args.campus} posted={posted}")
        print(f"→ 확인: curl {args.api.rstrip('/')}/campus/{args.campus}")
        return

    store = seed(args.campus)
    backend = "DynamoDB" if os.environ.get("TERRA_TABLE") else "InMemory(드라이런)"

    results, dept_meta = store.load_campus(args.campus)
    agg = aggregate(results, dept_meta, args.campus)
    print(f"[seed] backend={backend} campus={args.campus} depts={len(dept_meta)} results={len(results)}")
    print(json.dumps(agg, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
