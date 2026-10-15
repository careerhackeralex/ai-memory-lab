"""test_01 공용 도우미. 테스트는 결정적이다(LLM 판정 없음)."""
import json
import pathlib

import httpx
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
ENV_PATH = ROOT / "hindsight" / ".env"
LOG_PATH = ROOT / "data" / "logs" / "hindsight.log"


def read_env() -> dict:
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


@pytest.fixture(scope="session")
def env():
    return read_env()


@pytest.fixture(scope="session")
def port(env):
    return int(env.get("HINDSIGHT_API_PORT", "8888"))


@pytest.fixture(scope="session")
def base(port):
    return f"http://127.0.0.1:{port}"


def mcp_call(url: str, method: str, params: dict | None = None) -> dict:
    """MCP streamable HTTP: initialize → method. SSE 또는 JSON 응답 모두 처리."""
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}

    def parse(r):
        if "text/event-stream" in r.headers.get("content-type", ""):
            for line in r.text.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[5:])
        return r.json()

    with httpx.Client(timeout=30) as c:
        r = c.post(url, headers=h, json={"jsonrpc": "2.0", "id": 1, "method": "initialize",
                                          "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                                                     "clientInfo": {"name": "test_01", "version": "1"}}})
        r.raise_for_status()
        if sid := r.headers.get("mcp-session-id"):
            h["mcp-session-id"] = sid
        c.post(url, headers=h, json={"jsonrpc": "2.0", "method": "notifications/initialized"})
        r = c.post(url, headers=h, json={"jsonrpc": "2.0", "id": 2, "method": method, "params": params or {}})
        r.raise_for_status()
        return parse(r)
