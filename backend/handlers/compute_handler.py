"""POST /compute — { user_id, dept_id, extraction, campus_id? } → PersonalResult(§2-A).

CONTRACT.md §5. Lambda(Python) + API Gateway HTTP API.
계산 후 결과를 저장(집계용). campus_id 는 선택(기본 "main").
"""

from __future__ import annotations

import json
from typing import Any

from carbon_engine import compute
from store import ResultStore, get_store

from ._http import error, ok, parse_body

_DEFAULT_CAMPUS = "main"


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

    # 집계용 저장 (best-effort: 저장 실패해도 계산 결과는 반환)
    persisted = True
    try:
        store.save_personal(campus_id, result)
    except Exception as exc:  # noqa: BLE001 - 저장 실패를 응답으로 surface
        persisted = False
        print(f"[compute] save_personal failed: {exc}")

    payload = dict(result)
    payload["persisted"] = persisted
    return ok(payload)
