"""check_00: 실습 준비물 확인 (표준 라이브러리만 사용). make check-env로 실행한다."""
import json
import os
import pathlib
import platform
import shutil
import socket
import subprocess
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
rows = []  # (항목, 결과, 비고)

def pad(s, n):
    """한글 폭(2칸)을 고려한 왼쪽 정렬."""
    import unicodedata
    w = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in str(s))
    return str(s) + " " * max(0, n - w)

failed = False


def add(name, ok, note=""):
    global failed
    rows.append((name, "OK" if ok else "실패", note))
    failed |= not ok


def run(*cmd):
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return ""


def read_env():
    p = ROOT / "hindsight" / ".env"
    src = "hindsight/.env"
    if not p.exists():
        p, src = ROOT / "hindsight" / ".env.example", "hindsight/.env.example(.env 없음)"
    env = {}
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env, src


# 운영체제
system = platform.system()
add("운영체제", system in ("Darwin", "Linux"), f"{system} {platform.machine()}" + ("" if system != "Windows" else " → WSL2 안에서 진행"))

# Python 3.12 (uv가 찾을 수 있으면 됨)
uv = shutil.which("uv")
py312 = run("uv", "python", "find", "3.12") if uv else ""
py312 = py312 or shutil.which("python3.12") or ""
add("Python 3.12", bool(py312), py312 or "uv python install 3.12")
add("uv", bool(uv), run("uv", "--version") if uv else "https://docs.astral.sh/uv/")
add("git", bool(shutil.which("git")), run("git", "--version"))
claude = shutil.which("claude")
add("Claude Code", bool(claude), run("claude", "--version") if claude else "https://docs.claude.com/claude-code")

# 포트
env, env_src = read_env()
port = int(env.get("HINDSIGHT_API_PORT", "8888"))
s = socket.socket()
s.settimeout(1)
busy = s.connect_ex(("127.0.0.1", port)) == 0
s.close()
note = "비어 있음"
ok = not busy
if busy:
    try:
        v = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/version", timeout=3))
        note, ok = f"이 실습의 Hindsight {v.get('api_version')}가 이미 실행 중", True
    except Exception:
        note = f"다른 프로그램이 사용 중: lsof -i :{port}"
add(f"포트 {port}", ok, note)

# LLM 공급자 (키 값은 출력하지 않는다)
prov = env.get("HINDSIGHT_API_LLM_PROVIDER", "")
model = env.get("HINDSIGHT_API_LLM_MODEL", "")
if prov == "claude-code":
    add("LLM 공급자", False, "claude-code는 쓰지 않습니다 (ollama 또는 API 키 공급자)")
elif prov == "ollama":
    base = env.get("HINDSIGHT_API_LLM_BASE_URL", "http://127.0.0.1:11434/v1").rstrip("/")
    base = base[:-3] if base.endswith("/v1") else base
    try:
        tags = json.load(urllib.request.urlopen(base + "/api/tags", timeout=5))
        names = [m["name"] for m in tags.get("models", [])]
        have = model in names or f"{model}:latest" in names
        add("LLM 공급자", True, f"ollama 응답 OK ({env_src})")
        rows.append(("Ollama 모델", "OK" if have else "받기 전", f"{model}" + ("" if have else " → make models가 받습니다")))
    except Exception:
        add("LLM 공급자", False, f"ollama가 응답하지 않습니다 ({base}). 'ollama serve' 또는 앱 실행")
elif prov:
    key = env.get("HINDSIGHT_API_LLM_API_KEY", "")
    host = {"anthropic": "api.anthropic.com", "openai": "api.openai.com", "gemini": "generativelanguage.googleapis.com"}.get(prov)
    reach = True
    if host:
        try:
            socket.create_connection((host, 443), timeout=5).close()
        except Exception:
            reach = False
    add("LLM 공급자", bool(key) and reach, f"{prov}: 키 {'있음' if key else '없음'}(값은 표시 안 함), {host or '주소'} {'연결됨' if reach else '연결 실패'}")
else:
    add("LLM 공급자", False, f"{env_src}에 HINDSIGHT_API_LLM_PROVIDER가 없습니다")

if not (ROOT / "hindsight" / ".env").exists():
    rows.append(("hindsight/.env", "아직 없음", "cp hindsight/.env.example hindsight/.env"))

w = 16
print("check_00 — 실습 준비물")
for name, res, note in rows:
    print(f"  {pad(name, w)} {pad(res, 9)} {note}")
print("\n결과:", "준비 완료" if not failed else "실패 항목을 먼저 해결하세요")
sys.exit(1 if failed else 0)
