"""stdio MCP 서버: 도구 remember, recall(실습 03) + record_event, supersede(실습 04). `python -m mini_memory.server`로도 뜬다.

stdout에는 MCP 메시지만 쓴다. 로그는 stderr로.
"""
import logging
import sys

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from mini_memory import store

mcp = MCPServer("mini-memory")


def _call(fn, *args, **kwargs) -> dict:
    try:
        return fn(*args, **kwargs)
    except ValueError as e:
        raise ToolError(str(e)) from e


@mcp.tool()
def record_event(content: str, source: str | None = None) -> dict:
    """원본 기록(이벤트)을 추가한다. 이벤트는 고치거나 지우지 않는다. source는 출처 표시(예: 대화 파일 이름과 턴). id는 evt_로 시작."""
    return _call(store.record_event, content, source)


@mcp.tool()
def remember(content: str, type: str, derived_from: list[str] | None = None, quote: str | None = None) -> dict:
    """기억 한 조각(claim)을 저장한다. type은 episodic(일화)·semantic(사실·선호)·procedural(작업 방법, SKILL.md 형식 권장).
    derived_from은 근거 id 목록(이벤트 evt_… 또는 claim clm_…). quote(원문 인용)를 주면 derived_from 이벤트 원문에 있어야 저장한다."""
    return _call(store.remember, content, type, derived_from, quote)


@mcp.tool()
def supersede(old_id: str, content: str, type: str | None = None,
              derived_from: list[str] | None = None, quote: str | None = None) -> dict:
    """사실이 바뀌었을 때 쓴다: 새 claim을 만들고 옛 claim(old_id)은 지우지 않고 status=superseded로 바꾼다.
    type을 생략하면 옛 claim의 type. 이미 대체된 claim은 다시 대체할 수 없다."""
    return _call(store.supersede, old_id, content, type, derived_from, quote)


@mcp.tool()
def recall(query: str, type: str | None = None, limit: int = 5, include_history: bool = False) -> dict:
    """content에 query가 들어 있는 기억을 찾는다. 기본은 현재 사실(active)만 최근 것부터.
    include_history=true면 대체된 옛 claim까지 recorded_at 오름차순(같으면 id 순)으로."""
    return _call(store.recall, query, type, limit, include_history)


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    mcp.run("stdio")


if __name__ == "__main__":
    main()
