import json

from conftest import ROOT

RECALL_LINE = "개인 정보 질문은 먼저 hindsight recall로 확인한다"


def test_01_automem_off():
    p = ROOT / ".claude" / "settings.json"
    assert p.exists(), ".claude/settings.json이 없습니다"
    s = json.loads(p.read_text())
    assert s.get("autoMemoryEnabled") is False, "autoMemoryEnabled=false가 아닙니다"
    assert RECALL_LINE in (ROOT / "CLAUDE.md").read_text(), "CLAUDE.md의 recall 안내 줄이 없습니다"
