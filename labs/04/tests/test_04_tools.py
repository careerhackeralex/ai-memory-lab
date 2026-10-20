"""test_04_tools: tools/list에 이 편까지 나온 도구(remember·recall·record_event·supersede)가 모두 있고,
시리즈 고정 목록 밖의 이름은 없다. 개수는 세지 않는다(뒤 편이 도구를 더한다)."""
from conftest import ALLOWED_TOOLS

NEEDED = {"remember", "recall", "record_event", "supersede"}


def test_04_tools(server):
    names = set(server().tools())
    missing = NEEDED - names
    assert not missing, f"이 편까지의 도구가 없습니다: {sorted(missing)} (있는 도구: {sorted(names)})"
    extra = names - ALLOWED_TOOLS
    assert not extra, f"고정 목록 밖의 도구: {sorted(extra)} (허용: {sorted(ALLOWED_TOOLS)})"
