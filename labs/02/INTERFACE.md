# 실습 02 계약 (INTERFACE)

compare.py와 check_02가 함께 지키는 약속이다. compare.py는 이 문서대로 만들고, 채점은 check_02만 한다.

## 입력 파일 (읽기만 한다)

| 파일 | 한 줄 | 내용 |
|---|---|---|
| `data/memos_02.jsonl` | `{"id": "m01", "date": "2025-03-10", "text": "..."}` | 연습 메모 50개. 가상 인물 하린과 가상 회사 벨로랩 |
| `data/questions_02.jsonl` | `{"id": "q01", "question": "...", "has_answer": true, "accept": ["성수", "seongsu"], "gold_memo_ids": ["m03", "m31"]}` | 질문 10개. 7개는 답이 있고 3개는 없다(`has_answer: false`, `accept`·`gold_memo_ids`는 빈 목록) |

- `accept`: 정답으로 인정하는 키워드 목록(동의어·표기 변형 포함, 예: `python`·`파이썬`).
- `gold_memo_ids`: 답에 필요한 메모(정답 구간, oracle). 사실이 바뀐 질문은 옛 메모와 새 메모를 함께 적었다.
- compare.py는 질문 문장, `accept`, `gold_memo_ids`를 Hindsight에 저장하지 않는다(평가 데이터 오염 방지). Hindsight에는 recall 요청만 보낸다.

## 세 방식 (다른 것은 컨텍스트뿐)

| method | 컨텍스트 |
|---|---|
| `A` | 메모 50개 전부, 파일 순서 그대로 |
| `B` | Hindsight recall 결과. 뱅크 `lab02`, 질문 문장을 그대로 query로, **`max_tokens: 300`**(recall 토큰 상한, 고정) |
| `C` | 그 질문의 `gold_memo_ids` 메모만, 파일 순서대로 |

컨텍스트 한 줄의 형식은 셋 다 같다: `- [YYYY-MM-DD] 내용`

- A·C: `date`와 `text`.
- B: recall 결과 `results[]`를 받은 순서대로, 각 항목의 `text`와 날짜(`occurred_start`, 없으면 `mentioned_at`의 앞 10자리, 둘 다 없으면 `- 내용`).

B의 recall 요청 (hindsight-api 1.0.0):

```
POST http://127.0.0.1:8888/v1/default/banks/lab02/memories/recall
{"query": "<질문 문장>", "max_tokens": 300}
```

`max_tokens`는 recall이 돌려줄 사실 텍스트의 토큰 상한이다(기본 4096, 순위가 높은 사실부터 채운다. hindsight_api/engine/fact_budget.py). 메모 50개 전체가 그보다 작아 기본값이면 A와 B가 거의 같아지므로 300으로 고정한다. Context Rot 보고서의 정답 구간 약 300토큰과 같은 크기다(단, 토큰 세는 방법은 다르다).

## 프롬프트 틀 (세 방식 공통, 글자 그대로)

```
아래는 한 사람에 대한 메모다.
<메모>
{컨텍스트 줄들}
</메모>
질문: {question}
메모에 답이 없으면 정확히 모름이라고만 답한다. 답이 있으면 한 줄로 짧게 답한다.
```

## 답변 호출 (labs/common.md의 격리 명령)

```bash
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude -p "<프롬프트>" --safe-mode --tools "" --no-session-persistence --output-format json < /dev/null
```

- 세 방식 모두 같은 명령, 같은 모델(계정 기본 모델, `--model`을 주지 않는다).
- API 키 사용자는 `--safe-mode` 대신 `--bare`를 쓸 수 있다(labs/common.md). 환경 변수 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`은 어느 쪽이든 붙인다.
- 실패(종료 코드 ≠ 0, JSON이 아님, `is_error: true`)면 3회까지 재시도한다. 그래도 실패하면 그 행은 쓰지 않고 `data/errors_02.log`에 남긴다(다시 실행하면 빈 행만 채운다).

## 출력 파일 `data/results_02.csv`

열(이 순서, 머리줄 포함): `question_id,method,input_tokens_est,input_tokens_usage,answer,flags`

| 열 | 값 |
|---|---|
| `question_id` | `q01`…`q10` |
| `method` | `A`·`B`·`C` |
| `input_tokens_est` | 보낸 프롬프트 전체를 `labs/tokens.py`의 `count_tokens()`로 센 값(양의 정수) |
| `input_tokens_usage` | JSON `usage`의 `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`. 필드가 없으면 비운다 |
| `answer` | JSON의 `result` 문자열(앞뒤 공백만 지움) |
| `flags` | 실제로 쓴 명령줄 문자열. 기본값이면 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude -p --safe-mode --tools "" --no-session-persistence --output-format json` |

- usage 필드 이름(Claude Code 2.1.301, 리허설 확인): `usage.input_tokens`는 **캐시되지 않은 입력만** 센다(예: 2). Claude Code는 시스템 프롬프트를 자동으로 캐시하므로 실제 입력은 `cache_creation_input_tokens`와 `cache_read_input_tokens`에 나뉘어 들어간다. 그래서 셋을 더한다. 이 합에는 Claude Code 자체 시스템 프롬프트(약 2천 토큰)도 들어 있어 `input_tokens_est`보다 크다.
- 이미 있는 `(question_id, method)` 행은 건너뛴다. `--limit N`은 앞에서 N개 질문만 돌린다(사용량 한도에 걸렸을 때 나눠 돌리기).
- compare.py는 정답을 판정하지 않고, 어느 방식이 이길지 예상하는 코드를 넣지 않는다.

## 채점 (check_02만 한다, LLM 없음)

정규화: 소문자로 바꾸고, 쉼표(`,`)와 모든 공백을 지우고, 끝의 마침표(`.`)를 지운다. 키워드에도 같은 정규화를 한다.

- 답이 있는 7문항: 정규화한 답에 정규화한 `accept` 키워드 하나라도 부분 문자열로 들어 있으면 정답.
- 답이 없는 3문항: 정규화한 답이 정확히 `모름`일 때만 정답. `모르겠습니다`, `메모에 없음`은 정답이 아니다.

## 그 밖의 고정값

| 항목 | 값 |
|---|---|
| Hindsight 주소 | `http://127.0.0.1:8888` |
| 뱅크 | `lab02` (`make start EP=02`가 메모 50개를 한 번 넣는다. `labs/02/seed_02.py`). 관찰 통합 꺼짐(`enable_observations: false`): recall은 메모에서 추출한 사실만 돌려준다 |
| recall 토큰 상한 | `max_tokens: 300` |
| 답변 호출 수 | 질문 10 × 방식 3 = 30 |
