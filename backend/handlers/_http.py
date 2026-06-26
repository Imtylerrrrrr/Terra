"""API Gateway HTTP API 공통 헬퍼 — JSON 응답/에러 형식 (CONTRACT.md §5)."""

from __future__ import annotations

import json
from typing import Any

_HEADERS = {"Content-Type": "application/json; charset=utf-8"}


def ok(body: dict[str, Any], status: int = 200) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": _HEADERS,
        "body": json.dumps(body, ensure_ascii=False),
    }


def error(code: str, message: str, status: int = 400) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": _HEADERS,
        "body": json.dumps({"error": {"code": code, "message": message}}, ensure_ascii=False),
    }


def parse_body(event: dict[str, Any]) -> dict[str, Any]:
    """HTTP API 이벤트에서 JSON 바디를 파싱 (없으면 빈 dict)."""
    raw = event.get("body")
    if not raw:
        return {}
    if isinstance(raw, (dict, list)):
        return raw  # type: ignore[return-value]
    return json.loads(raw)
