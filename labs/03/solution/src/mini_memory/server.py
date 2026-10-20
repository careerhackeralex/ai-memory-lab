"""stdio MCP 서버: 도구 remember, recall. `python -m mini_memory.server`로도 뜬다.

stdout에는 MCP 메시지만 쓴다. 로그는 stderr로.
"""
import logging
import sys

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from mini_memory import store

mcp = MCPServer("mini-memory")


@mcp.tool()
def remember(content: str, type: str) -> dict:
    """기억 한 조각(claim)을 저장한다. type은 episodic(일화)·semantic(사실·선호)·procedural(작업 방법, SKILL.md 형식 권장) 중 하나."""
    try:
        return store.remember(content, type)
    except ValueError as e:
        raise ToolError(str(e)) from e


@mcp.tool()
def recall(query: str, type: str | None = None, limit: int = 5) -> dict:
    """content에 query가 들어 있는 기억을 최근 것부터 찾는다. type을 주면 그 종류만."""
    try:
        return store.recall(query, type, limit)
    except ValueError as e:
        raise ToolError(str(e)) from e


def main() -> None:
    logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
    mcp.run("stdio")


if __name__ == "__main__":
    main()
