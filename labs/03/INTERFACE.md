# 실습 03 계약 (INTERFACE)

미니 메모리(`mini_memory/`)와 test_03이 함께 지키는 약속이다. 뒤 편(EP4~)은 반환 객체에 칸을, 서버에 도구를, `mm`에 하위 명령을 **더하기만** 하고 이름을 바꾸거나 지우지 않는다. 테스트는 필요한 칸만 확인한다.

## 폴더와 실행 환경

| 항목 | 값 |
|---|---|
| 프로젝트 | `mini_memory/` (uv 하위 프로젝트, `make start EP=03`이 `labs/03/skeleton`을 복사). 패키지 코드는 `mini_memory/src/mini_memory/` |
| 가상환경 | `mini_memory/.venv` — Hindsight용 저장소 `.venv`와 따로 둔다 |
| 의존성 | `mcp` 2.x(틀의 pyproject에 있음) + 표준 라이브러리(sqlite3 등). mcp 2에서는 FastMCP가 `mcp.server.mcpserver.MCPServer`로 바뀌었다 |
| 진입점 | `pyproject.toml`의 `[project.scripts]`에 `mm`, `mini-memory` 두 개 (Claude가 등록) |
| 실행 | 저장소 폴더에서 `uv run --project mini_memory mm …`, 또는 `cd mini_memory` 뒤 `uv run mm …` |

## 기억의 종류 (`type`)

| type | 뜻 | 예 (data/conv_03.jsonl) |
|---|---|---|
| `episodic` | 일화: 언제 무슨 일이 있었나 | 2월 27일 주간 회의에서 배송 지연 대시보드를 발표했다 |
| `semantic` | 의미: 사실·선호·지식 | 데이터 분석에 Python을 주로 쓴다 |
| `procedural` | 절차: 반복되는 작업 방법 (최소 SKILL.md 형식 권장) | 주간 배송 리포트 만드는 법 |

작업 기억(working memory)은 컨텍스트 자체라 저장하지 않는다. 세 값 밖(`working`, `opinion` 등)은 오류다: 서버가 먼저 거절하고, SQLite CHECK 제약도 거절한다.

## 저장 (SQLite)

- 파일: 환경 변수 `MINI_MEMORY_DB`. 없으면 저장소의 `data/mini_memory.db` (패키지 파일 위치에서 계산: `mini_memory/src/mini_memory/` → 세 단계 위가 저장소. `data/`는 git에 들어가지 않고 `make reset`이 지운다).
- 최소 스키마 (뒤 편이 열·테이블을 더한다):

```sql
CREATE TABLE IF NOT EXISTS claims (
  id          TEXT PRIMARY KEY,
  content     TEXT NOT NULL,
  type        TEXT NOT NULL CHECK (type IN ('episodic', 'semantic', 'procedural')),
  recorded_at TEXT NOT NULL
);
```

- CHECK 제약은 테이블을 **처음 만들 때만** 들어간다. 제약 없이 만든 DB가 남아 있으면 `make reset`으로 지우고 다시 만든다.

## 시계

- 현재 시각은 시계 함수 하나로만 얻는다. 환경 변수 `MINI_MEMORY_NOW`(ISO 8601)가 있으면 그 시각을 쓴다(시간대가 없는 값은 UTC로 본다).
- 저장할 때는 UTC로 바꿔 `YYYY-MM-DDTHH:MM:SSZ`(초 단위까지, 끝에 Z)로 적는다.
  예: `MINI_MEMORY_NOW=2026-03-02T09:00:00+09:00` → `recorded_at = "2026-03-02T00:00:00Z"`.
- 이 규칙은 뒤 편(EP4 이력 정렬, EP7 유효기간)에서도 그대로 쓴다.

## 함수 (MCP 도구와 CLI가 같은 함수를 부른다)

```
remember(content: str, type: str)
  → {"id": "clm_…", "content": …, "type": …, "recorded_at": "…Z"}

recall(query: str, type: str | None = None, limit: int = 5)
  → {"results": [{"id": …, "content": …, "type": …, "recorded_at": …, "score": …}, …]}
```

- `id`: 접두어 `clm_` + 무작위 16진수. (EP4에서 생길 원본 기록 '이벤트'는 `evt_…`.)
- `recall`: `content LIKE '%query%'`(단순 부분 문자열). `type`을 주면 그 종류만. 최근 `recorded_at` 먼저, 최대 `limit`개. `score`는 이 편에서 고정값(예: 1.0)이면 된다(EP5부터 결합 점수). 결과가 없으면 `{"results": []}`.
- 도구와 명령에 사용자·작성자 인자를 두지 않는다(신원은 뒤 편에서 서버 환경 변수로 정한다). CLI로 들어온 호출의 기본 ACTOR는 `human`이다(칸은 뒤 편에서 붙는다).

## MCP 서버 (stdio)

- `uv run mini-memory serve` = `python -m mini_memory.server`. 도구 이름 `remember`, `recall`.
- 시리즈 전체의 도구 이름 고정 목록: `remember, recall, record_event, supersede, link, forget, promote, approve`. 이 밖의 이름은 쓰지 않는다.
- **stdout에는 MCP 메시지만** 쓴다. 로그·print는 stderr로.
- type 오류는 도구 오류(isError)로 돌려준다.
- Claude Code 연결 (저장소 폴더에서): `claude mcp add --transport stdio mini-memory -- uv run --project mini_memory mini-memory serve` → `/mcp`로 확인.

## CLI `mm`

```
uv run mm remember "<내용>" --type <episodic|semantic|procedural>   → remember 반환 객체 JSON
uv run mm recall "<질의>" [--type <type>] [--limit N]               → {"results": [...]} JSON
```

- stdout 전체가 JSON 하나(한글은 그대로 출력). 오류는 stderr + 종료 코드 ≠ 0.
- 뒤 편이 하위 명령을 더한다: `load`(EP6), `forget`(EP8), `ingest`(EP9), `promote`·`approve`(EP10).

## 절차 기억의 형식 (권장, 검사는 EP13부터)

```
---
name: weekly-delivery-report
description: 매주 월요일 아침 주간 배송 지연 리포트를 만들 때 쓴다.
---
1. 웨어하우스에서 지난주 배송 데이터를 내려받는다.
2. 반품 건을 뺀다.
```

맨 위 `---`, `name`(영문 소문자·하이픈)과 `description`(언제 쓰는지 한 문장) 두 줄, 다시 `---`, 그 아래 번호 붙인 단계.

## 테스트 (`labs/03/tests`, 고치지 않는다)

`make check EP=03`. 테스트마다 임시 DB(`MINI_MEMORY_DB`)로 `uv run mini-memory serve`와 `uv run mm`을 실제로 띄운다.

| 테스트 | 확인하는 것 |
|---|---|
| test_03_tools | tools/list에 remember·recall이 있고, 고정 목록 밖 이름이 없다 |
| test_03_type_enum | `opinion`·`working`은 오류(도구와 CHECK 둘 다), episodic·semantic·procedural(SKILL.md 형식)은 저장 성공 |
| test_03_roundtrip | remember 뒤 recall('Python')의 `{"results": [...]}`에 같은 id(clm_)·content·type과 recorded_at·score |
| test_03_type_filter | recall(query, type='episodic')에는 일화 기억만 |
| test_03_clock | `MINI_MEMORY_NOW=2026-03-02T09:00:00+09:00` → `2026-03-02T00:00:00Z` |
| test_03_persist | 서버를 껐다 켜도 같은 DB에서 회상된다 |
| test_03_schema | claims 테이블과 id·content·type·recorded_at 열 |
| test_03_cli | `mm remember` → `mm recall` JSON이 MCP recall과 같은 모양이고 그 항목을 담는다 |

용어: **claim** = 기억 한 조각. 다음 편(EP4)에서 원본 기록(이벤트)과 나눈다.
