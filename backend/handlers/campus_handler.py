"""GET /campus/{campus_id} → AggregateResult(§2-B).

CONTRACT.md §5. 데모/스켈레톤: 개인 결과·학과 메타는 DynamoDB 조회 자리에 placeholder.
주영이 DB 연동 시 _load_* 두 함수만 교체하면 됨.
"""

from __future__ import annotations

from typing import Any

from carbon_engine import aggregate

from ._http import error, ok


def _load_personal_results(campus_id: str) -> list[dict[str, Any]]:
    """TODO(주영): DynamoDB 에서 campus_id 의 모든 개인 결과 조회. 현재는 빈 목록."""
    return []


def _load_dept_meta(campus_id: str) -> dict[str, dict[str, Any]]:
    """TODO(주영): DynamoDB 에서 학과 메타(name, total_students) 조회."""
    return {}


def handler(event: dict[str, Any], _context: Any = None) -> dict[str, Any]:
    path_params = event.get("pathParameters") or {}
    campus_id = path_params.get("campus_id")
    if not campus_id:
        return error("missing_field", "campus_id 경로 파라미터가 필요합니다.", status=404)

    results = _load_personal_results(campus_id)
    dept_meta = _load_dept_meta(campus_id)
    return ok(aggregate(results, dept_meta, campus_id))
