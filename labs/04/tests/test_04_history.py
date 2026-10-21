"""test_04_history: include_history=true면 results가 (recorded_at, id) 오름차순이다.
t1·t2의 두 claim은 시각 순으로, 같은 시각에 기록된 claim끼리는 id 순으로 나온다. limit이 작으면 최근 것부터 limit개를 고른 뒤
오름차순으로 돌려준다."""
from conftest import NEW_PRICE, OLD_PRICE, T1, T1Z, T2, T2Z


def test_04_history(server):
    s1 = server(now=T1)
    a = s1.call("remember", {"content": OLD_PRICE, "type": "semantic"})
    s1.close()
    s2 = server(now=T2)
    b = s2.call("supersede", {"old_id": a["id"], "content": NEW_PRICE})
    c = s2.call("remember", {"content": "Acme 팀 플랜 관리자는 하린이다", "type": "semantic"})
    d = s2.call("remember", {"content": "2026-04-01 Acme 팀 플랜 요금 인상 메일을 받았다", "type": "episodic"})

    r = s2.call("recall", {"query": "Acme 팀 플랜", "include_history": True, "limit": 20})
    got = [(x["recorded_at"], x["id"]) for x in r["results"]]
    assert {a["id"], b["id"], c["id"], d["id"]} <= {i for _, i in got}, f"이력에 네 claim이 모두 있어야 합니다: {got}"
    assert got == sorted(got), f"(recorded_at, id) 오름차순이어야 합니다: {got}"
    assert got[0] == (T1Z, a["id"]), f"t1의 옛 claim이 맨 앞: {got}"
    same_time = [i for t, i in got if t == T2Z]
    assert same_time == sorted([b["id"], c["id"], d["id"]]), f"같은 시각(t2)의 claim은 id 순: {same_time}"

    three = s2.call("recall", {"query": "Acme 팀 플랜", "include_history": True, "limit": 3})
    assert [(x["recorded_at"], x["id"]) for x in three["results"]] == got[-3:], f"limit=3이면 최근 세 개(t2의 세 claim)를 오름차순으로: {three}"

    default = s2.call("recall", {"query": "Acme 팀 플랜", "limit": 20})
    assert a["id"] not in {x["id"] for x in default["results"]}, "기본 recall에는 대체된 claim이 없어야 합니다"
