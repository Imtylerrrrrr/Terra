"""DynamoDB 단일 테이블 저장소 (Lambda 런타임).

테이블 키 스키마 (단일 테이블):
  PK = "CAMPUS#{campus_id}"
  SK = "RESULT#{dept_id}#{user_id}"   개인 결과
     | "DEPT#{dept_id}"               학과 메타
     | "USER#{user_id}"               사용자 도감 진행(누적 절감·해금)
→ 캠퍼스 1건 Query(PK)로 결과 + 학과 메타를 한 번에 조회.
  (load_campus 는 RESULT#/DEPT# 만 취함 → USER# 는 집계에 영향 없음)

boto3 는 Lambda 런타임 기본 제공. 로컬 테스트는 InMemoryResultStore 사용.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any


def _pk(campus_id: str) -> str:
    return f"CAMPUS#{campus_id}"


class DynamoResultStore:
    def __init__(self, table_name: str, *, table: Any = None) -> None:
        self._table_name = table_name
        self._table = table  # 주입 가능(테스트). 없으면 lazy 생성.

    def _t(self) -> Any:
        if self._table is None:
            import boto3  # lazy: 로컬/테스트에서 불필요

            self._table = boto3.resource("dynamodb").Table(self._table_name)
        return self._table

    def save_personal(self, campus_id: str, result: dict[str, Any]) -> None:
        self._t().put_item(
            Item={
                "PK": _pk(campus_id),
                "SK": f"RESULT#{result['dept_id']}#{result['user_id']}",
                "user_id": result["user_id"],
                "dept_id": result["dept_id"],
                # float → Decimal (DynamoDB Number)
                "total_grams_co2e": Decimal(str(result["total_grams_co2e"])),
                "tier": result.get("tier"),
            }
        )

    def put_dept_meta(
        self, campus_id: str, dept_id: str, name: str, total_students: int
    ) -> None:
        self._t().put_item(
            Item={
                "PK": _pk(campus_id),
                "SK": f"DEPT#{dept_id}",
                "dept_id": dept_id,
                "name": name,
                "total_students": int(total_students),
            }
        )

    def load_user_progress(self, campus_id: str, user_id: str) -> dict[str, Any]:
        resp = self._t().get_item(Key={"PK": _pk(campus_id), "SK": f"USER#{user_id}"})
        item = resp.get("Item")
        if not item:
            return {"cumulative_saved_grams": 0.0, "unlocks": [], "processed_requests": []}
        return {
            "cumulative_saved_grams": float(item.get("cumulative_saved_grams", 0)),
            "unlocks": list(item.get("unlocks", [])),
            "processed_requests": list(item.get("processed_requests", [])),
        }

    def save_user_progress(
        self,
        campus_id: str,
        user_id: str,
        cumulative_saved_grams: float,
        unlocks: list[str],
        processed_requests: list[str] | None = None,
    ) -> None:
        self._t().put_item(
            Item={
                "PK": _pk(campus_id),
                "SK": f"USER#{user_id}",
                "user_id": user_id,
                # float → Decimal (DynamoDB Number)
                "cumulative_saved_grams": Decimal(str(round(float(cumulative_saved_grams), 1))),
                "unlocks": list(unlocks),
                "processed_requests": list(processed_requests or []),
            }
        )

    def load_campus(
        self, campus_id: str
    ) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
        from boto3.dynamodb.conditions import Key

        results: list[dict[str, Any]] = []
        dept_meta: dict[str, dict[str, Any]] = {}

        kwargs: dict[str, Any] = {"KeyConditionExpression": Key("PK").eq(_pk(campus_id))}
        while True:
            resp = self._t().query(**kwargs)
            for it in resp.get("Items", []):
                sk = str(it.get("SK", ""))
                if sk.startswith("RESULT#"):
                    results.append(
                        {
                            "user_id": it["user_id"],
                            "dept_id": it["dept_id"],
                            "total_grams_co2e": float(it["total_grams_co2e"]),
                            "tier": it.get("tier"),
                        }
                    )
                elif sk.startswith("DEPT#"):
                    dept_meta[it["dept_id"]] = {
                        "name": it.get("name", it["dept_id"]),
                        "total_students": int(it.get("total_students", 0)),
                    }
            lek = resp.get("LastEvaluatedKey")
            if not lek:
                break
            kwargs["ExclusiveStartKey"] = lek

        return results, dept_meta
