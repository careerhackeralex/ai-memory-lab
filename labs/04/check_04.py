"""check_04 (선택, 측정): LLM이 대화에서 뽑은 claim의 인용(quote)이 원문에 실제로 있는지 잰다.

1. `claude -p`(labs/common.md의 격리 명령)가 data/conv_04.jsonl에서 claim과 인용을 JSON으로 뽑는다.
2. 내 미니 메모리(mini_memory/)를 MCP 서버로 띄워 대화 10턴을 record_event로 넣고, 각 claim을
   remember(content, type, derived_from=[그 턴의 evt_ id], quote)로 넣는다. 인용 검사가 통과·거절을 정한다.
3. 통과·거절 표를 출력하고 data/check_04/result.md에 쓴다(머리에 실제로 쓴 명령). 통과·실패 판정은 없다.

측정용 DB는 data/check_04/mini_memory.db를 매번 새로 만든다(내 실습 DB data/mini_memory.db는 건드리지 않는다).
HaluMem이 말한 '추출 환각'을 작게 보는 측정이다: 거절된 인용 = 원문에 없는 글을 원문이라고 내민 경우.

    .venv/bin/python labs/04/check_04.py             # claude -p 1회 (구독 한도 또는 API 요금)
    .venv/bin/python labs/04/check_04.py --dry-run   # 호출 없이 프롬프트와 명령만 보기
"""
import argparse
import json
import os
import pathlib
import queue
import shutil
import subprocess
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
CONV = ROOT / "data" / "conv_04.jsonl"
OUT = ROOT / "data" / "check_04"
PROJECT = ROOT / "mini_memory"

FLAGS = ["--safe-mode", "--tools", "", "--no-session-persistence", "--output-format", "json"]
COMMAND = ('CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude -p "$(cat data/check_04/prompt.txt)" '
           '--safe-mode --tools "" --no-session-persistence --output-format json < /dev/null')

PROMPT = """아래는 가상 인물 하린(사용자)과 AI 에이전트(assistant)의 대화다. JSON 한 줄이 한 턴이다.
나중에 다시 쓸 수 있게 장기 기억으로 남길 사실(claim)을 뽑아라.

규칙
- 답은 JSON 배열 하나만 쓴다. 설명이나 코드 블록 표시는 쓰지 않는다.
- 항목 형식: {{"turn": "근거 턴 id", "type": "episodic 또는 semantic", "content": "claim 한 문장", "quote": "근거 인용"}}
- type: 언제 무슨 일이 있었는지는 episodic, 사실·선호·설정은 semantic.
- quote: 근거 턴의 text에서 글자 그대로 복사한 구절(10~40자). 고쳐 쓰거나 줄이지 않는다.
- claim은 최대 12개.

대화
{conversation}
"""


# ---------------------------------------------------------------- MCP stdio 클라이언트 (표준 라이브러리)

class Mcp:
    def __init__(self, env: dict):
        uv = shutil.which("uv") or sys.exit("uv가 없습니다.")
        self.proc = subprocess.Popen([uv, "run", "--quiet", "--project", str(PROJECT), "mini-memory", "serve"],
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     env=env, cwd=str(ROOT), text=True, encoding="utf-8", bufsize=1)
        self.q: queue.Queue = queue.Queue()
        threading.Thread(target=lambda: [self.q.put(x) for x in self.proc.stdout] + [self.q.put(None)], daemon=True).start()
        self.n = 0
        self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                    "clientInfo": {"name": "check_04", "version": "1"}})
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.proc.stdin.flush()

    def request(self, method: str, params: dict) -> dict:
        self.n += 1
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params}, ensure_ascii=False) + "\n")
        self.proc.stdin.flush()
        while True:
            line = self.q.get(timeout=60)
            if line is None:
                sys.exit("mini-memory 서버가 끝났습니다. make check EP=04가 통과하는지 먼저 확인하세요.")
            msg = json.loads(line)
            if msg.get("id") == self.n:
                return msg

    def call(self, name: str, args: dict) -> tuple[bool, dict | str]:
        """(성공 여부, 반환 객체 또는 오류 글)."""
        r = self.request("tools/call", {"name": name, "arguments": args})
        if "error" in r:
            return False, str(r["error"].get("message"))
        res = r["result"]
        text = " ".join(c.get("text", "") for c in res.get("content") or [] if c.get("type") == "text")
        if res.get("isError"):
            return False, text
        sc = res.get("structuredContent")
        if isinstance(sc, dict):
            return True, sc["result"] if set(sc) == {"result"} and isinstance(sc["result"], dict) else sc
        return True, json.loads(text)

    def close(self):
        self.proc.stdin.close()
        self.proc.wait(timeout=10)


# ---------------------------------------------------------------- 추출

def parse_claims(text: str) -> list[dict]:
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1].rsplit("```", 1)[0]
    try:
        data = json.loads(t)
    except json.JSONDecodeError:
        data = json.loads(t[t.index("["): t.rindex("]") + 1])
    return [x for x in data if isinstance(x, dict)]


def extract(prompt: str) -> tuple[dict, float]:
    env = {**os.environ, "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1"}
    t0 = time.time()
    p = subprocess.run(["claude", "-p", prompt, *FLAGS], env=env, stdin=subprocess.DEVNULL,
                       capture_output=True, text=True, timeout=600)
    if p.returncode != 0 and not p.stdout.strip():
        sys.exit(f"claude -p 실패 (종료 코드 {p.returncode}): {p.stderr[-500:]}")
    return json.loads(p.stdout), time.time() - t0


def short(s: str, n: int) -> str:
    s = " ".join(str(s).split())
    return s if len(s) <= n else s[: n - 1] + "…"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true", help="claude -p를 부르지 않고 프롬프트와 명령만 출력")
    args = ap.parse_args()

    turns = [json.loads(x) for x in CONV.read_text(encoding="utf-8").splitlines() if x.strip()]
    conversation = "\n".join(json.dumps({"id": t["id"], "role": t["role"], "text": t["text"]}, ensure_ascii=False) for t in turns)
    prompt = PROMPT.format(conversation=conversation)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "prompt.txt").write_text(prompt, encoding="utf-8")
    print(f"명령: {COMMAND}")
    if args.dry_run:
        print("\n" + prompt)
        return
    if not (PROJECT / "pyproject.toml").exists():
        sys.exit("mini_memory/가 없습니다. 먼저 make start EP=04 → PROMPT.md → make check EP=04")

    print(f"• claude -p 추출 중 (data/conv_04.jsonl {len(turns)}턴)…", flush=True)
    answer, sec = extract(prompt)
    (OUT / "answer.json").write_text(json.dumps(answer, ensure_ascii=False, indent=2), encoding="utf-8")
    if answer.get("is_error"):
        sys.exit(f"claude -p 오류: {answer.get('result')}")
    claims = parse_claims(answer.get("result", ""))

    db = OUT / "mini_memory.db"
    for suffix in ("", "-wal", "-shm", "-journal"):
        pathlib.Path(str(db) + suffix).unlink(missing_ok=True)
    env = {k: v for k, v in os.environ.items() if k not in ("UV_PROJECT_ENVIRONMENT", "VIRTUAL_ENV", "MINI_MEMORY_NOW")}
    env["MINI_MEMORY_DB"] = str(db)
    mcp = Mcp(env)
    evt = {}
    for t in turns:
        ok, e = mcp.call("record_event", {"content": t["text"], "source": f"conv_04.jsonl#{t['id']}"})
        if not ok:
            sys.exit(f"record_event 실패: {e}")
        evt[t["id"]] = e["id"]
    text_of = {t["id"]: t["text"] for t in turns}

    rows = []
    for c in claims:
        turn, quote = str(c.get("turn", "")), str(c.get("quote", ""))
        exact = "예" if turn in text_of and quote and quote in text_of[turn] else "아니오"
        if turn not in evt:
            rows.append((turn, c.get("type"), "거절", f"근거 턴 {turn!r}가 대화에 없음", exact, c.get("content", ""), quote))
            continue
        ok, r = mcp.call("remember", {"content": str(c.get("content", "")), "type": str(c.get("type", "")),
                                      "derived_from": [evt[turn]], "quote": quote})
        rows.append((turn, c.get("type"), "통과" if ok else "거절", "" if ok else short(r, 60), exact, c.get("content", ""), quote))
    mcp.close()

    passed = sum(1 for r in rows if r[2] == "통과")
    rejected = len(rows) - passed
    u = answer.get("usage", {})
    tin = u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0)
    lines = [f"명령: {COMMAND}", "",
             f"check_04 — 추출 claim {len(rows)}개, 인용 검사 통과 {passed} · 거절 {rejected} "
             f"(claude -p {sec:.1f}초, 입력 {tin:,} · 출력 {u.get('output_tokens', 0):,} 토큰, total_cost_usd {answer.get('total_cost_usd', 0):.4f})",
             "", "| # | 턴 | type | 인용 검사 | 원문 그대로 | claim | quote | 거절 이유 |", "|---|---|---|---|---|---|---|---|"]
    for i, (turn, typ, verdict, why, exact, content, quote) in enumerate(rows, 1):
        lines.append(f"| {i} | {turn} | {typ} | {verdict} | {exact} | {short(content, 40)} | {short(quote, 30)} | {why} |")
    lines += ["", "원문 그대로 = 정규화 없이도 그 턴의 text에 quote가 그대로 있는지(참고). 인용 검사는 INTERFACE.md의 정규화 뒤 부분 문자열 일치.",
              "주: 추출은 LLM이 하므로 실행마다 달라진다. 측정이고 통과·실패 판정은 없다."]
    report = "\n".join(lines) + "\n"
    (OUT / "result.md").write_text(report, encoding="utf-8")
    print("\n".join(lines[2:]))  # 명령 줄은 맨 위에 이미 출력했다
    print(f"결과 파일: data/check_04/result.md (원 응답 answer.json, 프롬프트 prompt.txt, 측정 DB mini_memory.db)")


if __name__ == "__main__":
    main()
