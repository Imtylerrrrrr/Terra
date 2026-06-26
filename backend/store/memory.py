"""인메모리 저장소 — 로컬 개발/테스트용 (의존성 0).

프로세스 수명 동안만 유지. DynamoResultStore 와 동일한 인터페이스.
"""

from __future__ import annotations

from typing import Any


class InMemoryResultStore:
    def __init__(self) -> None:
        # campus_id -> "{dept}#{user}" -> 결과
        self._results: dict[str, dict[str, dict[str, Any]]] = {}
        # campus_id -> dept_id -> {name, total_students}
        self._dept: dict[str, dict[str, dict[str, Any]]] = {}
        # campus_id -> user_id -> {cumulative_saved_grams, unlocks}
        self._progress: dict[str, dict[str, dict[str, Any]]] = {}

    def save_personal(self, campus_id: str, result: dict[str, Any]) -> None:
        key = f"{result['dept_id']}#{result['user_id']}"
        self._results.setdefault(campus_id, {})[key] = {
            "user_id": result["user_id"],
            "dept_id": result["dept_id"],
            "total_grams_co2e": result["total_grams_co2e"],
            "tier": result.get("tier"),
        }

    def put_dept_meta(
        self, campus_id: str, dept_id: str, name: str, total_students: int
    ) -> None:
        self._dept.setdefault(campus_id, {})[dept_id] = {
            "name": name,
            "total_students": int(total_students),
        }

    def load_user_progress(self, campus_id: str, user_id: str) -> dict[str, Any]:
        prog = self._progress.get(campus_id, {}).get(user_id)
        if prog is None:
            return {"cumulative_saved_grams": 0.0, "unlocks": [], "processed_requests": []}
        return {
            "cumulative_saved_grams": float(prog.get("cumulative_saved_grams", 0.0)),
            "unlocks": list(prog.get("unlocks", [])),
            "processed_requests": list(prog.get("processed_requests", [])),
        }

    def save_user_progress(
        self,
        campus_id: str,
        user_id: str,
        cumulative_saved_grams: float,
        unlocks: list[str],
        processed_requests: list[str] | None = None,
    ) -> None:
        self._progress.setdefault(campus_id, {})[user_id] = {
            "cumulative_saved_grams": round(float(cumulative_saved_grams), 1),
            "unlocks": list(unlocks),
            "processed_requests": list(processed_requests or []),
        }

    def load_campus(
        self, campus_id: str
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        results = list(self._results.get(campus_id, {}).values())
        dept_meta = {k: dict(v) for k, v in self._dept.get(campus_id, {}).items()}
        return results, dept_meta

    def clear(self) -> None:
        self._results.clear()
        self._dept.clear()
        self._progress.clear()
