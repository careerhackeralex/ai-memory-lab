# 실습 04 — 원본은 지키고 사실은 고치기

## 목표

- 미니 메모리에 **원본 기록(이벤트)**을 따로 둔다: 대화 한 줄을 `events` 테이블에 추가만 하고, 지우거나 고치지 않는다(SQLite 트리거가 DELETE·UPDATE를 막는다). MCP 도구 `record_event`.
- 기억 한 조각(claim)은 근거를 가리킨다: `derived_from`(이벤트 `evt_…`·claim `clm_…` id 목록)과 `quote`(원문 인용). 인용이 원문에 없으면 저장하지 않는다.
- 사실이 바뀌면 **지우지 않고 대체한다**: `supersede`가 새 claim을 만들고 옛 claim을 `superseded`로 둔다. `recall`은 기본으로 현재 사실만, `include_history=true`면 이력까지 시간 순으로 보여 준다.
- (선택) `claude -p`가 대화에서 뽑은 claim의 인용이 원문에 실제로 있는지 잰다(check_04).

이어지는 실습: 실습 03(claims, `remember`·`recall`). 실습 03을 끝내지 못했어도 `make start EP=04`가 `labs/03/solution`을 시작점으로 둔다(내 코드는 `backup/`에 남는다). 이번 실습은 Hindsight를 쓰지 않는다. 데이터는 모두 가상이다: 가상 인물 '하린'과 가상 회사 '벨로랩'의 대화 10턴(`data/conv_04.jsonl`, 3월에 월 9,900원이던 Acme 팀 플랜이 4월에 월 12,900원으로 오른다). 실제 인물·회사와 겹치는 이름이 있다면 우연이다. 룬(Luhn) 검사를 통과하는 카드 번호는 넣지 않았다.

**event** = 원본 기록(대화 한 줄, 문서 한 단락). 지우지 않는다. **claim** = 원본에서 뽑은 기억 한 조각. 고칠 때는 대체한다.

## 진행

1. **시작점 확인**: `make start EP=04`. 내 `mini_memory/`로 test_03(8개)을 돌려 통과하면 그대로 이어 가고, 통과하지 못하거나 없으면 내 코드를 `backup/mini_memory-<시각>/`으로 옮기고 `labs/03/solution`을 `mini_memory/`로 복사한다. 마지막에 `labs/04/INTERFACE.md`를 출력한다.
2. **구현**: 이 폴더에서 Claude Code를 열고(`claude`) `labs/04/PROMPT.md`의 상자 안 글을 붙여 넣는다. Claude가 INTERFACE.md와 테스트를 읽고 `mini_memory/`를 고친 뒤 `make check EP=04`가 통과할 때까지 고친다.
3. **테스트**: `make check EP=04` → test_03 `8 passed` + test_04 `8 passed`. 테스트는 고치지 않는다.
4. **Claude Code에서 MCP로 원본·사실·이력 보기**: 실습 03에서 `claude mcp add`를 했다면 Claude Code를 다시 열기만 하면 된다(`/mcp`에서 `mini-memory · connected`, 도구 4개). 처음이면 저장소 폴더에서
   ```bash
   claude mcp add --transport stdio mini-memory -- uv run --project mini_memory mini-memory serve
   ```
   를 실행하고 다시 연다. 그리고 예를 들어 이렇게 묻는다:
   ```text
   data/conv_04.jsonl은 가상 인물 하린과 AI 에이전트의 대화다. mini-memory 도구로 다음을 순서대로 해 줘.
   1. 대화 10턴을 record_event로 원문 그대로 넣는다. source는 conv_04.jsonl#t01 형식으로 적는다.
   2. t01을 근거로 "벨로랩의 Acme 팀 플랜은 월 9,900원이다"를 remember로 저장한다. type은 semantic, derived_from은 t01 이벤트 id, quote는 t01 원문에서 글자 그대로 복사한다.
   3. t05를 근거로 그 claim을 supersede해 새 요금으로 바꾼다. derived_from은 t05 이벤트 id, quote는 t05 원문에서 글자 그대로 복사한다.
   4. 원문에 없는 quote "이미 12,900원으로 고쳤어"와 derived_from t09로 remember를 한 번 시도해 거절되는 것을 보여 준다.
   5. recall("Acme 팀 플랜")과 recall("Acme 팀 플랜", include_history=true)의 결과를 나란히 보여 준다.
   ```
5. **터미널에서 같은 일**: 관리자 변경(t03 서윤 → t07 하린)을 `mm`으로 해 본다. `clm_…`·`evt_…`는 앞 명령의 출력에서 복사한다.
   ```bash
   cd mini_memory
   uv run mm remember "벨로랩의 Acme 관리자는 디자인팀 서윤이다" --type semantic
   uv run mm record-event "결제일은 그대로 5일이야. 그리고 이번 달부터 Acme 관리자는 서윤 님 대신 내가 맡기로 했어." --source conv_04.jsonl#t07
   uv run mm supersede clm_… "벨로랩의 Acme 관리자는 하린이다" --derived-from evt_… --quote "서윤 님 대신 내가 맡기로 했어"
   uv run mm recall "Acme 관리자" --include-history
   cd ..
   ```
6. **(선택) 추출 환각 재기**: `.venv/bin/python labs/04/check_04.py`. `claude -p`(labs/common.md의 격리 명령, 1회)가 conv_04에서 claim과 인용을 JSON으로 뽑고, 스크립트가 대화를 `record_event`로, claim을 `remember(…, derived_from, quote)`로 넣어 인용 검사의 통과·거절 수를 표로 보여 준다. 결과는 `data/check_04/result.md`(첫 줄에 쓴 명령). 측정용 DB를 따로 써서 내 실습 DB는 건드리지 않는다. 호출 없이 프롬프트만 보려면 `--dry-run`.

### 참고: conv_04에서 바뀌는 사실 (정답표가 아니라 한 가지 읽기)

| 사실 | 3월 (t01·t03) | 4월 (t05·t07) | 처리 |
|---|---|---|---|
| Acme 팀 플랜 요금 | 월 9,900원 | 월 12,900원 | supersede (옛 claim은 superseded로 남음) |
| Acme 관리자 | 디자인팀 서윤 | 하린 | supersede |
| 결제일 | 매달 5일 | 그대로 5일 (t07) | 그대로 |
| 예산 문서 수정 | — | 다음 주 금요일까지 (t09) | 일화 `episodic` 추가 |

t09의 `“월 9,900원”`은 굽은 따옴표다. quote를 곧은 따옴표(`"`)로 적어도 INTERFACE.md의 정규화 덕분에 인용 검사를 통과한다.

## 파일

| 파일 | 내용 |
|---|---|
| `INTERFACE.md` | 계약: record_event·remember(+derived_from, quote)·supersede·recall(+include_history), events·claims 스키마, 트리거, 인용 정규화 규칙, 시계, `mm` 하위 명령, 뒤 편(EP5·EP7·EP8·EP10) 약속 |
| `PROMPT.md` | Claude Code에 붙여 넣을 글 |
| `start_04.sh` | `make start EP=04`: test_03 확인 → (필요하면) `backup/`으로 옮기고 `labs/03/solution` 복사 → INTERFACE.md |
| `tests/` | test_04 8개. 테스트마다 임시 DB로 `uv run mini-memory serve`와 `uv run mm`을 실제로 띄운다 |
| `check_04.py` | (선택) `claude -p` 추출 → 인용 검사 통과·거절 표 |
| `solution/` | 이 편의 참고 구현(test_03 + test_04 통과). 막혔을 때 비교용 |
| `../03/solution/` | 실습 03 참고 구현. `make start EP=04`의 시작점 |
| `../../data/conv_04.jsonl` | 가상 대화 10턴 (`{"id", "at", "role", "text"}`) |
| `../../data/sample_memory_04_old.md`·`_new.md`, `sample_source_04.md`·`sample_summary_04.md` | 영상의 따라 하기 프롬프트 1·2를 시험해 볼 가상 메모리 파일 |

## 테스트

| 테스트 | 확인하는 것 |
|---|---|
| test_04_tools | tools/list에 remember·recall·record_event·supersede가 모두 있고, 시리즈 고정 목록 밖 이름이 없다. 개수는 세지 않는다 |
| test_04_events_append_only | events에 직접 DELETE(한 행·전체), content를 바꾸는 UPDATE(길이가 다른 글, 같은 글자 수의 다른 글)가 모두 `sqlite3.DatabaseError` 계열 예외이고 행 수·내용이 그대로. 오류 문구는 보지 않는다 |
| test_04_supersede | t1 '월 9,900원'(semantic) → t2에 type 없이 '월 12,900원'으로 supersede: 기본 recall엔 새 claim만, 옛 claim은 superseded·content 그대로, 새 claim.supersedes = 옛 id, type = semantic, recorded_at = t2 |
| test_04_history | include_history=true 결과가 (recorded_at, id) 오름차순. 같은 시각의 claim끼리는 id 순 |
| test_04_derived_from | record_event의 id(`evt_`)를 derived_from으로 준 claim의 recall 항목에 그 id가 있다 |
| test_04_quote_must_exist | 원문에 없는 quote는 거절되고 claims 수가 늘지 않는다(대조: 따옴표·공백만 다른 인용은 저장) |
| test_04_no_double_supersede | 이미 대체된 claim을 다시 supersede하면 오류 |
| test_04_backcompat | test_03 8개가 그대로 통과(`remember(content, type)`만으로 동작) |

## 시간과 비용

숫자는 2026-10-20 리허설 2·3회차(Mac mini M4 Pro 48GB, Claude Code 2.1.305, 깨끗한 클론, 커밋 9be15eb) 기준이다.

- 시간(기계 시간, 사람이 읽는 시간 제외): `make start EP=04` 약 7초(test_03 + 시작점 복사), 프롬프트(구현 + `make check`) 104~150초, `make check EP=04` 약 13초(test_03 8개 + test_04 8개, backcompat이 test_03을 한 번 더 돈다), MCP로 원본·사실·이력 보기(4단계) 35~37초, `uv run mm` 한 번에 약 3초, check_04 25~33초, 따라 하기 프롬프트 1·2 각 16~26초. 합계 약 4~5분. 시청자 실제 소요는 읽기·붙여 넣기·Claude Code 다시 열기를 더해 약 20분(선택 과제 포함 30분).
- Claude Code 사용(구독이면 한도에서 차감, API 키면 과금. Claude Code가 `total_cost_usd`로 보고한 명목값, 모델 claude-opus-5-5): 구현 프롬프트 1회 0.91~1.06 USD(19턴), 4단계 MCP 대화 1회 0.36 USD(17턴), check_04 추출 1회 0.06~0.07 USD(입력 약 3,360 · 출력 2,300~3,200 토큰). 미니 메모리 자체는 LLM을 부르지 않는다.
- Hindsight LLM: 이번 실습은 Hindsight를 쓰지 않아 없음.
- check_04 결과(리허설 1~3회차): 추출 claim 11·11·12개, 인용 검사 거절 **0개**. 이 대화처럼 짧고 분명한 원문에서는 모델이 인용을 글자 그대로 복사했다(굽은 따옴표까지). 거절이 0이어도 검사가 하는 일은 같다: 4단계처럼 원문에 없는 인용은 저장되지 않는다.

## FAQ (막혔을 때, 위에서부터)

1. **test_03이 갑자기 실패 (`remember() missing …` 또는 recall 결과가 달라짐)** → 새 인자를 필수로 만들었다. `derived_from`·`quote`·`include_history`·`source`는 모두 기본값이 있는 선택 인자로 둔다.
2. **test_04_events_append_only 실패 (DELETE·UPDATE가 성공함)** → 트리거가 없다. `CREATE TRIGGER … BEFORE DELETE ON events`와 `BEFORE UPDATE ON events`에서 `SELECT RAISE(ABORT, '…')`. 서버 코드에서만 막으면 SQLite를 직접 여는 쪽은 못 막는다.
3. **트리거 때문에 내 DB를 비울 수 없음** → 그게 의도다. 실습 DB를 처음부터 다시 쓰려면 파일째 지운다: `make reset`(Hindsight 내장 DB도 지운다). 테스트는 매번 새 임시 DB를 쓰므로 영향이 없다.
4. **test_04_supersede에서 옛 content가 바뀜** → supersede를 `UPDATE claims SET content = …`로 구현했다. 옛 행은 `status`만 바꾸고, 새 내용은 새 행(새 `clm_` id)으로 넣는다.
5. **test_04_history 순서가 틀림** → 모든 시각을 시계 함수 하나에서 UTC `…Z`(같은 자릿수)로 적었는지, 정렬이 `ORDER BY recorded_at ASC, id ASC`인지 본다. `+09:00`이 섞이면 문자열 정렬이 시간 정렬과 어긋난다.
6. **원문에 있는 인용인데 거절됨** → 굽은 따옴표(`“ ”`)·두 칸 공백·줄바꿈 차이다. INTERFACE.md의 정규화(NFC → 따옴표 통일 → 공백 덩어리를 하나로)를 quote와 원문 **양쪽에** 똑같이 적용한다.
7. **기존 `data/mini_memory.db`로 `no such column: status`** → 실습 03에서 만든 DB에는 새 열이 없다. 연결할 때 `PRAGMA table_info(claims)`로 확인하고 빠진 열을 `ALTER TABLE claims ADD COLUMN`으로 더한다(또는 `make reset`).
8. **Claude Code에서 새 도구(record_event·supersede)가 안 보임** → MCP 서버는 Claude Code를 열 때 뜬다. 코드를 고친 뒤 Claude Code를 다시 열거나 `/mcp`에서 다시 연결한다. 그래도 없으면 `make check EP=04`의 test_04_tools부터 본다.
9. **check_04가 'claude -p 오류' / 거절 수가 실행마다 다름** → 추출은 LLM이 하므로 실행마다 달라진다. 측정 단계라 채점하지 않는다. 사용량이 걱정되면 건너뛰어도 다음 편에 영향이 없다.
10. **check_04 추출에 기억이 섞인 것 같음** → 결과 파일 첫 줄의 명령에 `--safe-mode`가 있는지 본다. `--tools ""`만으로는 MCP 도구가 꺼지지 않는다(labs/common.md).
