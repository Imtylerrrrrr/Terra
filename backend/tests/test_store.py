"""저장 계층 + 핸들러 통합 테스트 (InMemoryResultStore 주입, 의존성 0).

실행: cd backend && python -m unittest -v
"""

import json
import unittest

from handlers.campus_handler import handler as campus_handler
from handlers.compute_handler import handler as compute_handler
from store import InMemoryResultStore


def _compute_event(user_id, dept_id, menu, campus_id="main"):
    return {
        "body": json.dumps(
            {
                "user_id": user_id,
                "dept_id": dept_id,
                "campus_id": campus_id,
                "extraction": {"activities": [{"type": "menu", "name": menu}]},
            }
        )
    }


class StoreRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.store = InMemoryResultStore()
        self.store.put_dept_meta("main", "cs", "컴퓨터공학과", 200)
        self.store.put_dept_meta("main", "me", "기계공학과", 100)

    def test_compute_persists_and_campus_aggregates(self):
        # 3명 계산 → 저장
        r1 = compute_handler(_compute_event("u1", "cs", "비건비빔밥"), store=self.store)
        r2 = compute_handler(_compute_event("u2", "cs", "제육덮밥"), store=self.store)
        r3 = compute_handler(_compute_event("u3", "me", "소불고기덮밥"), store=self.store)
        for r in (r1, r2, r3):
            self.assertEqual(r["statusCode"], 200)
            self.assertTrue(json.loads(r["body"])["persisted"])

        # 캠퍼스 집계
        res = campus_handler({"pathParameters": {"campus_id": "main"}}, store=self.store)
        self.assertEqual(res["statusCode"], 200)
        cs_system = json.loads(res["body"])["campus_system"]

        depts = {d["dept_id"]: d for d in cs_system["departments"]}
        self.assertEqual(depts["cs"]["participants"], 2)
        self.assertEqual(depts["cs"]["participation_rate"], round(2 / 200, 4))
        # cs 평균 = (285 + 1050) / 2 = 667.5 → low
        self.assertAlmostEqual(depts["cs"]["avg_grams_co2e"], 667.5, places=1)
        self.assertEqual(depts["cs"]["tier"], "low")
        self.assertEqual(depts["me"]["tier"], "high")  # 소불고기 6021

        # 캠퍼스 = 3명 / 300명
        self.assertEqual(cs_system["participation_rate"], round(3 / 300, 4))

    def test_upsert_same_user_overwrites(self):
        compute_handler(_compute_event("u1", "cs", "소불고기덮밥"), store=self.store)
        compute_handler(_compute_event("u1", "cs", "비건비빔밥"), store=self.store)  # 갱신
        results, _ = self.store.load_campus("main")
        self.assertEqual(len(results), 1)  # 같은 user → 1건
        self.assertLessEqual(results[0]["total_grams_co2e"], 700)

    def test_empty_campus_safe(self):
        res = campus_handler({"pathParameters": {"campus_id": "none"}}, store=self.store)
        body = json.loads(res["body"])["campus_system"]
        self.assertEqual(body["departments"], [])
        self.assertEqual(body["participation_rate"], 0.0)


class ComputeValidationTest(unittest.TestCase):
    def test_missing_fields(self):
        store = InMemoryResultStore()
        res = compute_handler({"body": json.dumps({"user_id": "u1"})}, store=store)
        self.assertEqual(res["statusCode"], 400)
        self.assertEqual(json.loads(res["body"])["error"]["code"], "missing_field")


class UnlockProgressTest(unittest.TestCase):
    """도감 해금 배선 — 누적 절감(USER#) → unlocks 응답 (CONTRACT §2-A·§4-A)."""

    T1 = ["red_fox", "otter", "goral", "sika_deer"]
    T2 = ["least_weasel", "spotted_seal", "lynx", "golden_bat"]
    T3 = ["tube_nosed_bat", "musk_deer", "asiatic_black_bear", "wolf"]
    T4 = ["leopard", "tiger"]

    def setUp(self):
        self.store = InMemoryResultStore()

    def test_user_progress_round_trip(self):
        # 기본값: 없으면 0/빈배열
        prog = self.store.load_user_progress("main", "u1")
        self.assertEqual(prog["cumulative_saved_grams"], 0.0)
        self.assertEqual(prog["unlocks"], [])
        # 저장 → 재조회 라운드트립
        self.store.save_user_progress("main", "u1", 5736.0, self.T1 + self.T2 + self.T3)
        prog = self.store.load_user_progress("main", "u1")
        self.assertEqual(prog["cumulative_saved_grams"], 5736.0)
        self.assertEqual(prog["unlocks"], self.T1 + self.T2 + self.T3)

    def test_compute_accumulates_unlocks(self):
        # 소불고기덮밥: 6021g, best_alternative(비건비빔밥) 절감 ≈ 5736g
        r1 = compute_handler(_compute_event("u1", "cs", "소불고기덮밥"), store=self.store)
        body1 = json.loads(r1["body"])
        self.assertTrue(body1["persisted"])
        # 누적 5736 → 0.5/2/5kg 마일스톤 통과(12종), 10kg 미만
        self.assertEqual(body1["unlocks"], self.T1 + self.T2 + self.T3)

        # 같은 유저 한 번 더 → 누적 ≈ 11472 ≥ 10kg → 전종(14)
        r2 = compute_handler(_compute_event("u1", "cs", "소불고기덮밥"), store=self.store)
        body2 = json.loads(r2["body"])
        self.assertEqual(body2["unlocks"], self.T1 + self.T2 + self.T3 + self.T4)

        prog = self.store.load_user_progress("main", "u1")
        self.assertAlmostEqual(prog["cumulative_saved_grams"], 5736.0 * 2, delta=1.0)

    def test_low_saving_unlocks_tier1_only(self):
        # 제육덮밥: 1050g, 절감 ≈ 765g → 0.5kg만 통과(티어1 4종)
        r = compute_handler(_compute_event("u1", "design", "제육덮밥"), store=self.store)
        self.assertEqual(json.loads(r["body"])["unlocks"], self.T1)

    def test_user_progress_excluded_from_aggregate(self):
        # USER# 항목이 학과 집계(§2-B)를 오염시키지 않아야 함
        self.store.put_dept_meta("main", "cs", "컴퓨터공학과", 200)
        compute_handler(_compute_event("u1", "cs", "비건비빔밥"), store=self.store)
        results, _ = self.store.load_campus("main")
        self.assertEqual(len(results), 1)  # 개인 결과 1건만(USER# 제외)


if __name__ == "__main__":
    unittest.main()
