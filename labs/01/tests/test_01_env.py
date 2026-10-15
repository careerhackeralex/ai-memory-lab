import subprocess

from conftest import ENV_PATH, ROOT


def test_01_env(env):
    assert ENV_PATH.exists(), "hindsight/.env가 없습니다 (cp hindsight/.env.example hindsight/.env)"
    prov = env.get("HINDSIGHT_API_LLM_PROVIDER", "")
    assert prov, "HINDSIGHT_API_LLM_PROVIDER가 비어 있습니다"
    assert prov != "claude-code", "claude-code 공급자는 쓰지 않습니다"
    r = subprocess.run(["git", "check-ignore", "-q", "hindsight/.env"], cwd=ROOT)
    assert r.returncode == 0, "hindsight/.env가 .gitignore에 걸리지 않습니다"
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "hindsight/.env"], cwd=ROOT, capture_output=True)
    assert tracked.returncode != 0, "hindsight/.env가 git에 추적되고 있습니다 (git rm --cached hindsight/.env)"
