# mini_memory

> 실습 03 참고 구현(`labs/03/solution`). 리허설에서 Claude가 `labs/03/PROMPT.md`로 만든 코드다. `make start EP=04`는 내 `mini_memory/`가 test_03을 통과하지 못할 때 내 코드를 `backup/`에 옮기고 이것을 시작점으로 복사한다.

AI 기억 설계 실습에서 직접 만드는 작은 기억 저장소. 계약은 [`labs/03/INTERFACE.md`](../labs/03/INTERFACE.md).

**claim** = 기억 한 조각. 다음 편(EP4)에서 원본 기록(이벤트)과 나눈다.

- 종류(`type`): `episodic`(일화) · `semantic`(사실·선호) · `procedural`(작업 방법, 최소 SKILL.md 형식 권장). 작업 기억은 저장하지 않는다.
- 저장: SQLite `claims` 테이블. 파일은 `MINI_MEMORY_DB`, 없으면 저장소의 `data/mini_memory.db`.
- 시계: `MINI_MEMORY_NOW`(ISO 8601)가 있으면 그 시각. UTC `YYYY-MM-DDTHH:MM:SSZ`로 저장한다.

## 실행

저장소 폴더에서:

```bash
# MCP 서버 (stdio, 도구 remember·recall)
uv run --project mini_memory mini-memory serve        # = python -m mini_memory.server

# Claude Code에 연결
claude mcp add --transport stdio mini-memory -- uv run --project mini_memory mini-memory serve

# 터미널 명령 (JSON 출력)
uv run --project mini_memory mm remember "나는 데이터 분석에 Python을 주로 쓴다" --type semantic
uv run --project mini_memory mm recall "Python" --type semantic --limit 5

# 테스트
make check EP=03
```

`cd mini_memory` 뒤에는 `uv run mm …`, `uv run mini-memory serve`로 줄여 쓸 수 있다.
