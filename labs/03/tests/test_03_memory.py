"""test_03: 미니 메모리 계약 (labs/03/INTERFACE.md). 결정적이다(LLM 없음).

뒤 편이 반환 객체에 칸을 더하거나 도구를 더해도 그대로 통과하도록, 필요한 칸만 확인한다.
"""
import sqlite3

import pytest

from conftest import ALLOWED_TOOLS, is_tool_error, run_mm

SKILL = """---
name: weekly-delivery-report
description: 매주 월요일 배송 지연 리포트를 만들 때 쓴다.
---
1. 지난주 배송 데이터를 내려받는다.
2. 지역별 지연율을 계산한다.
3. 표를 팀 채널에 올린다."""


def find(results: list, cid: str) -> dict | None:
    return next((r for r in results if r.get("id") == cid), None)


def test_03_tools(server):
    """tools/list에 remember·recall이 있고, 시리즈 고정 목록 밖의 도구 이름은 없다."""
    names = set(server().tools())
    assert {"remember", "recall"} <= names, f"remember·recall이 있어야 합니다: {sorted(names)}"
    extra = names - ALLOWED_TOOLS
    assert not extra, f"고정 목록 밖의 도구: {sorted(extra)} (허용: {sorted(ALLOWED_TOOLS)})"


def test_03_type_enum(server, db):
    """type은 episodic·semantic·procedural만. opinion·working은 서버와 SQLite 둘 다 거절한다."""
    s = server()
    for bad in ("opinion", "working"):
        r = s.call_raw("remember", {"content": f"{bad} 종류는 저장하지 않는다", "type": bad})
        assert is_tool_error(r), f"type={bad!r}는 오류여야 합니다: {r}"
    for t, content in (("episodic", "2026-03-01 주간 회의에서 대시보드를 발표했다"),
                       ("semantic", "벨로랩 데이터팀 팀장은 최서진이다"),
                       ("procedural", SKILL)):
        m = s.call("remember", {"content": content, "type": t})
        assert m.get("type") == t and m.get("content") == content, f"{t} 저장 반환 객체: {m}"
        assert str(m.get("id", "")).startswith("clm_"), f"id는 clm_로 시작: {m.get('id')}"
    con = sqlite3.connect(db)
    try:
        for bad in ("opinion", "working"):
            with pytest.raises(sqlite3.IntegrityError):
                con.execute("INSERT INTO claims (id, content, type, recorded_at) VALUES (?, ?, ?, ?)",
                            (f"clm_check_{bad}", "CHECK 제약 확인", bad, "2026-03-02T00:00:00Z"))
    finally:
        con.close()


def test_03_roundtrip(server):
    """remember → recall('Python')이 {"results": [...]}로 같은 항목을 돌려준다."""
    s = server()
    m = s.call("remember", {"content": "나는 데이터 분석에 Python을 주로 쓴다", "type": "semantic"})
    for k in ("id", "content", "type", "recorded_at"):
        assert k in m, f"remember 반환 객체에 {k} 칸이 없습니다: {m}"
    assert m["id"].startswith("clm_")
    r = s.call("recall", {"query": "Python"})
    assert isinstance(r, dict) and isinstance(r.get("results"), list), f'recall은 {{"results": [...]}} 객체: {r}'
    hit = find(r["results"], m["id"])
    assert hit, f"recall 결과에 방금 저장한 {m['id']}가 없습니다: {r}"
    assert hit["content"] == m["content"] and hit["type"] == "semantic"
    for k in ("recorded_at", "score"):
        assert k in hit, f"recall 항목에 {k} 칸이 없습니다: {hit}"


def test_03_type_filter(server):
    """recall(query, type='episodic')에는 일화 기억만 나온다."""
    s = server()
    ep = s.call("remember", {"content": "어제 회의에서 배송 지연 대시보드를 처음 보여 줬다", "type": "episodic"})
    se = s.call("remember", {"content": "배송 지연 대시보드는 매주 월요일에 갱신된다", "type": "semantic"})
    r = s.call("recall", {"query": "대시보드", "type": "episodic"})
    types = [x.get("type") for x in r["results"]]
    assert find(r["results"], ep["id"]), f"일화 기억이 결과에 없습니다: {r}"
    assert not find(r["results"], se["id"]) and set(types) == {"episodic"}, f"episodic만 나와야 합니다: {types}"


def test_03_clock(server):
    """MINI_MEMORY_NOW=2026-03-02T09:00:00+09:00 → recorded_at '2026-03-02T00:00:00Z'(UTC, 초 단위, Z)."""
    s = server(now="2026-03-02T09:00:00+09:00")
    m = s.call("remember", {"content": "시계 주입 확인용 기억", "type": "semantic"})
    assert m["recorded_at"] == "2026-03-02T00:00:00Z", f"remember의 recorded_at: {m['recorded_at']!r}"
    hit = find(s.call("recall", {"query": "시계 주입"})["results"], m["id"])
    assert hit and hit["recorded_at"] == "2026-03-02T00:00:00Z", f"recall의 recorded_at: {hit}"


def test_03_persist(server):
    """서버를 껐다 켜도(같은 MINI_MEMORY_DB) 기억이 남는다."""
    s1 = server()
    m = s1.call("remember", {"content": "하린의 고양이 이름은 보리다", "type": "semantic"})
    s1.close()
    s2 = server()
    assert find(s2.call("recall", {"query": "보리"})["results"], m["id"]), "재시작 뒤 recall에 기억이 없습니다"


def test_03_schema(server, db):
    """SQLite에 claims 테이블과 id·content·type·recorded_at 열이 있다(최소 스키마만)."""
    server().call("remember", {"content": "스키마 확인용 기억", "type": "semantic"})
    assert db.exists(), f"MINI_MEMORY_DB 경로에 DB 파일이 없습니다: {db}"
    con = sqlite3.connect(db)
    try:
        cols = {row[1] for row in con.execute("PRAGMA table_info(claims)")}
    finally:
        con.close()
    assert cols, "claims 테이블이 없습니다"
    missing = {"id", "content", "type", "recorded_at"} - cols
    assert not missing, f"claims에 없는 열: {sorted(missing)}"


def test_03_cli(server, db):
    """`uv run mm remember` → `uv run mm recall` JSON이 MCP recall과 같은 {"results": [...]} 모양이다."""
    m = run_mm(db, "remember", "하린은 매주 월요일 배송 리포트를 쓴다", "--type", "semantic")
    assert str(m.get("id", "")).startswith("clm_") and m.get("type") == "semantic", f"mm remember 출력: {m}"
    r = run_mm(db, "recall", "배송 리포트")
    assert isinstance(r.get("results"), list), f'mm recall 출력은 {{"results": [...]}}: {r}'
    hit = find(r["results"], m["id"])
    assert hit and {"id", "content", "type", "recorded_at", "score"} <= set(hit), f"mm recall 항목: {hit}"
    r2 = run_mm(db, "recall", "배송 리포트", "--type", "episodic", "--limit", "3")
    assert not find(r2["results"], m["id"]), "--type episodic인데 semantic 기억이 나왔습니다"
    via_mcp = server().call("recall", {"query": "배송 리포트"})
    assert set(via_mcp) >= {"results"} and find(via_mcp["results"], m["id"]), "MCP recall에 CLI로 넣은 기억이 없습니다"
