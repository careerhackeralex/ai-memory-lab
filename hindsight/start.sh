#!/usr/bin/env bash
# Hindsight(hindsight-api==1.0.0)를 127.0.0.1:8888에 띄운다. 내장 DB 인스턴스 memory-lab, 뱅크 lab.
set -euo pipefail
source "$(dirname "$0")/_common.sh"

# Intel Mac: hindsight-api의 torch 휠이 없다 → hindsight-all-slim 안내
if [ "$(uname -s)" = Darwin ] && [ "$(uname -m)" = x86_64 ]; then
  echo "✗ Intel Mac은 이 스크립트로 설치되지 않습니다. labs/01/README.md의 'Intel Mac' 항목(hindsight-all-slim)을 보세요."
  exit 1
fi

load_env

# 금지·필수 설정 확인 (값은 출력하지 않는다)
case "${HINDSIGHT_API_LLM_PROVIDER:-}" in
  "") echo "✗ hindsight/.env에 HINDSIGHT_API_LLM_PROVIDER가 없습니다."; exit 1 ;;
  claude-code) echo "✗ claude-code 공급자는 이 실습에서 쓰지 않습니다. ollama 또는 API 키 공급자를 고르세요."; exit 1 ;;
esac
if [ "${HINDSIGHT_API_EMBEDDINGS_PROVIDER:-}" != onnx ]; then
  echo "✗ HINDSIGHT_API_EMBEDDINGS_PROVIDER=onnx 줄이 없습니다. .env.example에서 다시 복사하세요."; exit 1
fi

# 패키지(저장소 안 .venv)와 모델(저장소 안 .cache)이 준비됐는지
if [ ! -x "$VENV/bin/hindsight-api" ]; then
  echo "✗ .venv가 없습니다. 먼저 'make models'를 실행하세요."; exit 1
fi
if [ ! -d "$HF_HOME/hub/models--intfloat--multilingual-e5-small" ]; then
  echo "✗ 임베딩 모델이 없습니다. 먼저 'make models'를 실행하세요."; exit 1
fi
# 실행 중에는 모델을 내려받지 않는다 (make models로 받은 캐시만 읽음)
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 HF_HUB_DISABLE_TELEMETRY=1

# 이미 떠 있으면 그대로 둔다
if pid=$(server_pid); then
  echo "• Hindsight가 이미 실행 중입니다 (pid $pid)."
else
  if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "✗ 포트 $PORT를 다른 프로그램이 쓰고 있습니다:"; lsof -nP -iTCP:"$PORT" -sTCP:LISTEN
    echo "  그 프로그램을 끄거나, .env의 HINDSIGHT_API_PORT와 MCP 주소를 함께 바꾸세요."; exit 1
  fi
  mkdir -p "$DATA_DIR/logs"
  echo "• Hindsight 시작: 127.0.0.1:$PORT, 내장 DB pg0://$PG0_INSTANCE, LLM ${HINDSIGHT_API_LLM_PROVIDER}/${HINDSIGHT_API_LLM_MODEL:-기본값}"
  t0=$(date +%s)
  NO_COLOR=1 nohup "$VENV/bin/hindsight-api" --no-access-log >>"$LOG_FILE" 2>&1 &
  echo $! >"$PID_FILE"
  ok=""
  for _ in $(seq 1 300); do
    if ! kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then break; fi
    if [ "$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$PORT/health")" = 200 ]; then ok=1; break; fi
    sleep 1
  done
  if [ -z "$ok" ]; then
    echo "✗ 서버가 뜨지 않았습니다. 로그 마지막 20줄 (data/logs/hindsight.log):"; tail -20 "$LOG_FILE"; exit 1
  fi
  echo "• 준비 완료: $(( $(date +%s) - t0 ))초"
fi

# 뱅크 lab 만들기 (있으면 그대로)
curl -s -o /dev/null -X PUT -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$PORT/v1/default/banks/$BANK_ID"

echo
echo "상태"
echo "  health   : $(curl -s "http://127.0.0.1:$PORT/health" | "$VENV/bin/python" -c 'import json,sys;d=json.load(sys.stdin);print(d["status"],"/ db",d["database"])')"
echo "  version  : $(curl -s "http://127.0.0.1:$PORT/version" | "$VENV/bin/python" -c 'import json,sys;print(json.load(sys.stdin)["api_version"])')"
echo "  listen   : $(lsof -nP -iTCP:"$PORT" -sTCP:LISTEN -Fn | sed -n 's/^n//p' | sort -u | tr '\n' ' ')"
echo "  embedding: $(grep -o 'initializing ONNX provider with model [^ ]*' "$LOG_FILE" | tail -1 | awk '{print $NF}')"
echo "  MCP      : http://127.0.0.1:$PORT/mcp/$BANK_ID/"
echo "  로그     : data/logs/hindsight.log"
