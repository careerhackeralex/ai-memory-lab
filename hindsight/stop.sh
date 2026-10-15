#!/usr/bin/env bash
# Hindsight를 끈다. 서버가 내장 DB(pg0)도 함께 멈춘다. 데이터는 지우지 않는다.
set -euo pipefail
source "$(dirname "$0")/_common.sh"

if pid=$(server_pid); then
  kill "$pid"
  for _ in $(seq 1 60); do kill -0 "$pid" 2>/dev/null || break; sleep 1; done
  kill -0 "$pid" 2>/dev/null && { echo "✗ pid $pid가 60초 안에 끝나지 않았습니다."; exit 1; }
  echo "• Hindsight 종료 (pid $pid)"
else
  echo "• 실행 중인 Hindsight가 없습니다."
fi
rm -f "$PID_FILE"
# 서버가 비정상 종료돼 DB만 남은 경우 정리
if [ -x "$VENV/bin/python" ]; then
  PG0=$(pg0_bin)
  if "$PG0" info --name "$PG0_INSTANCE" 2>/dev/null | grep -q "is running"; then
    "$PG0" stop --name "$PG0_INSTANCE" >/dev/null && echo "• 내장 DB $PG0_INSTANCE 정지"
  fi
fi
