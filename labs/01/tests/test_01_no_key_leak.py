import subprocess

import httpx

from conftest import LOG_PATH, ROOT


def secrets(env: dict) -> list[str]:
    keys = ("API_KEY", "TOKEN", "SECRET", "PASSWORD")
    return [v for k, v in env.items() if any(x in k for x in keys) and len(v) >= 8]


def test_01_no_key_leak(env, base):
    vals = secrets(env)
    if not vals:
        print("\n  .env에 키가 없습니다(ollama) — 검사할 키 없음")
        return
    places = {}
    if LOG_PATH.exists():
        places["data/logs/hindsight.log"] = LOG_PATH.read_text(errors="replace")
    for f in (ROOT / "data").rglob("*"):
        if f.is_file() and f != LOG_PATH:
            places[str(f.relative_to(ROOT))] = f.read_text(errors="replace")
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True).stdout.split()
    for f in files:
        p = ROOT / f
        if p.is_file():
            places[f] = p.read_text(errors="replace")
    for bank in ("lab", "lab-check"):  # LLM 요청 추적(내장 DB)
        r = httpx.get(f"{base}/v1/default/banks/{bank}/llm-requests", params={"limit": 500}, timeout=30)
        if r.status_code == 200:
            places[f"llm-requests:{bank}"] = r.text
    leaked = [name for name, text in places.items() for v in vals if v in text]
    assert not leaked, f"키 문자열이 발견된 곳: {sorted(set(leaked))}"
