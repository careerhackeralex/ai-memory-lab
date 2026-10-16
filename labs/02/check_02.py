"""check_02: data/results_02.csv를 INTERFACE.md 규칙으로 확인하고 채점해 표로 보여 준다. LLM 판정 없음.

- check_02_schema   : 30행(질문 10 × 방식 A·B·C), 필수 열이 채워졌는지, input_tokens_est가 양수인지
                      (input_tokens_usage가 비어 있으면 경고만)
- check_02_isolation: flags에 --safe-mode(또는 --bare), --tools "", CLAUDE_CODE_DISABLE_AUTO_MEMORY=1이 있는지,
                      뱅크 lab02에 질문 문장이 저장되지 않았는지(recall 결과와 기억 목록에 질문이 없는지)
- check_02_score    : 답 있는 7문항은 허용 키워드 부분 일치, 답 없는 3문항은 정확히 '모름'
- check_02_report   : 방식별 평균 입력 토큰(추정치·usage)과 정답 수 표. 승패 기준은 없다(측정)

pytest(labs/02/tests)가 schema·isolation·score를 통과/실패로 보고, 이 파일을 직접 실행하면 표를 출력한다.
"""
import csv
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULTS = ROOT / "data" / "results_02.csv"
QUESTIONS = ROOT / "data" / "questions_02.jsonl"
COLUMNS = ["question_id", "method", "input_tokens_est", "input_tokens_usage", "answer", "flags"]
REQUIRED = ["question_id", "method", "input_tokens_est", "answer", "flags"]
METHODS = ["A", "B", "C"]
LABEL = {"A": "A 다 넣기", "B": "B 검색해 넣기", "C": "C 정답 구간만"}
BANK = "lab02"


def normalize(s: str) -> str:
    """소문자 → 쉼표·모든 공백 제거 → 끝의 마침표 제거."""
    s = "".join(ch for ch in s.lower() if ch != "," and not ch.isspace())
    return s.rstrip(".")


def is_correct(answer: str, q: dict) -> bool:
    a = normalize(answer)
    if q["has_answer"]:
        return any(normalize(k) in a for k in q["accept"])
    return a == "모름"


def load_questions() -> list[dict]:
    return [json.loads(x) for x in QUESTIONS.read_text().splitlines() if x.strip()]


def load_results(path: pathlib.Path = RESULTS) -> tuple[list[str], list[dict]]:
    if not path.exists():
        raise FileNotFoundError(f"{path.relative_to(ROOT)}가 없습니다. 먼저 compare.py를 실행하세요.")
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        return list(r.fieldnames or []), list(r)


def check_02_schema(header: list[str], rows: list[dict], questions: list[dict]) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    if header != COLUMNS:
        errors.append(f"열이 다릅니다: {header} (필요: {COLUMNS})")
    want = {(q["id"], m) for q in questions for m in METHODS}
    got = [(r.get("question_id"), r.get("method")) for r in rows]
    if len(rows) != len(want):
        errors.append(f"행 수 {len(rows)} (필요: {len(want)} = 질문 {len(questions)} × 방식 {len(METHODS)})")
    if missing := sorted(want - set(got)):
        errors.append(f"빠진 행 {len(missing)}개: {', '.join(q + m for q, m in missing[:10])}")
    if dup := sorted({k for k in got if got.count(k) > 1}):
        errors.append(f"중복 행: {dup}")
    for i, r in enumerate(rows, 2):
        for col in REQUIRED:
            if not (r.get(col) or "").strip():
                errors.append(f"{i}행 {col}이 비어 있습니다")
        est = (r.get("input_tokens_est") or "").strip()
        if est and not (est.isdigit() and int(est) > 0):
            errors.append(f"{i}행 input_tokens_est가 양의 정수가 아닙니다: {est!r}")
        usage = (r.get("input_tokens_usage") or "").strip()
        if not usage:
            warnings.append(f"{i}행 input_tokens_usage가 비어 있습니다(JSON usage를 찾지 못함)")
        elif not usage.isdigit():
            errors.append(f"{i}행 input_tokens_usage가 정수가 아닙니다: {usage!r}")
    return errors, warnings


def check_02_isolation_flags(rows: list[dict]) -> list[str]:
    errors = []
    for i, r in enumerate(rows, 2):
        f = r.get("flags") or ""
        miss = []
        if "--safe-mode" not in f and "--bare" not in f:
            miss.append("--safe-mode(또는 --bare)")
        if '--tools ""' not in f and "--tools ''" not in f:
            miss.append('--tools ""')
        if "CLAUDE_CODE_DISABLE_AUTO_MEMORY=1" not in f:
            miss.append("CLAUDE_CODE_DISABLE_AUTO_MEMORY=1")
        if miss:
            errors.append(f"{i}행({r.get('question_id')}{r.get('method')}) flags에 없음: {', '.join(miss)}")
    return errors


def bank_texts(base: str) -> list[str]:
    """뱅크 lab02에 저장된 기억 단위 텍스트 전부."""
    import httpx
    out, offset = [], 0
    with httpx.Client(timeout=60) as c:
        while True:
            r = c.get(f"{base}/v1/default/banks/{BANK}/memories/list", params={"limit": 200, "offset": offset})
            r.raise_for_status()
            items = r.json().get("items", [])
            out += [x.get("text") or "" for x in items]
            if len(items) < 200:
                return out
            offset += 200


def check_02_isolation_bank(questions: list[dict], base: str) -> list[str]:
    """질문 문장이 lab02에 저장되지 않았는지: 기억 목록과 recall 결과에 질문 문장(정규화)이 없어야 한다."""
    import httpx
    errors = []
    texts = [normalize(t) for t in bank_texts(base)]
    with httpx.Client(timeout=60) as c:
        for q in questions:
            nq = normalize(q["question"])
            if any(nq in t for t in texts):
                errors.append(f"{q['id']} 질문 문장이 뱅크 {BANK}의 기억에 들어 있습니다")
                continue
            r = c.post(f"{base}/v1/default/banks/{BANK}/memories/recall", json={"query": q["question"], "max_tokens": 300})
            r.raise_for_status()
            if any(nq in normalize(x.get("text") or "") for x in r.json().get("results", [])):
                errors.append(f"{q['id']} 질문 문장이 recall됩니다")
    return errors


def check_02_score(rows: list[dict], questions: list[dict]) -> dict:
    qs = {q["id"]: q for q in questions}
    score = {m: {"answerable": 0, "unanswerable": 0, "est": [], "usage": [], "wrong": []} for m in METHODS}
    for r in rows:
        q, m = qs.get(r["question_id"]), r["method"]
        if not q or m not in score:
            continue
        s = score[m]
        s["est"].append(int(r["input_tokens_est"]))
        if (r.get("input_tokens_usage") or "").strip().isdigit():
            s["usage"].append(int(r["input_tokens_usage"]))
        if is_correct(r["answer"], q):
            s["answerable" if q["has_answer"] else "unanswerable"] += 1
        else:
            s["wrong"].append((q["id"], r["answer"]))
    return score


def _w(s: str) -> int:
    import unicodedata
    return sum(2 if unicodedata.east_asian_width(ch) in "WF" else 1 for ch in s)


def _pad(s, n, right=False):
    s = str(s)
    sp = " " * max(0, n - _w(s))
    return sp + s if right else s + sp


def check_02_report(score: dict, questions: list[dict]) -> str:
    n_ans = sum(1 for q in questions if q["has_answer"])
    n_un = len(questions) - n_ans
    avg = lambda xs: f"{sum(xs) / len(xs):,.0f}" if xs else "-"  # noqa: E731
    head = ["방식", "평균 입력 토큰(추정)", "평균 입력 토큰(usage)", f"답 있는 {n_ans}문항 정답", f"답 없는 {n_un}문항 '모름'"]
    body = []
    for m in METHODS:
        s = score[m]
        body.append([LABEL[m], avg(s["est"]), avg(s["usage"]), f"{s['answerable']} / {n_ans}", f"{s['unanswerable']} / {n_un}"])
    width = [max(_w(str(r[i])) for r in [head] + body) for i in range(len(head))]
    lines = ["| " + " | ".join(_pad(h, w) for h, w in zip(head, width)) + " |",
             "|" + "|".join("-" * (w + 2) for w in width) + "|"]
    for cells in body:
        lines.append("| " + " | ".join(_pad(c, w, right=i > 0) for i, (c, w) in enumerate(zip(cells, width))) + " |")
    lines.append("주: C = 정답 구간(oracle), B = 검색기. 승패 기준 없는 측정이다. usage에는 Claude Code 시스템 프롬프트가 포함된다.")
    return "\n".join(lines)


def main() -> int:
    sys.path.insert(0, str(ROOT / "labs" / "01" / "tests"))
    from conftest import read_env
    base = f"http://127.0.0.1:{int(read_env().get('HINDSIGHT_API_PORT', '8888'))}"
    questions = load_questions()
    try:
        header, rows = load_results()
    except FileNotFoundError as e:
        print(f"✗ {e}")
        return 1
    errors, warnings = check_02_schema(header, rows, questions)
    print(f"check_02_schema    : {'통과' if not errors else '실패'} — {len(rows)}행" + (f", 경고 {len(warnings)}개" if warnings else ""))
    for e in errors[:10]:
        print(f"  ✗ {e}")
    for w in warnings[:3]:
        print(f"  ! {w}")
    iso = check_02_isolation_flags(rows)
    try:
        iso += check_02_isolation_bank(questions, base)
        bank_note = "질문 문장 저장 없음"
    except Exception as e:  # 서버가 꺼져 있으면 flags만 본다
        iso.append(f"뱅크 {BANK}를 확인하지 못했습니다(make start EP=02): {type(e).__name__}")
        bank_note = "뱅크 확인 못 함"
    print(f"check_02_isolation : {'통과' if not iso else '실패'} — flags 격리 3종, {bank_note}")
    for e in iso[:10]:
        print(f"  ✗ {e}")
    if errors:
        return 1
    score = check_02_score(rows, questions)
    print("check_02_score     : 채점 완료 (허용 키워드 부분 일치 / 정확히 '모름', LLM 판정 없음)")
    print()
    print("check_02_report — 방식별 평균 입력 토큰과 정답 수")
    print(check_02_report(score, questions))
    wrong = {m: score[m]["wrong"] for m in METHODS if score[m]["wrong"]}
    if wrong:
        print("\n틀린 답 (question_id: 답)")
        for m, ws in wrong.items():
            for qid, a in ws:
                print(f"  {m} {qid}: {a.splitlines()[0][:70] if a else '(빈 답)'}")
    out = ROOT / "data" / "check_02"
    out.mkdir(parents=True, exist_ok=True)
    (out / "last.json").write_text(json.dumps({m: {k: v for k, v in score[m].items()} for m in METHODS},
                                              ensure_ascii=False, indent=1))
    print("(채점 결과는 data/check_02/last.json)")
    return 1 if iso else 0


if __name__ == "__main__":
    sys.exit(main())
