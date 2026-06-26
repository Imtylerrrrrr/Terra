"""계산엔진 테스트 (표준 unittest — 의존성 0).

실행: cd backend && python -m unittest -v
"""

import unittest

from carbon_engine import aggregate, compute, load_factors, tier_from_grams


class TierTest(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(tier_from_grams(0), "low")
        self.assertEqual(tier_from_grams(700), "low")      # 경계 포함
        self.assertEqual(tier_from_grams(700.1), "mid")
        self.assertEqual(tier_from_grams(2500), "mid")     # 경계 포함
        self.assertEqual(tier_from_grams(2500.1), "high")
        self.assertEqual(tier_from_grams(8150), "high")


class ComputeTest(unittest.TestCase):
    def setUp(self):
        self.f = load_factors()

    def _menu(self, name):
        return {"activities": [{"type": "menu", "name": name}], "needs_review": False}

    def test_vegan_is_low(self):
        r = compute(self._menu("비건비빔밥"), "u1", "cs", self.f)
        self.assertEqual(r["tier"], "low")
        self.assertLessEqual(r["total_grams_co2e"], 700)

    def test_beef_is_high(self):
        r = compute(self._menu("소불고기덮밥"), "u1", "cs", self.f)
        self.assertEqual(r["tier"], "high")
        self.assertGreater(r["total_grams_co2e"], 2500)

    def test_pork_is_mid_and_breakdown(self):
        r = compute(self._menu("제육덮밥"), "u1", "cs", self.f)
        self.assertEqual(r["tier"], "mid")
        # 돼지고기 120g×7 + 쌀밥 210g×1.0 = 840 + 210 = 1050
        self.assertAlmostEqual(r["total_grams_co2e"], 1050.0, places=1)
        labels = {b["label"] for item in r["items"] for b in item["breakdown"]}
        self.assertEqual(labels, {"돼지고기", "쌀밥"})

    def test_best_alternative_present_for_high(self):
        r = compute(self._menu("소불고기덮밥"), "u1", "cs", self.f)
        self.assertIn("best_alternative", r)
        self.assertGreater(r["best_alternative"]["saving_grams"], 0)

    def test_multi_type_activities(self):
        extraction = {
            "activities": [
                {"type": "food", "item": "닭고기", "grams": 100},     # 600
                {"type": "purchase", "item": "아메리카노", "qty": 2},   # 42
                {"type": "screentime", "item": "스마트폰", "minutes": 300},  # 9 (0.03 g/분)
                {"type": "energy", "item": "전력_가정용체감", "kwh": 1.5},   # 717.2
            ],
            "needs_review": False,
        }
        r = compute(extraction, "u1", "cs", self.f)
        self.assertAlmostEqual(r["total_grams_co2e"], 600 + 42 + 9 + 717.2, places=1)
        self.assertEqual(len(r["items"]), 4)

    def test_unmapped_key_sets_needs_review(self):
        extraction = {"activities": [{"type": "food", "item": "없는음식", "grams": 100}]}
        r = compute(extraction, "u1", "cs", self.f)
        self.assertTrue(r.get("needs_review"))
        self.assertEqual(r["total_grams_co2e"], 0.0)


class AggregateTest(unittest.TestCase):
    def test_participation_and_avg(self):
        personal = [
            {"user_id": "u1", "dept_id": "cs", "total_grams_co2e": 600.0},
            {"user_id": "u2", "dept_id": "cs", "total_grams_co2e": 800.0},
            {"user_id": "u3", "dept_id": "me", "total_grams_co2e": 3000.0},
        ]
        dept_meta = {
            "cs": {"name": "컴퓨터공학과", "total_students": 200},
            "me": {"name": "기계공학과", "total_students": 100},
        }
        out = aggregate(personal, dept_meta, "main")["campus_system"]

        cs = next(d for d in out["departments"] if d["dept_id"] == "cs")
        self.assertEqual(cs["participants"], 2)
        self.assertEqual(cs["participation_rate"], round(2 / 200, 4))
        self.assertAlmostEqual(cs["avg_grams_co2e"], 700.0, places=1)
        self.assertEqual(cs["tier"], "low")

        me = next(d for d in out["departments"] if d["dept_id"] == "me")
        self.assertEqual(me["tier"], "high")

        # 캠퍼스 = 3명 / 300명
        self.assertEqual(out["participation_rate"], round(3 / 300, 4))

    def test_zero_students_safe(self):
        personal = [{"user_id": "u1", "dept_id": "x", "total_grams_co2e": 500.0}]
        out = aggregate(personal, {}, "main")["campus_system"]
        self.assertEqual(out["departments"][0]["participation_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
