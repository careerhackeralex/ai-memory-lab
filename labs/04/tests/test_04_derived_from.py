"""test_04_derived_from: record_event로 만든 이벤트 id(evt_…)를 derived_from으로 준 claim은
recall 결과 항목의 derived_from에 그 id를 담는다. 이 테스트는 이벤트 id만 본다(claim id 근거는 EP8·EP10)."""
import re

from conftest import find

Z = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def test_04_derived_from(server):
    s = server()
    e = s.call("record_event", {"content": "우리 팀은 협업 도구로 Acme를 쓰고, 팀 플랜은 월 9,900원이야.",
                                "source": "conv_04.jsonl#t01"})
    assert str(e.get("id", "")).startswith("evt_"), f"이벤트 id는 evt_로 시작: {e}"
    assert Z.match(str(e.get("recorded_at", ""))), f"이벤트 recorded_at은 UTC, 끝에 Z: {e}"
    m = s.call("remember", {"content": "벨로랩은 협업 도구로 Acme 팀 플랜을 쓴다", "type": "semantic",
                            "derived_from": [e["id"]]})
    assert m.get("derived_from") == [e["id"]], f"remember 반환 객체의 derived_from: {m}"
    hit = find(s.call("recall", {"query": "Acme"})["results"], m["id"])
    assert hit, "recall 결과에 방금 저장한 claim이 없습니다"
    assert hit.get("derived_from") == [e["id"]], f"recall 항목의 derived_from: {hit}"
    assert hit.get("status") == "active", f"새 claim의 status는 active: {hit}"
