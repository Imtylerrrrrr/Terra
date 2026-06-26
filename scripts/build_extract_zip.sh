#!/usr/bin/env bash
# Terra — /extract Lambda 배포 zip 빌더 (콘솔 수동 배포용).
#
# 왜: 해커톤 제한계정은 SAM/CloudFormation 불확실 → 콘솔 수동 배포.
#     extract 는 anthropic(+pydantic-core 등 컴파일 휠) 의존이라, 빌드 OS 와 무관하게
#     **Lambda 타깃(Amazon Linux x86_64 · py3.12)** 휠로 받아야 import 에러가 안 난다.
#
# 사용: bash scripts/build_extract_zip.sh
# 결과: 리포 루트 terra-extract.zip (gitignore 대상) → Lambda 콘솔에 업로드.
#
# Lambda 설정(콘솔): 런타임 Python 3.12 · 아키텍처 x86_64 · 역할 SafeRole-netzero-12
#   · 핸들러 api.extract_handler.handler · Timeout 29s · 256MB
#   · env ANTHROPIC_API_KEY(직접 입력) · TERRA_UPLOAD_BUCKET(업로드 버킷명)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BUILD="$(mktemp -d)/terra-extract-build"
OUT="$ROOT/terra-extract.zip"

echo "[build] src=$ROOT/terra_ai → $BUILD"
mkdir -p "$BUILD"
cp -R "$ROOT/terra_ai/." "$BUILD/"

echo "[build] pip install (manylinux2014_x86_64 · cp312 · only-binary)"
python3 -m pip install -r "$BUILD/requirements.txt" -t "$BUILD" \
  --platform manylinux2014_x86_64 --implementation cp \
  --python-version 3.12 --only-binary=:all: --upgrade

echo "[build] prune (테스트·런북·캐시는 런타임 불필요)"
rm -rf "$BUILD/scripts" "$BUILD/RUNBOOK.md"
find "$BUILD" -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true

echo "[build] zip → $OUT"
rm -f "$OUT"
( cd "$BUILD" && zip -rq "$OUT" . )

echo "[build] done: $(du -h "$OUT" | cut -f1)  ($OUT)"
echo "[build] 핸들러: api.extract_handler.handler · 런타임 python3.12 · arch x86_64"
