# 실습 04 계약 (INTERFACE)

실습 03 계약(`labs/03/INTERFACE.md`)은 그대로 두고, 이 편은 **더하기만** 한다. 원본 기록(이벤트)을 지우지 않고 쌓는 `events` 테이블, 기억 한 조각(claim)의 근거(`derived_from`)와 원문 인용(`quote`), 그리고 사실이 바뀌었을 때 옛 claim을 지우지 않고 새 claim으로 대체하는 `supersede`다. 테스트는 필요한 칸만 확인한다.

용어: **event** = 원본 기록(대화 한 줄, 문서 한 단락). **claim** = 그 원본에서 뽑은 기억 한 조각. 원본은 지키고, 사실은 claim에서 고친다.

## 함수 (MCP 도구와 CLI가 같은 함수를 부른다)

```
record_event(content: str, source: str | None = None)
  → {"id": "evt_…", "content": …, "source": …, "recorded_at": "…Z"}

remember(content: str, type: str, derived_from: list[str] | None = None, quote: str | None = None)
  → {"id": "clm_…", "content": …, "type": …, "recorded_at": "…Z", "status": "active", "supersedes": null, "derived_from": [...]}

supersede(old_id: str, content: str, type: str | None = None, derived_from: list[str] | None = None, quote: str | None = None)
  → {"id": "clm_…(새 claim)", "supersedes": "<old_id>", "recorded_at": "…Z", "content": …, "type": …, "status": "active", "derived_from": [...]}

recall(query: str, type: str | None = None, limit: int = 5, include_history: bool = False)
  → {"results": [{"id", "content", "type", "recorded_at", "score", "status", "supersedes", "derived_from"}, …]}
```

- **앞 편 호환**: 새 인자는 모두 기본값이 있는 선택 인자다. `remember(content, type)`만으로 실습 03과 똑같이 동작한다(test_04_backcompat = test_03 전체). 반환 객체에는 칸을 더하기만 하고, 뒤 편도 칸을 더할 수 있다.
- **id 접두어**: 이벤트는 `evt_` + 무작위 16진수, claim은 실습 03대로 `clm_` + 무작위 16진수.
- **derived_from**: 근거 id의 목록. 이벤트 id(`evt_…`) 또는 claim id(`clm_…`)만 받는다(claim을 근거로 삼는 쓰임은 EP8·EP10). 접두어가 없거나, 없는 id면 오류. 생략하면 `[]`. recall 항목과 반환 객체에는 목록(JSON 배열)으로 담는다.
- **source**: 원본의 출처 표시(예: `conv_04.jsonl#t05`). 도구와 명령에 사용자·작성자 인자는 두지 않는다(실습 03과 같음).
- **status**: 이 편에서는 `active`·`superseded` 두 값. 새 claim은 `active`. 뒤 편이 `forgotten`·`quarantined`(EP8), `proposed`·`rejected`(EP10)를 더한다.
- **recall 기본값**: `status = 'active'`만, 실습 03대로 최근 `recorded_at` 먼저, 최대 `limit`개. 그래서 뒤 편의 새 status 값은 이 편의 테스트를 바꾸지 않고도 기본 결과에서 빠진다.
- **recall(include_history=true)**: status와 상관없이(대체된 옛 claim 포함) `query`·`type`에 맞는 claim을 `(recorded_at, id)` **오름차순**으로 준다. 같은 시각이면 id 오름차순. `limit`은 그대로 적용한다: 최근 것부터 `limit`개를 고른 뒤 오름차순으로 돌려준다.
- 오류(없는 id, 이미 대체된 claim, 인용 검사 실패, 잘못된 type·derived_from)는 MCP에서는 도구 오류(isError)로, CLI에서는 stderr + 종료 코드 ≠ 0으로 돌려준다. 오류이면 아무것도 저장하지 않는다.

### supersede

1. `old_id`가 없으면 오류.
2. 옛 claim의 status가 `active`가 아니면(이미 대체됨) 오류. **두 번 대체하지 않는다**: 바뀐 사실을 또 고치려면 현재 claim(새 id)을 대체한다.
3. 새 claim을 만든다: `supersedes = old_id`, `type`을 생략하면 옛 claim의 type, `recorded_at`은 시계 함수의 현재 시각.
4. 옛 claim은 **지우지 않고 content도 바꾸지 않는다**. `status`만 `superseded`로 바꾼다.
5. 3과 4는 한 트랜잭션에서 한다(하나가 실패하면 둘 다 없던 일).

### 인용 검사 (quote)

`remember`·`supersede`에 `quote`(원문 인용)를 주면, `derived_from`에 든 **이벤트(`evt_…`) 원문 가운데 하나**에 그 글이 실제로 있어야 저장한다. 없으면 저장하지 않고 이유를 담은 오류를 돌려준다. claim id(`clm_…`)는 인용 검사에 쓰지 않는다.

비교 전에 양쪽(quote와 이벤트 원문)을 똑같이 정규화하고, 정규화한 quote가 정규화한 원문의 **부분 문자열**이면 통과다.

1. 유니코드 NFC로 맞춘다(macOS에서 복사한 한글이 자모로 나뉘어 있을 때).
2. 따옴표를 통일한다: `“ ” „ ‟ ″ ＂` → `"`, `‘ ’ ‚ ‛ ′ ＇` → `'`.
3. 공백 덩어리(띄어쓰기·탭·줄바꿈·전각 공백 등 `\s+`)를 공백 하나로 바꾸고 앞뒤 공백을 지운다.

대소문자·문장부호·숫자 표기(`9,900`과 `9900`)는 바꾸지 않는다. quote가 비어 있거나, quote가 있는데 `derived_from`에 이벤트 id가 없으면 오류다.

예: 원문 `예산 문서에는 아직 “월 9,900원”으로  적혀 있으니까` ← quote `아직 "월 9,900원"으로 적혀 있으니까`는 통과(곧은 따옴표, 공백 하나), quote `이미 12,900원으로 고쳤어`는 거절.

## 저장 (SQLite)

실습 03의 `claims`에 열을 더하고 `events` 테이블을 새로 만든다. 최소 스키마(뒤 편이 열·테이블을 더한다):

```sql
CREATE TABLE IF NOT EXISTS events (
  id          TEXT PRIMARY KEY,   -- evt_…
  content     TEXT,               -- 원문. 서버는 빈 글을 받지 않는다. NOT NULL은 붙이지 않는다(EP8 forget이 NULL로 비울 수 있음)
  source      TEXT,
  recorded_at TEXT NOT NULL       -- UTC, 끝에 Z
);
-- claims (실습 03) + 이 편의 열
--   status       TEXT NOT NULL DEFAULT 'active'   -- active | superseded (값 검사는 서버가 한다. 뒤 편이 값을 더하므로 CHECK는 두지 않는다)
--   supersedes   TEXT                             -- 이 claim이 대체한 옛 claim id, 없으면 NULL
--   derived_from TEXT NOT NULL DEFAULT '[]'       -- 근거 id 목록(JSON 배열 문자열)
--   (권장) quote TEXT                             -- 검사를 통과한 원문 인용
```

- **기존 DB 이어 쓰기**: 실습 03에서 만든 `data/mini_memory.db`에는 새 열이 없다. 연결할 때 `PRAGMA table_info(claims)`로 확인하고 빠진 열만 `ALTER TABLE claims ADD COLUMN …`으로 더한다. 실습 03 claim들은 `status='active'`, `derived_from='[]'`가 된다.
- **events는 추가만**: 서버 코드에 지우거나 고치는 기능을 만들지 않고, SQLite 트리거로도 막는다. 이 편에는 허용되는 UPDATE가 없다.

```sql
CREATE TRIGGER IF NOT EXISTS events_no_delete BEFORE DELETE ON events
BEGIN SELECT RAISE(ABORT, 'events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS events_no_update BEFORE UPDATE ON events
BEGIN SELECT RAISE(ABORT, 'events is append-only'); END;
```

- 트리거 오류는 Python에서 `sqlite3.IntegrityError`(= `sqlite3.DatabaseError` 계열)로 올라온다. **오류 문구는 SQLite 버전마다 다르므로**, 코드와 테스트는 예외 종류로만 판단한다.

## 시계

실습 03 규칙 그대로: 모든 시각은 시계 함수 하나에서 얻고, `MINI_MEMORY_NOW`(ISO 8601, 시간대 없으면 UTC)를 따르며, UTC `YYYY-MM-DDTHH:MM:SSZ`로 저장한다. `events.recorded_at`도 같은 함수로 적는다.

- 모든 시각이 같은 자릿수의 UTC 문자열이라 **문자열 정렬이 곧 시간 정렬**이다. EP3에서 생긴 `claims.recorded_at`이 이제 대체 이력의 순서를 정한다.
- 예: `MINI_MEMORY_NOW=2026-03-02T09:00:00+09:00`에 저장 → `2026-03-02T00:00:00Z`, `MINI_MEMORY_NOW=2026-04-01T10:30:00+09:00`에 supersede → 새 claim `2026-04-01T01:30:00Z`.

## MCP 서버 (stdio)

- 도구 네 개: `remember`, `recall`(실습 03) + `record_event`, `supersede`. 시리즈 고정 목록(`remember, recall, record_event, supersede, link, forget, promote, approve`) 밖의 이름은 쓰지 않는다.
- stdout에는 MCP 메시지만, 로그는 stderr로(실습 03과 같음).
- 이미 `claude mcp add`로 연결했다면 다시 추가할 필요 없다. 코드를 고친 뒤 Claude Code를 다시 열면(또는 `/mcp`에서 다시 연결) 새 도구가 보인다.

## CLI `mm`

```
uv run mm record-event "<원문>" [--source <출처>]                                    → record_event 반환 객체 JSON
uv run mm remember "<내용>" --type <type> [--derived-from ID ...] [--quote "<인용>"]   → remember 반환 객체 JSON
uv run mm supersede <old_id> "<새 내용>" [--type <type>] [--derived-from ID ...] [--quote "<인용>"]
uv run mm recall "<질의>" [--type <type>] [--limit N] [--include-history]           → {"results": [...]} JSON
```

- stdout 전체가 JSON 하나(한글 그대로), 오류는 stderr + 종료 코드 ≠ 0(실습 03과 같음).

## 테스트 (`labs/04/tests`, 고치지 않는다)

`make check EP=04` = test_03 8개 + test_04 8개. 테스트마다 임시 DB(`MINI_MEMORY_DB`)를 새로 만드므로 트리거가 테스트 정리를 막지 않는다. 시각은 `MINI_MEMORY_NOW`로 t1 = `2026-03-02T09:00:00+09:00`, t2 = `2026-04-01T10:30:00+09:00` 두 개를 바꿔 가며 서버를 띄운다. 테스트 데이터는 episodic·semantic만 쓴다.

| 테스트 | 확인하는 것 |
|---|---|
| test_04_tools | tools/list에 remember·recall·record_event·supersede가 모두 있고, 고정 목록 밖 이름이 없다(개수는 세지 않음) |
| test_04_events_append_only | events에 직접 DELETE(한 행·전체), content를 바꾸는 UPDATE(길이가 다른 글, 같은 글자 수의 다른 글)가 모두 `sqlite3.DatabaseError` 계열 예외이고, 행 수와 내용이 그대로 |
| test_04_supersede | t1 '벨로랩의 Acme 팀 플랜은 월 9,900원이다'(semantic) → t2에 type 없이 12,900원으로 supersede: 기본 recall엔 새 claim만, 옛 claim은 superseded·content 그대로, 새 claim.supersedes = 옛 id, type = semantic, recorded_at = t2 |
| test_04_history | include_history=true 결과가 (recorded_at, id) 오름차순: t1 claim이 먼저, 같은 시각(t2) claim끼리는 id 순. 기본 recall엔 대체된 claim이 없다 |
| test_04_derived_from | record_event의 id가 `evt_`로 시작하고 recorded_at이 UTC Z, 그 id를 derived_from으로 준 claim의 recall 항목 derived_from = [그 id] |
| test_04_quote_must_exist | 원문에 있는 quote(따옴표·공백만 다름)는 저장, 원문에 없는 quote는 도구 오류이고 claims 수가 늘지 않음 |
| test_04_no_double_supersede | 이미 대체된 claim을 다시 supersede하면 오류, claim이 새로 생기지 않고 현재 claim은 active 그대로 |
| test_04_backcompat | test_03 전체(8개)가 그대로 통과 |

## 뒤 편을 위한 약속 (이 편에서 구현하지 않는다)

- **events 행은 어느 편에서도 지우지 않는다.** 직접 DELETE와 content를 임의로 바꾸는 UPDATE는 이후 모든 편에서 막힌다(test_04_events_append_only는 뒤 편에서도 유지).
- 유일하게 허용되는 변경은 **EP8의 forget**이다: 잊을 claim의 `source_span` 구간만 같은 글자 수의 `█`로 가리고 `redacted_spans`에 그 구간을 더하며 `redacted_at`을 적고, 그 이벤트에서 나온 claim이 모두 잊힐 때만 content를 NULL로 비운다. 가림이 글자 수를 바꾸지 않으므로 EP5의 글자 위치(`source_span`)도 그대로 유효하다.
- EP8부터 이벤트 가드(트리거)는 `UPDATE OF content`를 다음 둘 중 하나일 때만 통과시킨다:
  ① `length(NEW.content) = length(OLD.content)`(글자 수) AND `NEW.redacted_at IS NOT NULL` AND `json_array_length(NEW.redacted_spans) > json_array_length(COALESCE(OLD.redacted_spans,'[]'))`
  ② `NEW.content IS NULL AND NEW.redacted_at IS NOT NULL`
  조건 계산이 NULL이면 통과시키지 않는다(예: `WHEN NOT (COALESCE(①, 0) OR COALESCE(②, 0))`일 때 RAISE). ②의 '그 이벤트의 claim이 모두 forgotten' 조건은 트리거가 아니라 forget()이 같은 트랜잭션에서 검사한다. EP8은 이 편의 `events_no_update` 트리거를 이 가드로 바꾼다.
- status 값: 뒤 편이 `forgotten`·`quarantined`(EP8), `proposed`·`rejected`(EP10)를 더한다. recall 기본은 계속 `active`만.
- 시각 규칙은 EP7(유효기간)에서도 그대로 쓴다.
