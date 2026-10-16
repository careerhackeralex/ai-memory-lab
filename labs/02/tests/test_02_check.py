"""check_02_schema · check_02_isolation · check_02_score (results_02.csv가 있어야 한다)."""
import pytest

from check_02 import (BANK, check_02_isolation_bank, check_02_isolation_flags, check_02_schema, check_02_score,
                      is_correct, load_questions, load_results, normalize)
from conftest import read_env


@pytest.fixture(scope="module")
def results():
    try:
        return load_results()
    except FileNotFoundError as e:
        pytest.fail(str(e))


def test_02_normalize():
    """정규화 규칙과 판정 (INTERFACE.md '채점')."""
    py = {"has_answer": True, "accept": ["python", "파이썬"]}
    assert is_correct("Python입니다.", py) and is_correct("주로 파이썬(pandas)", py)
    assert not is_correct("R", py)
    may = {"has_answer": True, "accept": ["5월20일"]}
    assert is_correct("2026년 5월 20일.", may)
    none = {"has_answer": False, "accept": []}
    assert is_correct("모름", none) and is_correct(" 모름. ", none)
    assert not is_correct("모르겠습니다", none) and not is_correct("메모에 없음", none)
    assert normalize("A, B c.") == "abc"


def test_check_02_schema(results):
    header, rows = results
    errors, warnings = check_02_schema(header, rows, load_questions())
    for w in warnings[:3]:
        print(f"\n  경고: {w}")
    assert not errors, "\n".join(errors[:10])


def test_check_02_isolation(results):
    _, rows = results
    errors = check_02_isolation_flags(rows)
    base = f"http://127.0.0.1:{int(read_env().get('HINDSIGHT_API_PORT', '8888'))}"
    try:
        errors += check_02_isolation_bank(load_questions(), base)
    except Exception as e:
        pytest.fail(f"뱅크 {BANK}를 확인하지 못했습니다(make start EP=02 먼저): {type(e).__name__}")
    assert not errors, "\n".join(errors[:10])


def test_check_02_score(results):
    """모든 행이 LLM 없이 판정된다(정답 수는 측정값이라 기준을 두지 않는다)."""
    _, rows = results
    qs = load_questions()
    score = check_02_score(rows, qs)
    judged = sum(s["answerable"] + s["unanswerable"] + len(s["wrong"]) for s in score.values())
    assert judged == len(rows)
