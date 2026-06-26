"""POST /compute — { user_id, dept_id, extraction } → PersonalResult(§2-A).

CONTRACT.md §5. Lambda(Python) + API Gateway HTTP API.
"""

from __future__ import annotations

import json
from typing import Any

from carbon_engine import compute

from ._http import error, ok, parse_body


def handler(event: dict[str, Any], _context: Any = None) -> dict[str, Any]:
    try:
        body = parse_body(event)
    except json.JSONDecodeError:
        return error("invalid_json", "요청 바디가 올바른 JSON이 아닙니다.")

    user_id = body.get("user_id")
    dept_id = body.get("dept_id")
    extraction = body.get("extraction")

    if not user_id or not dept_id:
        return error("missing_field", "user_id 와 dept_id 는 필수입니다.")
    if not isinstance(extraction, dict) or "activities" not in extraction:
        return error("missing_field", "extraction(activities 포함)이 필요합니다.")

    result = compute(extraction, user_id=user_id, dept_id=dept_id)
    return ok(result)
