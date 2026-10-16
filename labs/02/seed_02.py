"""seed_02: 연습 메모 50개(data/memos_02.jsonl)를 뱅크 lab02에 한 번 넣는다. make start EP=02가 부른다.

- REST retain(async=false, 추출이 끝날 때까지 기다림), 메모 하나 = 문서 하나(document_id = 메모 id),
  timestamp = 메모 날짜.
- 이미 들어간 메모는 건너뛴다. 50개가 다 있으면 아무것도 하지 않는다(make reset 전까지 재사용).
- 질문 파일(data/questions_02.jsonl)은 읽지 않는다. 질문과 정답 라벨은 Hindsight에 넣지 않는다.
- 뱅크 lab02는 관찰(observation) 통합을 끈다(enable_observations=false, 뱅크 설정). 통합은 retain 뒤에
  비동기로 돌아 recall 결과가 seed 직후·몇 분 뒤에 달라지고, Ollama gemma3:12b에서는 메모 50개 통합 요청이
  LLM 시간 제한(120초)에 걸려 재시도를 반복했다(리허설). 그래서 B는 추출된 사실(world)만 검색한다.
  통합과 관찰은 EP3에서 다룬다.
"""
import json
import pathlib
import sys
import time

import httpx

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "labs" / "01" / "tests"))
from conftest import read_env  # noqa: E402

env = read_env()
PORT = int(env.get("HINDSIGHT_API_PORT", "8888"))
BANK = "lab02"
B = f"http://127.0.0.1:{PORT}/v1/default/banks/{BANK}"
BATCH = 10


def existing_ids(c: httpx.Client) -> set[str]:
    ids, offset = set(), 0
    while True:
        r = c.get(B + "/documents", params={"limit": 100, "offset": offset})
        if r.status_code == 404:
            return ids
        r.raise_for_status()
        items = r.json().get("items", [])
        ids |= {d["id"] for d in items}
        if len(items) < 100:
            return ids
        offset += 100


def main() -> int:
    memos = [json.loads(x) for x in (ROOT / "data" / "memos_02.jsonl").read_text().splitlines() if x.strip()]
    c = httpx.Client(timeout=1800)
    c.put(B, json={}).raise_for_status()
    c.patch(B + "/config", json={"updates": {"enable_observations": False}}).raise_for_status()
    have = existing_ids(c)
    todo = [m for m in memos if m["id"] not in have]
    print(f"• 뱅크 {BANK}: 메모 {len(memos)}개 중 {len(memos) - len(todo)}개가 이미 있음")
    if not todo:
        print("• seed 건너뜀 (처음부터 다시 넣으려면 make reset)")
    else:
        llm = env.get("HINDSIGHT_API_LLM_PROVIDER", "?") + "/" + env.get("HINDSIGHT_API_LLM_MODEL", "?")
        print(f"• {len(todo)}개 넣는 중 (retain, LLM {llm}, {BATCH}개씩. Ollama면 몇 분 걸린다)")
        t0, tin, tout = time.time(), 0, 0
        for i in range(0, len(todo), BATCH):
            part = todo[i:i + BATCH]
            t = time.time()
            r = c.post(B + "/memories", json={"async": False, "items": [
                {"content": m["text"], "timestamp": m["date"] + "T09:00:00Z", "document_id": m["id"]} for m in part]})
            if r.status_code != 200:
                print(f"✗ retain 실패 (HTTP {r.status_code}): {r.text[:300]}")
                print("  tail -n 50 data/logs/hindsight.log 로 LLM 오류를 확인하세요.")
                return 1
            u = r.json().get("usage") or {}
            tin += u.get("input_tokens") or 0
            tout += u.get("output_tokens") or 0
            print(f"  {part[0]['id']}–{part[-1]['id']}  {time.time() - t:5.1f}초", flush=True)
        print(f"• seed 완료: {time.time() - t0:.0f}초, LLM 토큰 입력 {tin:,} / 출력 {tout:,}")
    docs = len(existing_ids(c))
    stats = c.get(B + "/stats").json()
    by = stats.get("nodes_by_fact_type") or {}
    kinds = ", ".join(f"{k} {v}" for k, v in sorted(by.items())) or "-"
    print(f"  lab02    : 문서 {docs}개, 기억 단위 {stats.get('total_nodes', '?')}개 ({kinds}), 관찰 통합 꺼짐")
    return 0 if docs >= len(memos) else 1


if __name__ == "__main__":
    sys.exit(main())
