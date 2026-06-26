"""결과 저장 계층 — 개인 결과 저장 + 캠퍼스 집계 조회.

- 로컬/테스트: InMemoryResultStore (의존성 0)
- Lambda: DynamoResultStore (boto3, 환경변수 TERRA_TABLE)

get_store()가 환경에 맞는 구현을 반환한다.
"""

from __future__ import annotations

import os

from .base import ResultStore
from .memory import InMemoryResultStore

__all__ = ["ResultStore", "InMemoryResultStore", "get_store"]

_default_store: ResultStore | None = None


def get_store() -> ResultStore:
    """TERRA_TABLE 환경변수가 있으면 DynamoDB, 없으면 인메모리(프로세스 공유)."""
    global _default_store
    table = os.environ.get("TERRA_TABLE")
    if table:
        from .dynamo import DynamoResultStore  # boto3 lazy import

        return DynamoResultStore(table)
    if _default_store is None:
        _default_store = InMemoryResultStore()
    return _default_store
