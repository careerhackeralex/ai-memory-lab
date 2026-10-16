"""제공 데이터가 INTERFACE.md 모양인지 (compare.py 실행 전에도 돈다)."""
import json

from check_02 import ROOT, load_questions


def test_02_data():
    memos = [json.loads(x) for x in (ROOT / "data" / "memos_02.jsonl").read_text().splitlines() if x.strip()]
    qs = load_questions()
    ids = {m["id"] for m in memos}
    assert len(memos) == 50 and len(ids) == 50, "메모는 50개, id는 서로 달라야 합니다"
    assert all(m["text"].strip() and len(m["date"]) == 10 for m in memos)
    assert len(qs) == 10, "질문은 10개"
    assert sum(q["has_answer"] for q in qs) == 7, "답 있는 질문 7개, 없는 질문 3개"
    for q in qs:
        assert set(q["gold_memo_ids"]) <= ids, f"{q['id']} gold_memo_ids에 없는 메모"
        if q["has_answer"]:
            assert q["accept"] and q["gold_memo_ids"], f"{q['id']} accept·gold_memo_ids가 비어 있음"
        else:
            assert not q["accept"] and not q["gold_memo_ids"], f"{q['id']} 답 없는 질문인데 라벨이 있음"
