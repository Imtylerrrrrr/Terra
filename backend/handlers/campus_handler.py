"""GET /campus/{campus_id} → AggregateResult(§2-B).

CONTRACT.md §5. 저장소에서 개인 결과 + 학과 메타를 읽어 집계.
"""

from __future__ import annotations

from typing import Any

from carbon_engine import aggregate
from store import ResultStore, get_store

from ._http import error, ok


def handler(event: dict[str, Any], _context: Any = None, store: ResultStore | None = None) -> dict[str, Any]:
    store = store or get_store()

    path_params = event.get("pathParameters") or {}
    campus_id = path_params.get("campus_id")
    if not campus_id:
        return error("missing_field", "campus_id 경로 파라미터가 필요합니다.", status=404)

    results, dept_meta = store.load_campus(campus_id)
    return ok(aggregate(results, dept_meta, campus_id))
