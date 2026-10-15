"""check_01: 측정(통과·실패가 아니다). LLM 추출이 끼어 결과가 환경마다 달라질 수 있다.

- check_01_roundtrip: REST로 뱅크 lab-check에 가상 문장을 retain → '주로 쓰는 언어' recall에 Python이 있는가
- check_01_restart : make stop → make start 뒤 같은 recall이 결과를 돌려주는가(기억이 디스크에 남는가)

세션 A/B가 쓰는 뱅크 lab은 건드리지 않는다(lab-check를 매번 새로 만든다).
"""
import json
import pathlib
import subprocess
import sys
import time

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "labs" / "01" / "tests"))
from conftest import read_env  # noqa: E402

env = read_env()
PORT = int(env.get("HINDSIGHT_API_PORT", "8888"))
B = f"http://127.0.0.1:{PORT}/v1/default/banks/lab-check"
FACT = "나는 데이터 분석에 Python을 주로 쓰고, 지금은 Acme에서 일한다."  # 가상 인물
QUERY = "내가 주로 쓰는 언어는?"
c = httpx.Client(timeout=900)
rows = []


def pad(s, n):
    """한글 폭(2칸)을 고려한 왼쪽 정렬."""
    import unicodedata
    w = sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in str(s))
    return str(s) + " " * max(0, n - w)



def recall():
    t = time.time()
    r = c.post(B + "/memories/recall", json={"query": QUERY})
    r.raise_for_status()
    texts = [x["text"] for x in r.json().get("results", [])]
    return texts, time.time() - t


def short(s, n=60):
    return s if len(s) <= n else s[: n - 1] + "…"


# roundtrip
c.delete(B)  # 지난 측정 지우기 (없으면 404)
c.put(B, json={})
t = time.time()
r = c.post(B + "/memories", json={"items": [{"content": FACT}], "async": False})
retain_s = time.time() - t
usage = (r.json().get("usage") or {}) if r.status_code == 200 else {}
texts, recall_s = recall()
hit = any("python" in x.lower() for x in texts[:3])
rows.append(("check_01_roundtrip", "Python 있음" if hit else "Python 없음",
             f"retain {retain_s:.1f}초 · recall {recall_s:.2f}초",
             f"LLM 토큰 입력 {usage.get('input_tokens', '?')} / 출력 {usage.get('output_tokens', '?')}",
             short(texts[0]) if texts else "(결과 없음)"))

# restart
t = time.time()
subprocess.run(["bash", str(ROOT / "hindsight" / "stop.sh")], check=True, capture_output=True)
subprocess.run(["bash", str(ROOT / "hindsight" / "start.sh")], check=True, capture_output=True)
restart_s = time.time() - t
texts2, recall2_s = recall()
hit2 = any("python" in x.lower() for x in texts2[:3])
rows.append(("check_01_restart", "Python 있음" if hit2 else "Python 없음",
             f"재시작 {restart_s:.1f}초 · recall {recall2_s:.2f}초",
             f"결과 {len(texts2)}개", short(texts2[0]) if texts2 else "(결과 없음)"))

out = ROOT / "data" / "check_01"
out.mkdir(parents=True, exist_ok=True)
(out / "last.json").write_text(json.dumps({"rows": rows, "recall_before": texts, "recall_after": texts2,
                                           "llm": f"{env.get('HINDSIGHT_API_LLM_PROVIDER')}/{env.get('HINDSIGHT_API_LLM_MODEL')}"},
                                          ensure_ascii=False, indent=1))

print(f"\ncheck_01 — 측정 (LLM {env.get('HINDSIGHT_API_LLM_PROVIDER')}/{env.get('HINDSIGHT_API_LLM_MODEL')}, 뱅크 lab-check, 질문 '{QUERY}')")
print(f"| {pad('측정', 18)} | {pad('결과', 11)} | {pad('시간', 30)} | {pad('비고', 28)} | 회상 1위")
print(f"|{'-'*20}|{'-'*13}|{'-'*32}|{'-'*30}|{'-'*10}")
for name, res, tm, note, top in rows:
    print(f"| {pad(name, 18)} | {pad(res, 11)} | {pad(tm, 30)} | {pad(note, 28)} | {top}")
print("(측정 결과는 data/check_01/last.json)")
