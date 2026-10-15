#!/usr/bin/env bash
# 실습 기억을 처음 상태로: 서버를 끄고 내장 DB 인스턴스 memory-lab과 로그를 지운다.
# 받은 모델(.cache)과 패키지(.venv)는 남긴다.
set -euo pipefail
source "$(dirname "$0")/_common.sh"

bash "$ROOT/hindsight/stop.sh"
if [ -x "$VENV/bin/python" ]; then
  PG0=$(pg0_bin)
  if "$PG0" list 2>/dev/null | grep -q "^ *$PG0_INSTANCE "; then
    "$PG0" drop --name "$PG0_INSTANCE" --force >/dev/null
    echo "• 내장 DB 인스턴스 $PG0_INSTANCE 삭제 (~/.pg0/instances/$PG0_INSTANCE)"
  else
    echo "• 내장 DB 인스턴스 $PG0_INSTANCE가 없습니다."
  fi
fi
rm -rf "$DATA_DIR/logs" "$DATA_DIR/check_01"
echo "• 로그 삭제 (data/logs). 다시 시작: make start EP=01"
