# 실습 02 프롬프트

아래 상자 안의 글을 그대로 복사해 이 저장소 폴더에서 연 Claude Code에 붙여 넣는다.
붙여 넣기 전에 `make start EP=02`가 '상태' 블록과 `lab02 : 문서 50개`를 출력했는지 확인한다(README 진행 1).

```text
이 저장소(ai-memory-lab)의 실습 02를 진행해 줘. 목표는 labs/02/compare.py를 만드는 것이야. 질문 10개마다 세 방식(A 메모 50개 전부, B Hindsight recall 결과, C 정답 구간 메모만)으로 컨텍스트를 만들어 같은 답변 모델에 묻고, 답과 입력 토큰을 data/results_02.csv에 남기는 측정 스크립트다.

먼저 읽을 것: labs/02/INTERFACE.md(계약), labs/common.md(격리 명령), labs/tokens.py(count_tokens), data/memos_02.jsonl과 data/questions_02.jsonl의 첫 줄.

지킬 것
1. INTERFACE.md를 그대로 따른다: 입력 파일, 컨텍스트 줄 형식, 프롬프트 틀(고정 문장 '메모에 답이 없으면 정확히 모름이라고만 답한다' 포함), 결과 열(question_id, method, input_tokens_est, input_tokens_usage, answer, flags), 뱅크 lab02, recall 토큰 상한 max_tokens 300.
2. compare.py는 data/ 파일만 읽는다. 질문 문장과 정답 라벨(accept, gold_memo_ids)을 Hindsight에 저장하지 않는다. Hindsight에는 B의 recall 요청만 보낸다.
3. 세 방식의 답변 모델, 프롬프트 틀, 출력 형식을 똑같이 둔다. 다른 것은 컨텍스트 내용뿐이다.
4. 답변 호출은 labs/common.md의 격리 명령을 그대로 쓴다: 환경 변수 CLAUDE_CODE_DISABLE_AUTO_MEMORY=1, claude -p, --safe-mode, --tools "", --no-session-persistence, --output-format json, 표준 입력은 /dev/null. --tools ""는 내장 도구만 끄므로 --safe-mode를 빼지 않는다. 쓴 명령줄을 flags 열에 기록한다.
5. 입력 토큰은 두 값으로 남긴다: labs/tokens.py의 count_tokens()로 보낸 프롬프트 전체를 센 추정치, JSON usage에서 INTERFACE.md가 정한 대로 읽은 값(없으면 비움).
6. 정답 판정에 LLM을 쓰지 않는다. compare.py는 답과 토큰만 기록하고 채점하지 않는다. 어느 방식이 이길지 예상하는 코드를 넣지 않는다.
7. 호출이 실패하면 3회까지 재시도하고, 그래도 실패하면 data/errors_02.log에 남긴다. 이미 있는 (question_id, method) 행은 건너뛴다. --limit N(앞 N개 질문만)과 --dry-run(호출 없이 첫 질문의 세 프롬프트와 추정 토큰만 출력) 옵션을 둔다. 진행 상황을 호출마다 한 줄씩 출력한다.
8. 표준 라이브러리와 httpx만 쓴다(.venv에 있음). hindsight/.env는 열지 않는다. 다른 파일은 고치지 않는다.

순서
1. labs/02/compare.py를 쓴다.
2. .venv/bin/python labs/02/compare.py --dry-run 을 실행해 첫 질문의 A·B·C 프롬프트와 추정 토큰을 보여 줘. 실제 답변 호출 30회는 내가 터미널에서 직접 돌린다.
3. 마지막에 내가 칠 명령 두 줄을 코드 블록으로 출력해 줘:
   .venv/bin/python labs/02/compare.py
   make check EP=02
```
