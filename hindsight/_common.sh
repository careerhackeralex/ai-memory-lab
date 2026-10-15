# start.sh/stop.sh/reset.sh 공용. source로 읽는다.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$ROOT/hindsight/.env"
DATA_DIR="$ROOT/data"
LOG_FILE="$DATA_DIR/logs/hindsight.log"
PID_FILE="$DATA_DIR/hindsight.pid"
PG0_INSTANCE="memory-lab"
BANK_ID="lab"
VENV="$ROOT/.venv"
export HF_HOME="$ROOT/.cache/huggingface"

load_env() {
  [ -f "$ENV_FILE" ] || { echo "✗ hindsight/.env가 없습니다: cp hindsight/.env.example hindsight/.env"; exit 1; }
  set -a; . "$ENV_FILE"; set +a
  # 강제값: 내 컴퓨터에서만, 내장 DB 인스턴스 memory-lab
  export HINDSIGHT_API_HOST=127.0.0.1
  export HINDSIGHT_API_PORT="${HINDSIGHT_API_PORT:-8888}"
  export HINDSIGHT_API_DATABASE_URL="pg0://$PG0_INSTANCE"
  PORT="$HINDSIGHT_API_PORT"
}

pg0_bin() {
  "$VENV/bin/python" -c 'import os,pg0;print(os.path.join(os.path.dirname(pg0.__file__),"bin","pg0"))'
}

server_pid() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null && cat "$PID_FILE"
}
