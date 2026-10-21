"""저장소: SQLite claims 테이블과 remember()·recall(), 시계 함수.

계약은 labs/03/INTERFACE.md. MCP 서버(server.py)와 CLI(cli.py)가 이 함수들을 그대로 부른다.
"""
import os
import pathlib
import secrets
import sqlite3
from datetime import datetime, timezone

TYPES = ("episodic", "semantic", "procedural")

# mini_memory/src/mini_memory/store.py → 세 단계 위 폴더가 저장소
DEFAULT_DB = pathlib.Path(__file__).resolve().parents[3] / "data" / "mini_memory.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
  id          TEXT PRIMARY KEY,
  content     TEXT NOT NULL,
  type        TEXT NOT NULL CHECK (type IN ('episodic', 'semantic', 'procedural')),
  recorded_at TEXT NOT NULL
);
"""


def now() -> str:
    """현재 시각의 유일한 출처. MINI_MEMORY_NOW가 있으면 그 값(시간대 없으면 UTC). 'YYYY-MM-DDTHH:MM:SSZ'."""
    raw = os.environ.get("MINI_MEMORY_NOW")
    if raw:
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def db_path() -> pathlib.Path:
    env = os.environ.get("MINI_MEMORY_DB")
    return pathlib.Path(env) if env else DEFAULT_DB


def connect() -> sqlite3.Connection:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def check_type(type: str) -> str:
    if type not in TYPES:
        raise ValueError(f"type은 {', '.join(TYPES)} 중 하나여야 합니다 (받은 값: {type!r}). 작업 기억은 저장하지 않습니다.")
    return type


def remember(content: str, type: str) -> dict:
    """기억 한 조각(claim)을 저장하고 반환 객체를 돌려준다."""
    check_type(type)
    if not content or not content.strip():
        raise ValueError("content가 비어 있습니다.")
    claim = {"id": "clm_" + secrets.token_hex(8), "content": content, "type": type, "recorded_at": now()}
    with connect() as con:
        con.execute("INSERT INTO claims (id, content, type, recorded_at) VALUES (:id, :content, :type, :recorded_at)", claim)
    con.close()
    return claim


def recall(query: str, type: str | None = None, limit: int = 5) -> dict:
    """content에 query가 들어 있는 기억을 최근 것부터 최대 limit개. score는 이 편에서 고정 1.0."""
    if type is not None:
        check_type(type)
    if limit < 1:
        raise ValueError(f"limit은 1 이상이어야 합니다 (받은 값: {limit}).")
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    sql = "SELECT id, content, type, recorded_at FROM claims WHERE content LIKE ? ESCAPE '\\'"
    params: list = [pattern]
    if type is not None:
        sql += " AND type = ?"
        params.append(type)
    sql += " ORDER BY recorded_at DESC, rowid DESC LIMIT ?"
    params.append(limit)
    con = connect()
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    return {"results": [{**dict(r), "score": 1.0} for r in rows]}
