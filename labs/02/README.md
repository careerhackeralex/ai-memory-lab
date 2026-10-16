# 실습 02 — 다 넣기, 검색해 넣기, 정답 구간만 넣기를 재 보기

## 목표

- 같은 질문 10개를 세 방식으로 같은 답변 모델에 묻고, 방식별 입력 토큰과 정답 수를 표로 본다.
  - **A 다 넣기**: 메모 50개 전부 + 질문
  - **B 검색해 넣기**: Hindsight recall 결과(토큰 상한 300 고정) + 질문
  - **C 정답 구간만 넣기**: 라벨에 적힌 정답 메모만 + 질문 (Context Rot의 정답 구간(oracle) 조건)
- B와 C의 차이는 '검색이 놓친 몫', A와 C의 차이는 '긴 입력의 효과'로 읽는다. 승패를 가리는 실습이 아니라 재는 실습이다.

이어지는 실습: 실습 01(Hindsight 서버, 127.0.0.1:8888). 데이터는 모두 가상이다: 가상 인물 '하린'과 가상 회사 '벨로랩'의 연습 메모 50개(`data/memos_02.jsonl`), 질문 10개(`data/questions_02.jsonl`, 3개는 메모에 답이 없다). 실제 인물·회사와 겹치는 이름이 있다면 우연이다.

## 진행

1. **Hindsight와 뱅크 준비**: `make start EP=02`. 실습 01과 같은 설정(127.0.0.1, 임베딩 onnx의 `intfloat/multilingual-e5-small`)으로 서버를 띄우고, `labs/02/seed_02.py`가 메모 50개를 뱅크 `lab02`에 넣는다. seed는 한 번만 돈다(다시 실행하면 '건너뜀'). 실습 01을 건너뛰었다면 먼저 실습 01 README의 준비 1~3(`make check-env`, `.env`, `make models`)을 한다.
2. **compare.py 만들기**: 이 폴더에서 Claude Code를 열고(`claude`) `labs/02/PROMPT.md`의 상자 안 글을 붙여 넣는다. Claude가 `labs/02/INTERFACE.md`를 읽고 `labs/02/compare.py`를 쓴 뒤 `--dry-run`으로 첫 질문의 세 프롬프트를 보여 준다. 이 파일 쓰기와 `--dry-run`은 `.claude/settings.json`에서 미리 허용해 두었다.
3. **30회 답변 호출**: 터미널에서 `.venv/bin/python labs/02/compare.py`. 질문 10 × 방식 3 = 30번 `claude -p`를 격리 명령(labs/common.md)으로 부르고 `data/results_02.csv`에 쓴다.
4. **채점 표**: `make check EP=02`. test_02(데이터·결과 파일 검사)와 check_02 표를 본다.
5. 표를 Context Rot 보고서와 비교한다. 메모 50개(추정 약 1,500토큰)는 보고서의 약 113k 토큰보다 훨씬 짧아 A와 C의 차이가 작게 나와도 정상이다. 길이 효과는 입력이 길어야 보인다는 것도 관찰 거리다.

## 파일

| 파일 | 내용 |
|---|---|
| `INTERFACE.md` | compare.py와 check_02의 계약: 입력, 컨텍스트 형식, 프롬프트 틀, 결과 열, 정규화·채점 규칙, recall 상한 300 |
| `PROMPT.md` | Claude Code에 붙여 넣을 글 |
| `seed_02.py` | 메모 50개를 뱅크 lab02에 넣기(REST, 한 번만) |
| `check_02.py` | 채점과 표 (LLM 판정 없음) |
| `tests/` | test_02_data, test_02_normalize, test_check_02_schema / isolation / score |
| `../tokens.py` | `count_tokens()`: 입력 토큰 어림값(ASCII 아닌 글자 1자 = 1토큰, ASCII 4자 = 1토큰). 실제 토크나이저가 아니다 |

## 테스트와 측정

- **check_02_schema**: `data/results_02.csv`가 30행이고 question_id·method·input_tokens_est·answer·flags가 채워졌는지, input_tokens_est가 양수인지. input_tokens_usage가 비면 경고만 한다.
- **check_02_isolation**: flags 열에 `--safe-mode`(API 키 대안이면 `--bare`), `--tools ""`, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`이 있는지, 뱅크 lab02의 기억 목록과 recall 결과에 질문 문장이 없는지.
- **check_02_score**: 답 있는 7문항은 정규화한 답에 허용 키워드(accept) 하나가 들어 있으면 정답, 답 없는 3문항은 정규화한 답이 정확히 `모름`일 때만 정답. 정규화 = 소문자, 쉼표·공백 제거, 끝 마침표 제거.
- **check_02_report**: 방식별 평균 입력 토큰(추정치, usage)과 정답 수 표. 주석 'C = 정답 구간(oracle), B = 검색기'. 승패 기준은 없다.

## 시간과 비용

숫자는 2026-10-16 리허설(Mac mini M4 Pro 48GB, Claude Code 2.1.301, Ollama gemma3:12b) 기준이다.

- 시간(기계 시간, 사람이 읽는 시간 제외): `make start EP=02` 7~10분(서버 15초 + seed 422~554초), 프롬프트(compare.py 작성 + dry-run) 1~1.5분, compare.py 약 1분 40초(호출 30회, 평균 2.2초), `make check EP=02` 3~4초. 실습 01을 마친 상태에서 합계 약 10~13분.
- Claude Code 사용(구독이면 한도에서 차감, API 키면 과금. 아래는 Claude Code가 `total_cost_usd`로 보고한 명목값, 모델 claude-opus-5-5): 프롬프트 1회 0.65~0.71 USD, 답변 30회 0.20~0.49 USD. 답변 비용은 캐시에 따라 달라진다: 첫 실행은 프롬프트를 캐시에 쓰느라 비싸고(A 30% 넘게), 1시간 안에 같은 A 프롬프트를 다시 보내면 캐시 읽기로 싸진다.
- Hindsight LLM: 메모 50개 retain에 추출·통합 호출. Ollama는 로컬이라 0원, API 키 공급자면 입력 약 10만·출력 약 5,700 토큰(retain 50회)만큼 그 공급자 요금. recall은 LLM을 부르지 않는다.

## FAQ (막혔을 때, 위에서부터)

1. **A 방식에도 기억이 섞이는 것 같음**(답변 모델이 Hindsight MCP나 auto memory를 씀) → labs/common.md의 격리 명령을 그대로 쓴다. `--tools ""`만으로는 MCP 도구가 꺼지지 않고(→ `--safe-mode`), auto memory는 `--safe-mode`가 아니라 환경 변수 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1`이 끈다. check_02_isolation과 flags 열로 확인한다.
2. **`--bare`로 돌렸더니 인증 오류** → `--bare`는 구독 로그인(OAuth)과 키체인을 읽지 않고 `ANTHROPIC_API_KEY`(또는 apiKeyHelper)로만 인증한다. 구독 사용자는 기본 명령(`--safe-mode`)을 쓴다.
3. **`claude -p` 사용량 한도에 걸림** → `--limit 3`처럼 질문 수를 줄여 돌리고, 한도가 풀리면 다시 실행한다. 이미 있는 행은 건너뛰고 빈 행만 채운다. 실패한 호출은 `data/errors_02.log`에 있다.
4. **input_tokens_usage가 2나 3처럼 작게 나옴** → JSON의 `usage.input_tokens`는 캐시되지 않은 입력만 센다. Claude Code는 프롬프트를 자동으로 캐시하므로 INTERFACE.md대로 `input_tokens + cache_creation_input_tokens + cache_read_input_tokens`를 더한다. 필드 이름이 버전마다 다르면 비워 두고 input_tokens_est로 표를 읽는다(check_02는 경고만 한다).
5. **usage가 추정치보다 2천 토큰쯤 큼** → 정상이다. usage에는 Claude Code 자체 시스템 프롬프트가 들어 있고, 추정치는 우리가 보낸 프롬프트만 센 어림값이다. 방식끼리 비교할 때는 같은 덧셈이 붙는다.
6. **맞는 답이 오답으로 셈** → 표기가 흔들린 경우다('파이썬'과 'Python'). INTERFACE.md의 허용 키워드와 정규화 규칙을 확인하고 채점 코드는 고치지 않는다. '모름' 대신 '모르겠습니다'처럼 답하면 '모름'으로 세지 않으므로 프롬프트 틀에 고정 문장이 그대로 들어갔는지(`--dry-run`) 본다.
7. **seed가 오래 걸림** → 메모 50개 retain은 Hindsight LLM 추출과 통합을 부른다. Ollama gemma3:12b로 약 7~9분(리허설 422~554초). API 키 공급자면 시간 대신 사용량이 든다. 한 번만 하고 `make reset` 전까지 재사용한다.
8. **seed 도중 끊김** → `make start EP=02`를 다시 실행하면 이미 들어간 메모는 건너뛰고 나머지만 넣는다.
9. **한국어 메모의 recall이 약함** → `hindsight/.env`가 임베딩 공급자 onnx(`intfloat/multilingual-e5-small`)와 재순위 rrf를 지정하는지 `make check EP=01`의 test_01_embedding으로 확인한다(Hindsight 기본은 영어 전용 모델). 메모를 넣은 뒤 공급자를 바꿨다면 `make reset` 뒤 `make start EP=02`로 다시 넣는다.
10. **B의 컨텍스트에 메모 원문이 아닌 문장이 나옴** → 정상이다. Hindsight는 메모에서 사실을 뽑아 저장하고(`… | Involving: 하린`), recall은 그 사실을 돌려준다. 그래서 B는 '원문 검색'이 아니라 '기억 시스템이 고른 결과'다.
11. **결과가 Context Rot 보고서와 다름** → 정상이다. 보고서의 300토큰은 정답 구간이고 B는 검색기가 고른 것이며, 메모 50개는 보고서의 약 113k 토큰보다 훨씬 짧다.
12. **표가 매번 조금씩 다름** → 답변 모델이 매번 같은 답을 하지 않는다. 한 번의 표는 측정 1회다.
