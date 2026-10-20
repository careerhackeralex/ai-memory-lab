"""test_04_supersede: t1에 'Acme 팀 플랜은 월 9,900원'(semantic)을 저장하고, t2에 12,900원으로 type을 생략하고 supersede한다.

- 기본 recall의 results에는 새 claim만 있다(옛 claim은 빠짐).
- 옛 claim은 지워지지 않고 status=superseded, content는 그대로다.
- 새 claim.supersedes = 옛 id, 새 claim.type = semantic(옛 claim의 type), recorded_at = t2.
"""
from conftest import NEW_PRICE, OLD_PRICE, T1, T1Z, T2, T2Z, db_rows, find


def test_04_supersede(server, db):
    s1 = server(now=T1)
    old = s1.call("remember", {"content": OLD_PRICE, "type": "semantic"})
    assert old["recorded_at"] == T1Z
    s1.close()

    s2 = server(now=T2)
    new = s2.call("supersede", {"old_id": old["id"], "content": NEW_PRICE})
    assert str(new.get("id", "")).startswith("clm_") and new["id"] != old["id"], f"supersede 반환 객체: {new}"
    assert new.get("supersedes") == old["id"], f"새 claim.supersedes는 옛 id여야 합니다: {new}"
    assert new.get("recorded_at") == T2Z, f"새 claim.recorded_at은 t2: {new}"

    r = s2.call("recall", {"query": "Acme 팀 플랜"})
    ids = [x.get("id") for x in r["results"]]
    assert ids == [new["id"]], f"기본 recall에는 새 claim만 있어야 합니다: {r['results']}"
    hit = r["results"][0]
    assert hit["content"] == NEW_PRICE and hit["type"] == "semantic", f"새 claim은 옛 claim의 type(semantic)을 잇습니다: {hit}"
    assert hit.get("status") == "active" and hit.get("supersedes") == old["id"] and hit.get("recorded_at") == T2Z, hit

    hist = s2.call("recall", {"query": "Acme 팀 플랜", "include_history": True, "limit": 20})
    o = find(hist["results"], old["id"])
    assert o, f"include_history에 옛 claim이 있어야 합니다: {hist}"
    assert o.get("status") == "superseded" and o["content"] == OLD_PRICE and o["recorded_at"] == T1Z, f"옛 claim: {o}"

    rows = db_rows(db, "SELECT content, status FROM claims WHERE id = ?", (old["id"],))
    assert rows == [(OLD_PRICE, "superseded")], f"SQLite의 옛 claim 행(지우거나 content를 바꾸면 안 됨): {rows}"
