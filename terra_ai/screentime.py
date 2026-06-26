"""
스크린타임 매핑 — 안드로이드 UsageStatsManager 앱별 사용시간 → 4버킷 digital activities.

입력(프론트/연성이 네이티브에서 수집): [{"package": "com.google.android.youtube", "minutes": 130}, ...]
출력: CONTRACT §1 digital activities [{type:digital, item:버킷, hours:X}, ...]
미등록 앱 → '정보생산성'(catch-all). 매핑표 = data/app_categories.csv (연성이 실패키지로 보강).

스크린타임은 구조화 데이터라 Bedrock 비전 불필요 — 매핑만 코드로(환각0).
"""
import json
import pathlib
from collections import defaultdict

DATA = pathlib.Path(__file__).resolve().parent / "data"
_APPS = json.loads((DATA / "factors.json").read_text(encoding="utf-8"))["app_categories"]
_MAP = {pkg: v["bucket"] for pkg, v in _APPS.items()}       # 패키지 → 버킷
_NAME = {v["app_ko"]: v["bucket"] for v in _APPS.values()}  # 한글 앱명 → 버킷

BUCKETS = {"엔터테인먼트", "소셜", "게임", "정보생산성"}
DEFAULT = "정보생산성"

def _bucket(app):
    if app in _MAP:           # 패키지 정확 매칭
        return _MAP[app]
    if app in _NAME:          # 한글 앱명 매칭
        return _NAME[app]
    if app in BUCKETS:        # 이미 버킷명이면 그대로
        return app
    return DEFAULT            # 미등록 → catch-all

def to_activities(usage):
    """usage=[{"package"|"app": str, "minutes": float}] → digital activities(시간 합산)."""
    mins = defaultdict(float)
    for u in usage:
        app = u.get("package") or u.get("app", "")
        mins[_bucket(app)] += float(u.get("minutes", 0))
    return [{"type": "digital", "item": b, "hours": round(m / 60, 2)}
            for b, m in mins.items() if m > 0]


if __name__ == "__main__":
    # 안드로이드 UsageStatsManager가 줄 법한 입력으로 검증
    demo = [{"package": "com.google.android.youtube", "minutes": 130},
            {"package": "com.instagram.android", "minutes": 60},
            {"package": "com.zhiliaoapp.musically", "minutes": 25},
            {"package": "com.pubg.imobile", "minutes": 40},
            {"package": "com.unknown.app", "minutes": 15}]   # 미등록→정보생산성
    import json
    print(json.dumps(to_activities(demo), ensure_ascii=False))
