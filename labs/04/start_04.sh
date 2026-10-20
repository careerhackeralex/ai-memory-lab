#!/usr/bin/env bash
# make start EP=04: 앞 편(test_03)을 확인하고, 통과하지 못하면 내 mini_memory/를 backup/으로 옮긴 뒤
# labs/03/solution을 시작점으로 복사한다. 마지막에 labs/04/INTERFACE.md를 보여 준다. Hindsight는 쓰지 않는다.
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
unset UV_PROJECT_ENVIRONMENT VIRTUAL_ENV

test_03() {  # 결과 요약 한 줄을 출력하고 통과 여부를 돌려준다
  local out rc
  out=$(.venv/bin/python -m pytest labs/03/tests -q --no-header -p no:warnings -p no:cacheprovider 2>&1); rc=$?
  echo "  test_03: $(printf '%s\n' "$out" | grep -E '(passed|failed|error)' | tail -1)"
  return $rc
}

echo "== 실습 03 확인 (test_03, 내 mini_memory/) =="
copied=1
if [ ! -f mini_memory/pyproject.toml ]; then
  echo "• mini_memory/가 없음 → labs/03/solution을 시작점으로 복사"
  cp -R labs/03/solution mini_memory
elif uv sync --project mini_memory --quiet 2>/dev/null && test_03; then
  echo "• 통과 → 내 mini_memory/에서 이어 간다"
  copied=0
else
  dest="backup/mini_memory-$(date +%Y%m%d-%H%M%S)"
  mkdir -p backup && mv mini_memory "$dest"
  echo "• 통과하지 못함 → 내 코드를 $dest/로 옮기고 labs/03/solution을 시작점으로 복사"
  cp -R labs/03/solution mini_memory
fi
uv sync --project mini_memory --quiet || { echo "✗ mini_memory/.venv 준비 실패"; exit 1; }
if [ $copied = 1 ]; then
  test_03 || { echo "✗ 시작점에서도 test_03이 통과하지 않습니다."; exit 1; }
  echo "• 시작점 labs/03/solution 확인 (mcp $(mini_memory/.venv/bin/python -c 'import importlib.metadata as m; print(m.version("mcp"))'))"
fi
echo "• 미니 메모리 DB: ${MINI_MEMORY_DB:-data/mini_memory.db} ($([ -f "${MINI_MEMORY_DB:-data/mini_memory.db}" ] && echo '있음, 실습 04 코드가 열 때 새 열·events 테이블을 더한다' || echo '아직 없음, 처음 저장할 때 만들어짐'))"
echo
echo "== labs/04/INTERFACE.md =="
cat labs/04/INTERFACE.md
