"""test_04_backcompat: 실습 03의 test_03 전체가 그대로 통과한다(remember(content, type)만으로 동작, recall의 {"results": [...]} 유지).
이 편의 테스트 데이터는 episodic·semantic만 쓰고 절차 기억의 회상에 기대지 않는다."""
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[3]


def test_04_backcompat():
    env = {k: v for k, v in os.environ.items() if k not in ("UV_PROJECT_ENVIRONMENT", "VIRTUAL_ENV", "MINI_MEMORY_NOW", "MINI_MEMORY_DB")}
    p = subprocess.run([sys.executable, "-m", "pytest", "labs/03/tests", "-q", "--no-header", "-p", "no:warnings", "-p", "no:cacheprovider"],
                       cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=600)
    tail = "\n".join(p.stdout.strip().splitlines()[-15:])
    assert p.returncode == 0, f"test_03이 실패합니다(앞 편 계약이 깨짐):\n{tail}"
