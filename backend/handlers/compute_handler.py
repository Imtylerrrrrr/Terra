"""POST /compute — { user_id, dept_id, extraction, campus_id? } → PersonalResult(§2-A).

CONTRACT.md §5. Lambda(Python) + API Gateway HTTP API.
계산 후 결과를 저장(집계용). campus_id 는 선택(기본 "main").

도감 해금(§2-A unlocks): compute() 는 stateless(unlocks: [])이므로, 핸들러가
사용자별 누적 절감(best_alternative.saving_grams 합산)을 store(USER#)에 누적하고
unlocked_ids(누적)로 unlocks 를 채운다.
"""

from __future__ import annotations

import json
from typing import Any

from carbon_engine import compute, unlocked_ids
from store import ResultStore, get_store

from ._http import error, ok, parse_body

_DEFAULT_CAMPUS = "main"


def _saving_grams(result: dict[str, Any]) -> float:
    """이번 계산의 절감량(gCO2e). best_alternative 없거나 비정상이면 0."""
    alt = result.get("best_alternative")
    if not isinstance(alt, dict):
        return 0.0
    try:
        saving = float(alt.get("saving_grams", 0))
    except (TypeError, ValueError):
        return 0.0
    return saving if saving > 0 else 0.0


def handler(event: dict[str, Any], _context: Any = None, store: ResultStore | None = None) -> dict[str, Any]:
    store = store or get_store()
    try:
        body = parse_body(event)
    except json.JSONDecodeError:
        return error("invalid_json", "요청 바디가 올바른 JSON이 아닙니다.")

    user_id = body.get("user_id")
    dept_id = body.get("dept_id")
    extraction = body.get("extraction")
    campus_id = body.get("campus_id", _DEFAULT_CAMPUS)

    if not user_id or not dept_id:
        return error("missing_field", "user_id 와 dept_id 는 필수입니다.")
    if not isinstance(extraction, dict) or "activities" not in extraction:
        return error("missing_field", "extraction(activities 포함)이 필요합니다.")

    result = compute(extraction, user_id=user_id, dept_id=dept_id)

    # 도감 해금: 이전 누적 + 이번 절감 → 해금 id. 누적/해금은 호출측(여기) 책임(§2-A).
    saving = _saving_grams(result)
    persisted = True
    try:
        prev = float(store.load_user_progress(campus_id, user_id).get("cumulative_saved_grams", 0.0))
    except Exception as exc:  # noqa: BLE001 - 로드 실패 시 0부터(하위호환), 응답으로 surface
        prev = 0.0
        persisted = False
        print(f"[compute] load_user_progress failed: {exc}")

    cumulative = round(prev + saving, 1)
    unlocks = unlocked_ids(cumulative)
    result["unlocks"] = unlocks

    # 집계용 개인 결과 + 사용자 진행상태 저장 (best-effort: 실패해도 계산 결과는 반환)
    try:
        store.save_personal(campus_id, result)
        store.save_user_progress(campus_id, user_id, cumulative, unlocks)
    except Exception as exc:  # noqa: BLE001 - 저장 실패를 응답으로 surface
        persisted = False
        print(f"[compute] persist failed: {exc}")

    payload = dict(result)
    payload["persisted"] = persisted
    return ok(payload)
