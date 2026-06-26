#!/usr/bin/env python3
"""데모 시드 — 캠퍼스에 학과 메타 + 샘플 개인 결과 적재.

왜 필요한가:
  aggregate()(§2-B)는 **개인 결과**를 기준으로 departments 를 만든다. 그래서
  학과 메타만 넣으면 집계가 빈 채로 나온다 → 메타 + 샘플 결과를 함께 적재한다.
  배포 직후 1회 실행하면 GET /campus/{id} 가 의미있는 행성 집계를 반환한다.

사용:
  TERRA_TABLE=<테이블명> python scripts/seed.py --campus main   # 실제 DynamoDB 적재
  python scripts/seed.py                                        # 드라이런(인메모리→집계 출력)

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
# 학과별 tier 가 갈리도록 구성: design=낮음 / cs=보통 / mech=높음.
_DEPTS = [
    ("cs", "컴퓨터공학과", 20, ["제육덮밥", "제육덮밥", "비건비빔밥", "잔치국수"]),
    ("design", "디자인학과", 8, ["비건비빔밥", "비건비빔밥", "잔치국수"]),
    ("mech", "기계공학과", 12, ["소불고기덮밥", "제육덮밥", "소불고기덮밥"]),
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


def main() -> None:
    ap = argparse.ArgumentParser(description="Terra 데모 시드 적재")
    ap.add_argument("--campus", default="main", help='캠퍼스 id (기본 "main")')
    args = ap.parse_args()

    store = seed(args.campus)
    backend = "DynamoDB" if os.environ.get("TERRA_TABLE") else "InMemory(드라이런)"

    results, dept_meta = store.load_campus(args.campus)
    agg = aggregate(results, dept_meta, args.campus)
    print(f"[seed] backend={backend} campus={args.campus} depts={len(dept_meta)} results={len(results)}")
    print(json.dumps(agg, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
