"""저장 계층 + 핸들러 통합 테스트 (InMemoryResultStore 주입, 의존성 0).

실행: cd backend && python -m unittest -v
"""

import json
import unittest

from handlers.campus_handler import handler as campus_handler
from handlers.compute_handler import handler as compute_handler
from store import InMemoryResultStore


def _compute_event(user_id, dept_id, menu, campus_id="main", request_id=None):
    payload = {
        "user_id": user_id,
        "dept_id": dept_id,
        "campus_id": campus_id,
        "extraction": {"activities": [{"type": "menu", "name": menu}]},
    }
    if request_id is not None:
        payload["request_id"] = request_id
    return {"body": json.dumps(payload)}


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


class IdempotencyTest(unittest.TestCase):
    """리뷰 ②: 같은 request_id 재시도는 누적에 두 번 더해지지 않아야(멱등)."""

    T123 = UnlockProgressTest.T1 + UnlockProgressTest.T2 + UnlockProgressTest.T3
    T1234 = T123 + UnlockProgressTest.T4

    def setUp(self):
        self.store = InMemoryResultStore()

    def test_same_request_id_is_idempotent(self):
        ev = _compute_event("u1", "cs", "소불고기덮밥", request_id="req-1")
        b1 = json.loads(compute_handler(ev, store=self.store)["body"])
        b2 = json.loads(compute_handler(ev, store=self.store)["body"])  # 재시도(같은 키)

        self.assertEqual(b1["unlocks"], self.T123)
        self.assertEqual(b2["unlocks"], self.T123)  # 두 번째도 그대로(2배 X)
        prog = self.store.load_user_progress("main", "u1")
        self.assertAlmostEqual(prog["cumulative_saved_grams"], 5736.0, delta=1.0)

    def test_distinct_request_ids_accumulate(self):
        compute_handler(_compute_event("u1", "cs", "소불고기덮밥", request_id="req-1"), store=self.store)
        b2 = json.loads(
            compute_handler(_compute_event("u1", "cs", "소불고기덮밥", request_id="req-2"), store=self.store)["body"]
        )
        self.assertEqual(b2["unlocks"], self.T1234)  # 서로 다른 키 → 정상 누적(전종)
        prog = self.store.load_user_progress("main", "u1")
        self.assertAlmostEqual(prog["cumulative_saved_grams"], 5736.0 * 2, delta=1.0)


class _LoadFailsStore:
    """load_user_progress 만 일시 실패하는 래퍼(나머지는 inner 에 위임)."""

    def __init__(self, inner):
        self._inner = inner

    def load_user_progress(self, *_a, **_k):
        raise RuntimeError("transient load failure")

    def __getattr__(self, name):
        return getattr(self._inner, name)


class LoadFailureGuardTest(unittest.TestCase):
    """리뷰 ①: 로드 실패 시 기존 누적/해금을 0부터 덮어쓰지 않아야 함."""

    T123 = UnlockProgressTest.T1 + UnlockProgressTest.T2 + UnlockProgressTest.T3

    def test_load_failure_preserves_existing_progress(self):
        inner = InMemoryResultStore()
        inner.save_user_progress("main", "u1", 9000.0, self.T123)  # 기존: 9kg·티어1~3

        store = _LoadFailsStore(inner)
        # 작은 절감 메뉴(제육 ≈765g). 버그 시 prev=0 → 누적 765 로 덮어써져 티어1만 남음.
        res = compute_handler(_compute_event("u1", "design", "제육덮밥"), store=store)
        body = json.loads(res["body"])

        self.assertEqual(res["statusCode"], 200)  # 계산 결과는 여전히 반환
        self.assertFalse(body["persisted"])  # 저장 실패 surface

        prog = inner.load_user_progress("main", "u1")  # 기존 값 보존(덮어쓰기 X)
        self.assertEqual(prog["cumulative_saved_grams"], 9000.0)
        self.assertEqual(prog["unlocks"], self.T123)


if __name__ == "__main__":
    unittest.main()
