# 실습 03 — 미니 메모리 시작: 기억의 종류

## 목표

- 내 기억 서버(미니 메모리)의 첫 뼈대를 만든다: 기억 한 조각(**claim**)을 종류(`type`)와 함께 SQLite에 저장하고 찾는 stdio MCP 서버(도구 `remember`·`recall`)와 터미널 명령 `mm`.
- `type`은 CoALA의 네 종류 중 저장하는 세 가지(일화 `episodic`·의미 `semantic`·절차 `procedural`)만 받는다. 작업 기억은 컨텍스트 자체라 저장하지 않는다.
- 같은 가상 대화를 Hindsight에도 넣고, Hindsight가 나눈 네트워크(세계·경험·의견·관찰 = 역할)와 내가 붙인 type(종류)을 나란히 본다. 관찰 단계이고 채점하지 않는다.

이어지는 실습: 실습 01(Hindsight·Claude Code MCP 연결). 미니 메모리 코드는 이번 편이 시작점이고, Hindsight가 없어도 1~5단계는 진행할 수 있다. 데이터는 모두 가상이다: 가상 인물 '하린'과 가상 회사 '벨로랩'의 대화 10턴(`data/conv_03.jsonl`). 실제 인물·회사와 겹치는 이름이 있다면 우연이다. 룬(Luhn) 검사를 통과하는 카드 번호는 넣지 않았다.

**claim** = 기억 한 조각. 다음 편(EP4)에서 원본 기록(이벤트)과 나눈다.

## 진행

1. **틀 준비**: `make start EP=03`. Hindsight를 켜고(6단계용), `labs/03/skeleton`을 `mini_memory/`로 복사한 뒤 `mini_memory/.venv`를 만들고(mcp 2.x), 마지막에 `labs/03/INTERFACE.md`를 출력한다. 틀에는 pyproject.toml(의존성 mcp, 진입점은 아직 없음)과 빈 모듈 세 개(store·server·cli)만 있다.
2. **구현**: 이 폴더에서 Claude Code를 열고(`claude`) `labs/03/PROMPT.md`의 상자 안 글을 붙여 넣는다. Claude가 INTERFACE.md와 테스트를 읽고 `mini_memory/`를 채운 뒤 `make check EP=03`이 통과할 때까지 고친다. `mini_memory/` 쓰기와 `uv run --project mini_memory …`, `make check`는 `.claude/settings.json`에서 미리 허용해 두었다.
3. **테스트**: `make check EP=03` → `8 passed`. 테스트는 고치지 않는다.
4. **Claude Code에서 MCP로 쓰기**: 저장소 폴더에서
   ```bash
   claude mcp add --transport stdio mini-memory -- uv run --project mini_memory mini-memory serve
   ```
   를 실행하고 Claude Code를 다시 연 뒤 `/mcp`에서 `mini-memory · connected`와 도구 2개를 확인한다. 그리고 예를 들어 이렇게 묻는다:
   ```text
   data/conv_03.jsonl은 가상 인물 하린과 AI 에이전트의 대화다. mini-memory 도구로 기억 세 개를 저장해 줘: 일화(episodic) 하나, 의미(semantic) 하나, 절차(procedural) 하나(최소 SKILL.md 형식). 작업 기억과 판단 문장은 저장하지 않는다. 저장한 뒤 recall로 "Python"을 찾아 결과를 보여 줘.
   ```
5. **터미널에서 같은 일**:
   ```bash
   cd mini_memory
   uv run mm remember "하린은 차트로 막대그래프보다 선 그래프를 좋아한다" --type semantic
   uv run mm recall "그래프"
   cd ..
   ```
   MCP로 넣은 기억과 `mm`으로 넣은 기억이 같은 DB(`data/mini_memory.db`)에 있다.
6. **Hindsight와 나란히 보기**: `.venv/bin/python labs/03/show_hindsight.py`. 같은 대화를 뱅크 `lab03`에 retain하고(추출이 끝날 때까지 기다림), 관찰(observation) 통합을 최대 300초 기다린 뒤 네트워크별 표와 내 미니 메모리의 type 표를 출력한다. 같은 문장이 '종류'(내 type)와 '역할'(Hindsight 네트워크)에서 각각 어디에 들어갔는지 한 장으로 적는다.

### 참고: conv_03의 기억 후보 (정답표가 아니라 한 가지 읽기)

| 턴 | 문장 | 종류(내 type) |
|---|---|---|
| t01 | 2월 27일 주간 회의에서 배송 지연 대시보드를 처음 발표했다 | 일화 `episodic` |
| t03 | 데이터 분석에 Python을 주로 쓰고, 선 그래프를 좋아한다 | 의미 `semantic` |
| t04 | (에이전트가) 부산 물류센터 지연율을 다시 계산했다 — 6.1% | 일화 `episodic` |
| t05 | 요일별 그래프가 더 설득력 있었을 것 같다 | 판단: 종류로는 의미에 가깝지만 사실이 아니라 믿음이다(이 구분이 Hindsight의 '역할' 축) |
| t06·t07 | 주간 배송 리포트 만드는 법 (t07은 SKILL.md 형식) | 절차 `procedural` |
| t08 | 이 표에서 3행만 다시 보여 줘 | 작업 기억 — 저장하지 않음 |
| t10 | 3월 11일에 2차 발표가 있다 | 일화 `episodic`(예정된 일) |

## 파일

| 파일 | 내용 |
|---|---|
| `INTERFACE.md` | 계약: type 셋, claims 스키마, 시계(MINI_MEMORY_NOW, UTC Z), remember·recall 반환 객체, MCP 서버·CLI 이름, 절차 기억 형식 |
| `PROMPT.md` | Claude Code에 붙여 넣을 글 |
| `skeleton/` | 미니 메모리 틀. `make start EP=03`이 `mini_memory/`로 복사한다(이미 있으면 건드리지 않음) |
| `tests/` | test_03 8개. 테스트마다 임시 DB로 `uv run mini-memory serve`와 `uv run mm`을 실제로 띄운다 |
| `show_hindsight.py` | conv_03을 뱅크 lab03에 retain하고 네트워크 표 + 내 type 표 |
| `../../data/conv_03.jsonl` | 가상 대화 10턴 (`{"id", "at", "role", "text"}`) |
| `../../data/sample_record_03a.md`, `03b.md` | 영상의 따라 하기 프롬프트 1·2를 시험해 볼 가상 작업 기록 |

## 테스트

| 테스트 | 확인하는 것 |
|---|---|
| test_03_tools | MCP tools/list에 remember·recall이 있고, 시리즈 고정 목록(remember, recall, record_event, supersede, link, forget, promote, approve) 밖 이름이 없다. 개수는 세지 않는다 |
| test_03_type_enum | `opinion`·`working`은 오류(도구 오류와 SQLite CHECK 둘 다), episodic·semantic·procedural(SKILL.md 형식)은 저장 성공. procedural은 회상을 검사하지 않는다(EP13부터 승인된 절차만 회상) |
| test_03_roundtrip | remember('나는 데이터 분석에 Python을 주로 쓴다', 'semantic') 뒤 recall('Python')이 `{"results": [...]}`이고 같은 id(clm_)·content·type, recorded_at·score 칸이 있다 |
| test_03_type_filter | 같은 단어의 episodic·semantic을 넣고 recall(type='episodic')에는 일화만 |
| test_03_clock | `MINI_MEMORY_NOW=2026-03-02T09:00:00+09:00` → `recorded_at = 2026-03-02T00:00:00Z` |
| test_03_persist | 서버를 껐다 켜도 같은 MINI_MEMORY_DB에서 회상된다 |
| test_03_schema | claims 테이블과 id·content·type·recorded_at 열 |
| test_03_cli | `mm remember` → `mm recall` JSON이 MCP recall과 같은 모양이고 그 항목을 담는다 |

## Hindsight 네트워크에 대해 (hindsight-api 1.0.0)

- 네트워크 이름은 기억 목록(`GET /v1/default/banks/lab03/memories/list`)의 `fact_type` 칸이다(recall 응답에서는 `type`). 1.0.0의 값은 `world`·`experience`·`observation` 세 개다.
- 논문의 네 번째 네트워크 **opinion(의견)은 1.0.0에 없다**: 2026-04 마이그레이션 `remove_opinion_fact_type`이 의견 행과 확신도(confidence_score) 칸을 지웠다. 그래서 표의 opinion 줄은 늘 0개이고, 대화의 판단 문장(t05)은 '하린은 …라고 생각했다'는 **세계 사실(world)**로 들어간다. 논문의 의견은 에이전트 자신의 판단이고, t05는 사용자의 판단이라는 점도 다르다.
- `experience`는 에이전트가 한 일(t04 재계산, t07 SKILL.md 초안)이다. Hindsight는 대화의 `AI 에이전트(assistant)` 줄을 보고 가른다.
- `observation`은 retain 뒤 비동기 통합(consolidation)이 사실들을 합쳐 만든다. 실습 02는 이것을 껐고(lab02), 이 실습의 lab03은 켠다.

## 시간과 비용

숫자는 2026-10-19 리허설 2·3회차(Mac mini M4 Pro 48GB, Claude Code 2.1.304, Ollama gemma3:12b, 깨끗한 클론) 기준이다.

- 시간(기계 시간, 사람이 읽는 시간 제외): `make start EP=03` 15~17초(서버 + mini_memory/.venv), 프롬프트(구현 + `make check`) 70~76초, `make check EP=03` 약 6초, MCP로 저장·회상(4단계) 22~24초, `uv run mm` 한 번에 약 3초, `show_hindsight.py` 2.5~3.7분(retain 51~75초 + 관찰 통합 99~145초). 합계 약 6~7분. 시청자 실제 소요는 읽기·붙여 넣기를 더해 약 20분.
- Claude Code 사용(구독이면 한도에서 차감, API 키면 과금. Claude Code가 `total_cost_usd`로 보고한 명목값, 모델 claude-opus-5-5): 구현 프롬프트 1회 0.69~0.77 USD(1회차 0.83), 4단계 MCP 대화 1회 0.28 USD. 미니 메모리 자체는 LLM을 부르지 않는다.
- Hindsight LLM(6단계 retain 한 번): 추출 1회 입력 2,602 · 출력 1,066~1,367 토큰 + 관찰 통합 2회 입력 약 9,950~10,020 · 출력 977~1,447 토큰. Ollama는 로컬이라 0원, API 키 공급자면 이 토큰 수만큼 그 공급자 요금.

## FAQ (막혔을 때, 위에서부터)

1. **MCP 서버가 연결되자마자 끊김 / 테스트가 'stdout에 MCP 메시지가 아닌 줄'로 실패** → 서버 코드의 `print`가 stdout으로 나가 프로토콜을 깼다. 로그는 `sys.stderr`(또는 stderr로 보낸 logging)로만 쓴다.
2. **test_03_type_enum이 CHECK 쪽에서 실패하는데 코드에는 CHECK가 있음** → CHECK 제약은 테이블을 처음 만들 때만 들어간다. 제약 없이 만든 `data/mini_memory.db`가 남아 있으면 `make reset`으로 지우고 다시 만든다(테스트는 매번 임시 DB를 쓰므로, 테스트가 실패하면 코드의 CREATE TABLE을 본다).
3. **test_03_clock 실패 (`2026-03-02T09:00:00+09:00`나 `…+00:00`가 저장됨)** → MINI_MEMORY_NOW를 파싱해 UTC로 바꾼 뒤 `%Y-%m-%dT%H:%M:%SZ`로 적는다. 시간대를 버리거나 현지 시각 그대로 저장하면 안 된다.
4. **`Failed to spawn: mini-memory` / `mm`을 찾지 못함** → 두 진입점(`mm`, `mini-memory`)을 `mini_memory/pyproject.toml`의 `[project.scripts]`에 등록하고, `[build-system]`이 남아 있는지(프로젝트가 패키지로 설치되는지) 확인한다. 저장소 폴더에서는 `uv run --project mini_memory mm …`, `mini_memory/` 안에서는 `uv run mm …`.
5. **`No module named 'mcp.server.fastmcp'`** → mcp 2.x에서는 FastMCP가 `from mcp.server.mcpserver import MCPServer`로 바뀌었다. `mcp<2`로 내리지 말고 2.x API로 쓴다.
6. **Hindsight 쪽 패키지가 사라지거나 mcp 버전이 섞임** → 미니 메모리는 `mini_memory/.venv`, Hindsight는 저장소 `.venv`를 쓴다. 저장소 폴더에서 `uv sync`나 `uv add`를 직접 치지 말고 Makefile 명령과 `uv run --project mini_memory …`만 쓴다.
7. **`claude mcp add` 뒤에도 도구가 안 보임** → 범위 문제다. 저장소 폴더에서 추가하고(기본 범위 local은 그 폴더에만 적용), Claude Code를 다시 열어 `/mcp`로 확인한다.
8. **show_hindsight.py 표가 기대와 다름 (네트워크·문장)** → 추출과 통합은 LLM이 하므로 실행마다 달라진다. 관찰 단계라 채점하지 않는다. 다시 넣어 보려면 `--fresh`.
9. **Hindsight 사실이 영어로 나옴** → 추출 LLM(gemma3:12b)이 실행에 따라 한국어 대화를 영어 사실로 적는다(리허설 3회 중 1회). Hindsight 규칙은 '입력과 같은 언어'지만 지키지 않을 때가 있다. 네트워크 나뉨은 그대로 볼 수 있다. 한국어로 다시 보려면 `--fresh`.
10. **observation이 0개이거나 '300초 안에 안 끝남'** → 통합은 retain 뒤 비동기로 돈다. Ollama에서는 몇 분 걸릴 수 있다. 나중에 `.venv/bin/python labs/03/show_hindsight.py`를 다시 실행하면(retain은 건너뜀) 그때까지 생긴 관찰을 보여 준다.
11. **절차 기억을 자유 문장으로 저장함** → 이 편은 형식을 검사하지 않지만 EP13부터 최소 SKILL.md 형식(머리말 name·description + 번호 단계)이 필수다. 지금부터 그 형식으로 쓴다.
