"""show_hindsight: 가상 대화(data/conv_03.jsonl)를 Hindsight 뱅크 lab03에 retain하고,
추출된 기억이 어느 네트워크(world·experience·opinion·observation)에 들어갔는지 표로 본다. 실습 03의 6단계(관찰, 채점 없음).

    .venv/bin/python labs/03/show_hindsight.py            # 처음이면 retain, 이미 있으면 표만
    .venv/bin/python labs/03/show_hindsight.py --fresh    # 뱅크 lab03을 지우고 다시 retain
    .venv/bin/python labs/03/show_hindsight.py --wait 0   # 관찰(observation) 통합을 기다리지 않음

- 대화 10턴을 문서 하나(document_id conv_03)로 넣는다. retain은 추출이 끝날 때까지 기다린다(async=false).
- 네트워크 이름은 hindsight-api 1.0.0의 `fact_type` 칸이다(memories/list). 1.0.0의 값은 world·experience·observation
  셋이다. opinion은 2026-04 마이그레이션(remove_opinion_fact_type)에서 없어져 이 버전에서는 늘 0개다.
- observation은 retain 뒤 비동기 통합(consolidation)이 만든다. 기본 300초까지 기다리고, 그 안에 안 끝나면
  있는 만큼 보여 준다(나중에 다시 실행하면 표만 다시 그린다).
- 아래에 내 미니 메모리(MINI_MEMORY_DB, 기본 data/mini_memory.db)의 type 표를 나란히 출력한다(읽기만).
- 추출은 LLM이 하므로 실행마다 문장과 네트워크가 조금씩 다를 수 있다.
"""
import argparse
import json
import os
import pathlib
import sqlite3
import sys
import time
import unicodedata
from datetime import datetime, timezone

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "labs" / "01" / "tests"))
from conftest import read_env  # noqa: E402

env = read_env()
PORT = int(env.get("HINDSIGHT_API_PORT", "8888"))
BANK = "lab03"
DOC = "conv_03"
B = f"http://127.0.0.1:{PORT}/v1/default/banks/{BANK}"
NETWORKS = ("world", "experience", "opinion", "observation")
NOTE = {"world": "세상·사용자에 대한 사실", "experience": "에이전트 자신이 한 일",
        "opinion": "판단·믿음 (1.0.0에서 제거됨)", "observation": "여러 사실을 통합한 요약"}


def width(s: str) -> int:
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def clip(s: str, w: int) -> str:
    s = " ".join(s.split())
    if width(s) <= w:
        return s + " " * (w - width(s))
    out = ""
    for ch in s:
        if width(out + ch) > w - 1:
            break
        out += ch
    return out + "…" + " " * (w - 1 - width(out))


def transcript(turns: list[dict]) -> str:
    who = {"user": "사용자(하린)", "assistant": "AI 에이전트(assistant)"}
    return "\n".join(f"[{t['at'][11:16]}] {who.get(t['role'], t['role'])}: {t['text']}" for t in turns)


def to_utc(s: str) -> str:
    return datetime.fromisoformat(s).astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def has_doc(c: httpx.Client) -> bool:
    r = c.get(B + "/documents", params={"limit": 100})
    return r.status_code == 200 and any(d["id"] == DOC for d in r.json().get("items", []))


def all_memories(c: httpx.Client) -> list[dict]:
    items, offset = [], 0
    while True:
        r = c.get(B + "/memories/list", params={"limit": 100, "offset": offset})
        r.raise_for_status()
        part = r.json().get("items", [])
        items += part
        if len(part) < 100:
            return items
        offset += 100


def pending_consolidation(c: httpx.Client) -> int:
    n = 0
    for st in ("pending", "processing"):
        r = c.get(B + "/operations", params={"type": "consolidation", "status": st, "limit": 100})
        if r.status_code == 200:
            n += len(r.json().get("operations", []))
    return n


def llm_usage(c: httpx.Client, since: str | None) -> dict:
    r = c.get(B + "/llm-requests", params={"limit": 500, **({"start_date": since} if since else {})})
    out: dict = {}
    if r.status_code != 200:
        return out
    for x in r.json().get("items", []):
        o = out.setdefault(x.get("operation") or "?", {"calls": 0, "in": 0, "out": 0, "errors": 0})
        o["calls"] += 1
        o["in"] += x.get("input_tokens") or 0
        o["out"] += x.get("output_tokens") or 0
        o["errors"] += x.get("status") == "error"
    return out


def mini_memory_rows() -> tuple[pathlib.Path, list]:
    db = pathlib.Path(os.environ.get("MINI_MEMORY_DB") or ROOT / "data" / "mini_memory.db")
    if not db.exists():
        return db, []
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        return db, con.execute("SELECT type, content, recorded_at FROM claims ORDER BY recorded_at, id").fetchall()
    except sqlite3.Error:
        return db, []
    finally:
        con.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--fresh", action="store_true", help="뱅크 lab03을 지우고 다시 retain")
    ap.add_argument("--wait", type=int, default=300, help="observation 통합을 기다릴 최대 초 (0이면 안 기다림)")
    a = ap.parse_args()

    turns = [json.loads(x) for x in (ROOT / "data" / "conv_03.jsonl").read_text().splitlines() if x.strip()]
    c = httpx.Client(timeout=1800)
    try:
        c.get(f"http://127.0.0.1:{PORT}/health").raise_for_status()
    except httpx.HTTPError:
        print(f"✗ Hindsight(127.0.0.1:{PORT})가 꺼져 있습니다. make start EP=03 으로 켜세요.")
        return 1
    if a.fresh:
        c.delete(B)
    c.put(B, json={}).raise_for_status()
    c.patch(B + "/config", json={"updates": {"enable_observations": True}}).raise_for_status()

    llm = env.get("HINDSIGHT_API_LLM_PROVIDER", "?") + "/" + env.get("HINDSIGHT_API_LLM_MODEL", "?")
    since = None
    if has_doc(c):
        print(f"• 뱅크 {BANK}: 대화 {DOC}가 이미 있음 → retain 건너뜀 (다시 넣으려면 --fresh)")
    else:
        print(f"• retain: data/conv_03.jsonl {len(turns)}턴 → 뱅크 {BANK} (문서 하나, LLM {llm})", flush=True)
        t = time.time()
        since = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        r = c.post(B + "/memories", json={"async": False, "items": [{
            "content": transcript(turns), "timestamp": to_utc(turns[0]["at"]), "document_id": DOC,
            "context": "하린(가상 인물)과 AI 에이전트의 업무 대화"}]})
        if r.status_code != 200:
            print(f"✗ retain 실패 (HTTP {r.status_code}): {r.text[:300]}")
            print("  tail -n 50 data/logs/hindsight.log 로 LLM 오류를 확인하세요.")
            return 1
        u = r.json().get("usage") or {}
        print(f"  추출 완료 {time.time() - t:.1f}초, LLM 토큰 입력 {u.get('input_tokens', 0):,} / 출력 {u.get('output_tokens', 0):,}")

    if a.wait > 0:
        t0, last = time.time(), -1.0
        while (n := pending_consolidation(c)) and time.time() - t0 < a.wait:
            if time.time() - last >= 15:
                print(f"  observation 통합 대기 중 ({n}건, {time.time() - t0:.0f}초)", flush=True)
                last = time.time()
            time.sleep(3)
        n = pending_consolidation(c)
        print(f"• observation 통합: {'끝남' if not n else f'{a.wait}초 안에 안 끝남 ({n}건 남음)'} ({time.time() - t0:.0f}초)")

    mems = all_memories(c)
    by = {k: [m for m in mems if (m.get("fact_type") or m.get("type")) == k] for k in NETWORKS}
    other = [m for m in mems if (m.get("fact_type") or m.get("type")) not in NETWORKS]

    print(f"\nHindsight 뱅크 {BANK} — 네트워크별 기억 (칸 이름 fact_type, hindsight-api 1.0.0)")
    print("─" * 110)
    for k in NETWORKS:
        print(f"{k:<12}{len(by[k]):>3}개   {NOTE[k]}")
        for m in by[k]:
            print(f"    · {clip(m.get('text', ''), 100)}")
    for m in other:
        print(f"{(m.get('fact_type') or '?'):<12}    · {clip(m.get('text', ''), 100)}")
    print("─" * 110)

    db, rows = mini_memory_rows()
    rel = db.relative_to(ROOT) if db.is_relative_to(ROOT) else db
    print(f"\n내 미니 메모리 ({rel}) — type별")
    print("─" * 110)
    if not rows:
        print("  (아직 없음: 5단계에서 mini-memory로 저장하면 여기에 나온다)")
    for typ, content, at in rows:
        print(f"{typ:<12}{at}  {clip(content, 76)}")
    print("─" * 110)

    us = llm_usage(c, since)
    if us:
        print(f"\nHindsight LLM 호출 (뱅크 lab03, {'이번 실행' if since else '지금까지'}, 추적 기록): " + " · ".join(
            f"{op} {v['calls']}회 입력 {v['in']:,} / 출력 {v['out']:,}" + (f" (오류 {v['errors']})" if v["errors"] else "")
            for op, v in sorted(us.items())))
    print("주: 추출·통합은 LLM이 하므로 실행마다 달라질 수 있다. 관찰 단계라 채점하지 않는다.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
