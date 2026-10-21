"""test_04_events_append_only: events는 추가만 된다. SQLite에 직접 DELETE하거나 content를 바꾸는 UPDATE를 하면
트리거가 막아 sqlite3.DatabaseError 계열 예외가 나고, 행 수와 내용이 그대로다.

- 오류 문구는 SQLite 버전마다 달라 보지 않는다(예외 종류만).
- 바꾸는 글은 두 가지: 길이가 다른 글, 같은 글자 수의 다른 글. 이 편에는 redacted_spans 칸이 아직 없으므로 content만 바꾼다.
- 이 검사는 뒤 편에서도 유지된다(EP8 가드가 통과시키는 '가림' 변경은 시험하지 않는다).
"""
import sqlite3

import pytest

from conftest import db_rows

ORIGINAL = "Acme에서 메일 왔는데 4월부터 팀 플랜이 월 12,900원으로 오른대."
SAME_LENGTH = "Acme에서 메일 왔는데 4월부터 팀 플랜이 월 15,900원으로 오른대."
LONGER = ORIGINAL + " (수정됨)"


def snapshot(db):
    return db_rows(db, "SELECT id, content, source, recorded_at FROM events ORDER BY id")


def test_04_events_append_only(server, db):
    s = server()
    e1 = s.call("record_event", {"content": ORIGINAL, "source": "conv_04.jsonl#t05"})
    e2 = s.call("record_event", {"content": "결제는 매달 5일에 팀 카드로 나가.", "source": "conv_04.jsonl#t03"})
    for e in (e1, e2):
        assert str(e.get("id", "")).startswith("evt_"), f"이벤트 id는 evt_로 시작: {e}"
    assert len(SAME_LENGTH) == len(ORIGINAL)
    before = snapshot(db)
    assert len(before) == 2, f"events 행이 2개여야 합니다: {before}"

    attempts = [
        ("DELETE FROM events WHERE id = ?", (e1["id"],)),
        ("DELETE FROM events", ()),
        ("UPDATE events SET content = ? WHERE id = ?", (LONGER, e1["id"])),
        ("UPDATE events SET content = ? WHERE id = ?", (SAME_LENGTH, e1["id"])),
    ]
    con = sqlite3.connect(db)
    try:
        for sql, params in attempts:
            with pytest.raises(sqlite3.DatabaseError):
                with con:  # 실패하면 롤백
                    con.execute(sql, params)
    finally:
        con.close()
    assert snapshot(db) == before, "events 행 수나 내용이 바뀌었습니다(트리거가 막아야 합니다)"
