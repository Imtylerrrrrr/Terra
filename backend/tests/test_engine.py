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


class UnlocksTest(unittest.TestCase):
    """도감 해금 파생 — terra_ai/gamify.unlocked_ids 와 의미 1:1 (CONTRACT §4-A)."""

    T1 = ["red_fox", "otter", "goral", "sika_deer"]                     # 0.5kg
    T2 = ["least_weasel", "spotted_seal", "lynx", "golden_bat"]         # 2kg
    T3 = ["tube_nosed_bat", "musk_deer", "asiatic_black_bear", "wolf"]  # 5kg
    T4 = ["leopard", "tiger"]                                           # 10kg

    def test_milestone_boundaries(self):
        from carbon_engine import unlocked_ids

        self.assertEqual(unlocked_ids(0), [])
        self.assertEqual(unlocked_ids(499), [])
        self.assertEqual(unlocked_ids(500), self.T1)          # 0.5kg 경계 포함
        self.assertEqual(unlocked_ids(2000), self.T1 + self.T2)
        self.assertEqual(unlocked_ids(5000), self.T1 + self.T2 + self.T3)
        self.assertEqual(unlocked_ids(12000), self.T1 + self.T2 + self.T3 + self.T4)

    def test_none_and_negative_safe(self):
        from carbon_engine import unlocked_ids

        self.assertEqual(unlocked_ids(None), [])
        self.assertEqual(unlocked_ids(-100), [])

    def test_catalog_has_14_in_order(self):
        from carbon_engine import catalog_ids

        self.assertEqual(catalog_ids(), self.T1 + self.T2 + self.T3 + self.T4)


class CatalogDriftGuardTest(unittest.TestCase):
    """백엔드 벤더 카탈로그(dex_catalog.seed.json) ↔ terra_ai/data/collection.json 동기화 강제.

    단일 진실은 terra_ai 측. 두 파일의 (id·milestone_kg)·순서가 어긋나면 실패한다.
    terra_ai 파일이 없는 환경(백엔드만 배포)에서는 skip.
    """

    def test_backend_catalog_mirrors_terra_ai(self):
        import json as _json
        from pathlib import Path

        repo_root = Path(__file__).resolve().parents[2]
        terra = repo_root / "terra_ai" / "data" / "collection.json"
        if not terra.exists():
            self.skipTest("terra_ai/data/collection.json 부재(백엔드 단독 환경)")

        backend = Path(__file__).resolve().parents[1] / "carbon_engine" / "dex_catalog.seed.json"

        def pairs(p):
            items = _json.loads(p.read_text(encoding="utf-8")).get("items", [])
            items = sorted(items, key=lambda it: it["milestone_kg"])
            return [(it["id"], it["milestone_kg"]) for it in items]

        self.assertEqual(pairs(backend), pairs(terra))


if __name__ == "__main__":
    unittest.main()
