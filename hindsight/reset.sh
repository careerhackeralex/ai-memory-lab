#!/usr/bin/env bash
# 실습 기억을 처음 상태로: 서버를 끄고 내장 DB 인스턴스 memory-lab, 미니 메모리 DB(data/mini_memory.db), 로그를 지운다.
# 받은 모델(.cache), 패키지(.venv, mini_memory/.venv), 내가 쓴 미니 메모리 코드(mini_memory/)는 남긴다.
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
MM_DB="$DATA_DIR/mini_memory.db"
if [ -f "$MM_DB" ]; then
  rm -f "$MM_DB" "$MM_DB-wal" "$MM_DB-shm" "$MM_DB-journal"
  echo "• 미니 메모리 DB 삭제 (data/mini_memory.db). 다음 저장 때 CHECK 제약과 함께 새로 만들어진다"
fi
rm -rf "$DATA_DIR/logs" "$DATA_DIR/check_01" "$DATA_DIR/check_02"
echo "• 로그 삭제 (data/logs). 다시 시작: make start EP=01 (실습 02는 EP=02, 메모를 다시 넣는다. 실습 03은 EP=03)"
