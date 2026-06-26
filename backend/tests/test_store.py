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
        # cs 평균 = (570 + 1155) / 2 = 862.5 → mid
        self.assertAlmostEqual(depts["cs"]["avg_grams_co2e"], 862.5, places=1)
        self.assertEqual(depts["cs"]["tier"], "mid")
        self.assertEqual(depts["me"]["tier"], "high")  # 소불고기 8115

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


if __name__ == "__main__":
    unittest.main()
