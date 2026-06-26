"""저장 계층 인터페이스 (Protocol).

집계(§2-B)에 필요한 최소 정보만 다룬다:
- 개인 결과: user_id · dept_id · total_grams_co2e (+ tier)
- 학과 메타: name · total_students
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class ResultStore(Protocol):
    def save_personal(self, campus_id: str, result: dict[str, Any]) -> None:
        """compute() 결과(PersonalResult)를 캠퍼스 하위에 저장(upsert)."""
        ...

    def put_dept_meta(
        self, campus_id: str, dept_id: str, name: str, total_students: int
    ) -> None:
        """학과 메타(이름·총원) 저장(upsert) — 참여율 계산용."""
        ...

    def load_campus(
        self, campus_id: str
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        """(개인 결과 목록, dept_meta) 반환. aggregate() 입력 형태와 호환."""
        ...
