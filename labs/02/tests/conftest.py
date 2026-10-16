"""test_02 공용. 테스트는 결정적이다(LLM 판정 없음)."""
import importlib.util
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))  # labs/02 (check_02)

# hindsight/.env 읽기는 실습 01의 도우미를 그대로 쓴다 (이름이 같은 conftest라 경로로 불러온다)
_spec = importlib.util.spec_from_file_location("lab01_conftest", HERE.parents[1] / "01" / "tests" / "conftest.py")
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
read_env = _mod.read_env
