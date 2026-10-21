"""test_04_no_double_supersede: 이미 대체된 claim을 다시 supersede하면 오류이고, 아무것도 바뀌지 않는다."""
from conftest import NEW_PRICE, OLD_PRICE, db_rows, find, is_tool_error


def test_04_no_double_supersede(server, db):
    s = server()
    a = s.call("remember", {"content": OLD_PRICE, "type": "semantic"})
    b = s.call("supersede", {"old_id": a["id"], "content": NEW_PRICE})
    n = db_rows(db, "SELECT count(*) FROM claims")[0][0]

    again = s.call_raw("supersede", {"old_id": a["id"], "content": "벨로랩의 Acme 팀 플랜은 월 15,900원이다"})
    assert is_tool_error(again), f"이미 대체된 claim을 다시 대체하면 오류여야 합니다: {again}"
    assert db_rows(db, "SELECT count(*) FROM claims")[0][0] == n, "오류인데 claim이 새로 생겼습니다"
    cur = find(s.call("recall", {"query": "Acme 팀 플랜"})["results"], b["id"])
    assert cur and cur.get("status") == "active", f"현재 claim(b)은 그대로 active: {cur}"
