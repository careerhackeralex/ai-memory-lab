"""test_04_quote_must_exist: 원문에 없는 quote를 준 remember·supersede는 거절되고 claims 수가 늘지 않는다.

대조로, 원문에 있는 quote는 저장되고 recall로 다시 찾힌다. supersede가 거절되면 옛 claim은 active 그대로다. 비교는 INTERFACE.md의 정규화(따옴표 통일, 연속 공백 하나로) 뒤 부분 문자열 일치다.
"""
from conftest import db_rows, find, is_tool_error

SOURCE = "예산 문서에는 아직 “월 9,900원”으로  적혀 있으니까 다음 주까지 고쳐야 해."


def count(db) -> int:
    return db_rows(db, "SELECT count(*) FROM claims")[0][0]


def test_04_quote_must_exist(server, db):
    s = server()
    e = s.call("record_event", {"content": SOURCE, "source": "conv_04.jsonl#t09"})
    ok = s.call("remember", {"content": "예산 문서의 Acme 요금은 아직 9,900원으로 적혀 있다", "type": "episodic",
                             "derived_from": [e["id"]], "quote": "아직 \"월 9,900원\"으로 적혀 있으니까"})
    assert ok["id"].startswith("clm_"), ok
    n = count(db)
    assert n == 1, f"원문에 있는 quote를 준 claim은 저장되어야 합니다(claims 수 {n})"
    assert find(s.call("recall", {"query": "예산 문서"})["results"], ok["id"]), "저장한 claim이 recall에 나와야 합니다"

    bad = s.call_raw("remember", {"content": "예산 문서는 이미 12,900원으로 고쳤다", "type": "episodic",
                                  "derived_from": [e["id"]], "quote": "이미 12,900원으로 고쳤어"})
    assert is_tool_error(bad), f"원문에 없는 quote는 거절해야 합니다: {bad}"
    assert count(db) == n, "거절한 claim이 저장되었습니다(claims 수가 늘었음)"

    bad2 = s.call_raw("supersede", {"old_id": ok["id"], "content": "예산 문서는 이미 12,900원으로 고쳤다",
                                    "derived_from": [e["id"]], "quote": "이미 12,900원으로 고쳤어"})
    assert is_tool_error(bad2), f"supersede도 원문에 없는 quote는 거절해야 합니다: {bad2}"
    assert count(db) == n, "거절한 supersede가 새 claim을 저장했습니다"
    assert db_rows(db, "SELECT status FROM claims WHERE id = ?", (ok["id"],)) == [("active",)], "거절한 supersede가 옛 claim을 바꿨습니다"

    good = s.call("supersede", {"old_id": ok["id"], "content": "예산 문서의 Acme 요금은 아직 9,900원이고 다음 주까지 고쳐야 한다",
                                "derived_from": [e["id"]], "quote": "다음 주까지 고쳐야 해"})
    assert good.get("supersedes") == ok["id"] and count(db) == n + 1, f"원문에 있는 quote를 준 supersede는 저장: {good}"
