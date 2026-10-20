"""저장소: SQLite events·claims 테이블과 record_event()·remember()·supersede()·recall(), 시계 함수.

계약은 labs/03/INTERFACE.md + labs/04/INTERFACE.md. MCP 서버(server.py)와 CLI(cli.py)가 이 함수들을 그대로 부른다.
- events: 원본 기록. 추가만 한다(SQLite 트리거가 DELETE와 UPDATE를 거부).
- claims: 기억 한 조각. 고칠 때는 지우지 않고 새 claim을 만들어 옛 claim을 superseded로 바꾼다.
"""
import json
import os
import pathlib
import re
import secrets
import sqlite3
import unicodedata
from datetime import datetime, timezone

TYPES = ("episodic", "semantic", "procedural")
STATUSES = ("active", "superseded")  # 뒤 편이 forgotten·quarantined(EP8), proposed·rejected(EP10)를 더한다

# mini_memory/src/mini_memory/store.py → 세 단계 위 폴더가 저장소
DEFAULT_DB = pathlib.Path(__file__).resolve().parents[3] / "data" / "mini_memory.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS claims (
  id           TEXT PRIMARY KEY,
  content      TEXT NOT NULL,
  type         TEXT NOT NULL CHECK (type IN ('episodic', 'semantic', 'procedural')),
  recorded_at  TEXT NOT NULL,
  status       TEXT NOT NULL DEFAULT 'active',
  supersedes   TEXT,
  derived_from TEXT NOT NULL DEFAULT '[]',
  quote        TEXT
);
CREATE TABLE IF NOT EXISTS events (
  id          TEXT PRIMARY KEY,
  content     TEXT,
  source      TEXT,
  recorded_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN
  SELECT RAISE(ABORT, 'events is append-only: DELETE is not allowed');
END;
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN
  SELECT RAISE(ABORT, 'events is append-only: UPDATE is not allowed');
END;
"""

# 실습 03에서 만든 claims 테이블에 이 편의 열을 더한다(기존 DB를 그대로 이어 쓴다).
CLAIM_COLUMNS = {
    "status": "TEXT NOT NULL DEFAULT 'active'",
    "supersedes": "TEXT",
    "derived_from": "TEXT NOT NULL DEFAULT '[]'",
    "quote": "TEXT",
}

CLAIM_FIELDS = "id, content, type, recorded_at, status, supersedes, derived_from"


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
    have = {row[1] for row in con.execute("PRAGMA table_info(claims)")}
    for col, decl in CLAIM_COLUMNS.items():
        if col not in have:
            con.execute(f"ALTER TABLE claims ADD COLUMN {col} {decl}")
    con.commit()
    return con


def check_type(type: str) -> str:
    if type not in TYPES:
        raise ValueError(f"type은 {', '.join(TYPES)} 중 하나여야 합니다 (받은 값: {type!r}). 작업 기억은 저장하지 않습니다.")
    return type


# ---------------------------------------------------------------- 인용 정규화

DOUBLE_QUOTES = "“”„‟″＂"  # “ ” „ ‟ ″ ＂ → "
SINGLE_QUOTES = "‘’‚‛′＇"  # ‘ ’ ‚ ‛ ′ ＇ → '
_QUOTE_TABLE = str.maketrans({**{c: '"' for c in DOUBLE_QUOTES}, **{c: "'" for c in SINGLE_QUOTES}})


def normalize(text: str) -> str:
    """인용 비교용 정규화(INTERFACE.md): NFC → 따옴표 통일 → 모든 공백 덩어리를 공백 하나로 → 앞뒤 공백 제거."""
    text = unicodedata.normalize("NFC", text).translate(_QUOTE_TABLE)
    return re.sub(r"\s+", " ", text).strip()


# ---------------------------------------------------------------- 근거(derived_from)와 인용 검사

def _check_sources(con: sqlite3.Connection, derived_from: list[str] | None, quote: str | None) -> list[str]:
    ids = list(derived_from or [])
    for i in ids:
        if not isinstance(i, str) or not (i.startswith("evt_") or i.startswith("clm_")):
            raise ValueError(f"derived_from에는 이벤트 id(evt_…)나 claim id(clm_…)만 넣습니다 (받은 값: {i!r}).")
    events = {}
    for i in ids:
        table = "events" if i.startswith("evt_") else "claims"
        row = con.execute(f"SELECT id, content FROM {table} WHERE id = ?", (i,)).fetchone()
        if row is None:
            raise ValueError(f"derived_from의 {i}가 없습니다.")
        if table == "events":
            events[i] = row["content"]
    if quote is not None:
        if not quote.strip():
            raise ValueError("quote가 비어 있습니다.")
        if not events:
            raise ValueError("quote를 주려면 derived_from에 원문 이벤트 id(evt_…)가 하나 이상 있어야 합니다.")
        q = normalize(quote)
        if not any(c is not None and q in normalize(c) for c in events.values()):
            raise ValueError(f"인용 검사 실패: quote가 derived_from 이벤트({', '.join(events)})의 원문에 없습니다. 저장하지 않았습니다.")
    return ids


def _claim_row(row: sqlite3.Row) -> dict:
    d = dict(row)
    d["derived_from"] = json.loads(d.get("derived_from") or "[]")
    return d


def _insert_claim(con, content: str, type: str, derived: list[str], quote: str | None, supersedes: str | None) -> dict:
    claim = {"id": "clm_" + secrets.token_hex(8), "content": content, "type": type, "recorded_at": now(),
             "status": "active", "supersedes": supersedes, "derived_from": derived}
    con.execute(
        "INSERT INTO claims (id, content, type, recorded_at, status, supersedes, derived_from, quote) "
        "VALUES (?, ?, ?, ?, 'active', ?, ?, ?)",
        (claim["id"], content, type, claim["recorded_at"], supersedes, json.dumps(derived), quote),
    )
    return claim


# ---------------------------------------------------------------- 함수 (MCP 도구·CLI 공용)

def record_event(content: str, source: str | None = None) -> dict:
    """원본 기록(이벤트)을 추가한다. 이벤트는 고치거나 지우지 않는다."""
    if not content or not content.strip():
        raise ValueError("content가 비어 있습니다.")
    event = {"id": "evt_" + secrets.token_hex(8), "content": content, "source": source, "recorded_at": now()}
    con = connect()
    try:
        with con:
            con.execute("INSERT INTO events (id, content, source, recorded_at) VALUES (:id, :content, :source, :recorded_at)", event)
    finally:
        con.close()
    return event


def remember(content: str, type: str, derived_from: list[str] | None = None, quote: str | None = None) -> dict:
    """기억 한 조각(claim)을 저장한다. quote가 있으면 derived_from 이벤트 원문에 있어야 저장한다."""
    check_type(type)
    if not content or not content.strip():
        raise ValueError("content가 비어 있습니다.")
    con = connect()
    try:
        with con:
            derived = _check_sources(con, derived_from, quote)
            return _insert_claim(con, content, type, derived, quote, None)
    finally:
        con.close()


def supersede(old_id: str, content: str, type: str | None = None,
              derived_from: list[str] | None = None, quote: str | None = None) -> dict:
    """새 claim을 만들고 옛 claim을 superseded로 바꾼다. 옛 content는 그대로 둔다."""
    if not content or not content.strip():
        raise ValueError("content가 비어 있습니다.")
    con = connect()
    try:
        with con:
            old = con.execute("SELECT id, type, status FROM claims WHERE id = ?", (old_id,)).fetchone()
            if old is None:
                raise ValueError(f"대체할 claim {old_id!r}가 없습니다.")
            if old["status"] != "active":
                raise ValueError(f"{old_id}는 이미 {old['status']} 상태라 다시 대체할 수 없습니다. 이력은 recall(include_history=true)로 봅니다.")
            new_type = check_type(type) if type is not None else old["type"]
            derived = _check_sources(con, derived_from, quote)
            cur = con.execute("UPDATE claims SET status = 'superseded' WHERE id = ? AND status = 'active'", (old_id,))
            if cur.rowcount != 1:
                raise ValueError(f"{old_id}는 이미 대체되었습니다.")
            return _insert_claim(con, content, new_type, derived, quote, old_id)
    finally:
        con.close()


def recall(query: str, type: str | None = None, limit: int = 5, include_history: bool = False) -> dict:
    """content에 query가 들어 있는 기억. 기본은 active만 최근 것부터, include_history면 모든 상태를 (recorded_at, id) 오름차순."""
    if type is not None:
        check_type(type)
    if limit < 1:
        raise ValueError(f"limit은 1 이상이어야 합니다 (받은 값: {limit}).")
    pattern = "%" + query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    sql = f"SELECT {CLAIM_FIELDS} FROM claims WHERE content LIKE ? ESCAPE '\\'"
    params: list = [pattern]
    if type is not None:
        sql += " AND type = ?"
        params.append(type)
    if include_history:
        # 최근 limit개를 고른 뒤 시간 순으로 돌려준다
        sql = f"SELECT * FROM ({sql} ORDER BY recorded_at DESC, id DESC LIMIT ?) ORDER BY recorded_at ASC, id ASC"
    else:
        sql += " AND status = 'active' ORDER BY recorded_at DESC, rowid DESC LIMIT ?"
    params.append(limit)
    con = connect()
    try:
        rows = con.execute(sql, params).fetchall()
    finally:
        con.close()
    return {"results": [{**_claim_row(r), "score": 1.0} for r in rows]}
