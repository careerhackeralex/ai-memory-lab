"""test_04 공용 도우미(실습 03의 conftest와 같은 방식). 미니 메모리를 실제 명령(`uv run mini-memory serve`, `uv run mm`)으로 띄워 검사한다.

- 테스트마다 임시 폴더의 새 DB를 쓴다(MINI_MEMORY_DB). 내 실습 DB(data/mini_memory.db)는 건드리지 않는다.
- MCP 클라이언트는 표준 라이브러리로 직접 쓴다(stdio = 한 줄에 JSON-RPC 메시지 하나).
  stdout에 JSON이 아닌 줄이 나오면 바로 실패한다(로그는 stderr로).
- 이 파일과 test_04_*.py는 고치지 않는다. 실패하면 mini_memory/ 구현을 고친다.
"""
import json
import os
import pathlib
import queue
import shutil
import subprocess
import threading

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
PROJECT = ROOT / "mini_memory"
ALLOWED_TOOLS = {"remember", "recall", "record_event", "supersede", "link", "forget", "promote", "approve"}
TIMEOUT = 60  # 첫 실행은 uv가 패키지를 설치하느라 몇 초 걸린다


def uv() -> str:
    path = shutil.which("uv")
    if not path:
        pytest.fail("uv가 없습니다. 실습 00의 준비물(uv)을 설치하세요.")
    return path


def base_env(db: pathlib.Path, now: str | None = None) -> dict:
    env = {k: v for k, v in os.environ.items() if k not in ("UV_PROJECT_ENVIRONMENT", "VIRTUAL_ENV", "MINI_MEMORY_NOW")}
    env["MINI_MEMORY_DB"] = str(db)
    if now:
        env["MINI_MEMORY_NOW"] = now
    return env


@pytest.fixture(autouse=True)
def _project_exists():
    if not (PROJECT / "pyproject.toml").exists():
        pytest.fail("mini_memory/pyproject.toml이 없습니다. 먼저 make start EP=04")


@pytest.fixture
def db(tmp_path) -> pathlib.Path:
    return tmp_path / "mini_memory.db"


class McpStdio:
    """`uv run --project mini_memory mini-memory serve`를 띄우고 JSON-RPC로 말을 건다."""

    def __init__(self, env: dict):
        self.proc = subprocess.Popen(
            [uv(), "run", "--quiet", "--project", str(PROJECT), "mini-memory", "serve"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=env, cwd=str(ROOT), text=True, encoding="utf-8", bufsize=1,
        )
        self.lines: queue.Queue = queue.Queue()
        self.stderr: list[str] = []
        threading.Thread(target=self._pump, args=(self.proc.stdout, self.lines), daemon=True).start()
        threading.Thread(target=self._drain, daemon=True).start()
        self.next_id = 0
        init = self.request("initialize", {"protocolVersion": "2025-06-18", "capabilities": {},
                                           "clientInfo": {"name": "test_04", "version": "1"}})
        assert "result" in init, f"initialize 실패: {init}"
        self.notify("notifications/initialized")

    @staticmethod
    def _pump(stream, q):
        for line in stream:
            q.put(line)
        q.put(None)

    def _drain(self):
        for line in self.proc.stderr:
            self.stderr.append(line)

    def _fail(self, msg: str):
        tail = "".join(self.stderr[-15:])
        pytest.fail(f"{msg}\n--- 서버 stderr 마지막 줄 ---\n{tail}")

    def send(self, msg: dict):
        try:
            self.proc.stdin.write(json.dumps(msg, ensure_ascii=False) + "\n")
            self.proc.stdin.flush()
        except BrokenPipeError:
            self._fail("서버가 이미 끝났습니다 (mini-memory serve가 바로 종료됨)")

    def notify(self, method: str, params: dict | None = None):
        self.send({"jsonrpc": "2.0", "method": method, **({"params": params} if params else {})})

    def request(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        rid = self.next_id
        self.send({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}})
        while True:
            try:
                line = self.lines.get(timeout=TIMEOUT)
            except queue.Empty:
                self._fail(f"{method}: {TIMEOUT}초 안에 응답이 없습니다")
            if line is None:
                self._fail(f"{method}: 응답 전에 서버가 끝났습니다")
            if not line.strip():
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                self._fail(f"stdout에 MCP 메시지가 아닌 줄이 나왔습니다(로그·print는 stderr로): {line[:200]!r}")
            if msg.get("id") == rid and ("result" in msg or "error" in msg):
                return msg

    def tools(self) -> list[str]:
        r = self.request("tools/list")
        assert "result" in r, f"tools/list 실패: {r}"
        return [t["name"] for t in r["result"]["tools"]]

    def call_raw(self, name: str, args: dict) -> dict:
        return self.request("tools/call", {"name": name, "arguments": args})

    def call(self, name: str, args: dict) -> dict:
        r = self.call_raw(name, args)
        assert "result" in r, f"{name} 호출이 JSON-RPC 오류를 냈습니다: {r.get('error')}"
        res = r["result"]
        assert not res.get("isError"), f"{name} 도구 오류: {res.get('content')}"
        return tool_payload(res)

    def close(self):
        if self.proc.poll() is None:
            try:
                self.proc.stdin.close()
            except Exception:
                pass
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.terminate()
                self.proc.wait(timeout=10)


def tool_payload(res: dict) -> dict:
    """도구 결과에서 반환 객체를 꺼낸다: structuredContent가 있으면 그것, 없으면 첫 text를 JSON으로."""
    sc = res.get("structuredContent")
    if isinstance(sc, dict):
        if set(sc) == {"result"} and isinstance(sc["result"], dict):
            return sc["result"]
        return sc
    for c in res.get("content") or []:
        if c.get("type") == "text":
            try:
                return json.loads(c["text"])
            except json.JSONDecodeError:
                pytest.fail(f"도구 결과가 JSON 객체가 아닙니다: {c['text'][:200]!r}")
    pytest.fail(f"도구 결과에 반환 객체가 없습니다: {res}")


def is_tool_error(r: dict) -> bool:
    return "error" in r or bool(r.get("result", {}).get("isError"))


@pytest.fixture
def server(db):
    started = []

    def start(now: str | None = None) -> McpStdio:
        s = McpStdio(base_env(db, now))
        started.append(s)
        return s

    yield start
    for s in started:
        s.close()


def run_mm(db: pathlib.Path, *args: str) -> dict:
    """`uv run --project mini_memory mm ...`의 stdout 전체를 JSON으로 읽는다."""
    p = subprocess.run([uv(), "run", "--quiet", "--project", str(PROJECT), "mm", *args],
                       env=base_env(db), cwd=str(ROOT), capture_output=True, text=True, timeout=120)
    assert p.returncode == 0, f"mm {' '.join(args)} 종료 코드 {p.returncode}\n{p.stderr[-1500:]}"
    try:
        return json.loads(p.stdout)
    except json.JSONDecodeError:
        pytest.fail(f"mm {args[0]}의 stdout 전체가 JSON 하나여야 합니다(로그는 stderr로): {p.stdout[:300]!r}")


# ---- 실습 04 공용 값과 도우미
T1 = "2026-03-02T09:00:00+09:00"   # → 2026-03-02T00:00:00Z
T2 = "2026-04-01T10:30:00+09:00"   # → 2026-04-01T01:30:00Z
T1Z, T2Z = "2026-03-02T00:00:00Z", "2026-04-01T01:30:00Z"
OLD_PRICE = "벨로랩의 Acme 팀 플랜은 월 9,900원이다"
NEW_PRICE = "벨로랩의 Acme 팀 플랜은 월 12,900원이다"


def find(results: list, cid: str) -> dict | None:
    return next((r for r in results if r.get("id") == cid), None)


def db_rows(db: pathlib.Path, sql: str, params: tuple = ()) -> list[tuple]:
    """SQLite를 직접 읽는다(쓰지 않음)."""
    import sqlite3
    con = sqlite3.connect(db)
    try:
        return con.execute(sql, params).fetchall()
    finally:
        con.close()
