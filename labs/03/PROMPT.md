# 실습 03 프롬프트

아래 상자 안의 글을 그대로 복사해 이 저장소 폴더에서 연 Claude Code에 붙여 넣는다.
붙여 넣기 전에 `make start EP=03`이 `mini_memory/` 틀을 준비하고 INTERFACE.md를 출력했는지 확인한다(README 진행 1).

```text
이 저장소(ai-memory-lab)의 실습 03을 진행해 줘. 목표는 mini_memory/에 미니 메모리를 만드는 것이야. 기억 한 조각(claim)을 종류(type)와 함께 SQLite에 저장하고 찾는 stdio MCP 서버(도구 remember·recall)와, 같은 일을 터미널에서 하는 명령 mm이다.

먼저 읽을 것: labs/03/INTERFACE.md(계약), labs/03/tests/(테스트 8개), mini_memory/의 틀(pyproject.toml, src/mini_memory/), data/conv_03.jsonl의 첫 줄.

지킬 것
1. INTERFACE.md를 그대로 따른다: remember(content, type) → {id, content, type, recorded_at}, recall(query, type?, limit?=5) → {"results": [{id, content, type, recorded_at, score}]}. id는 clm_로 시작한다. 도구와 명령에 사용자·작성자 인자를 두지 않는다.
2. type은 episodic·semantic·procedural만 받는다. 다른 값은 서버 검증과 SQLite CHECK 제약 둘 다에서 오류로 거절한다. 작업 기억은 저장하지 않는다. procedural의 content는 최소 SKILL.md 형식을 권장하고, 이 편에서는 형식을 검사하지 않는다.
3. 저장은 SQLite 파일 하나(환경 변수 MINI_MEMORY_DB, 없으면 INTERFACE.md의 기본 경로)의 claims 테이블(id TEXT PRIMARY KEY, content TEXT NOT NULL, type TEXT CHECK, recorded_at TEXT)이다. recall은 단순 부분 문자열 검색(LIKE)이면 된다.
4. 현재 시각은 시계 함수 하나로만 얻는다. MINI_MEMORY_NOW가 있으면 그 값을 쓰고, UTC로 바꿔 끝에 Z를 붙인 ISO 8601(초 단위까지)로 저장한다.
5. pyproject.toml의 [project.scripts]에 mm과 mini-memory 두 진입점을 등록한다. `mini-memory serve`는 python -m mini_memory.server와 같은 stdio MCP 서버를 띄운다. `mm remember "<내용>" --type <type>`과 `mm recall "<질의>" [--type <type>] [--limit N]`은 MCP 도구와 같은 함수를 부르고 반환 객체를 JSON으로 출력한다.
6. MCP 서버는 stdout에 프로토콜 메시지만 쓰고 로그는 stderr로 보낸다. 의존성은 틀에 있는 mcp(2.x)와 표준 라이브러리만 쓴다. mcp 2에서는 FastMCP가 MCPServer(mcp.server.mcpserver)로 바뀌었으니 mini_memory/.venv에 설치된 패키지를 확인하고 쓴다.
7. labs/03/tests의 파일은 고치지 않는다. 실패하면 구현을 고친다. mini_memory/ 밖의 파일은 고치지 않고 hindsight/.env는 열지 않는다. 직접 실행할 때는 저장소 폴더에서 uv run --project mini_memory … 형태로, 명령을 한 줄에 하나씩 부른다(미리 허용한 명령은 하나 단위로 맞춰 두었다). 설치된 패키지 소스는 파일 읽기·검색 도구로 본다.
8. mini_memory/README.md를 만들고 claim의 뜻을 한 줄로 적는다: 기억 한 조각, 다음 편에서 원본 기록(이벤트)과 나눈다. 실행 명령도 적는다.

순서
1. mini_memory/src/mini_memory/의 store.py·server.py·cli.py를 채우고 pyproject.toml에 진입점을 등록한다.
2. make check EP=03 을 실행해 테스트 8개가 모두 통과할 때까지 구현을 고친다.
3. 마지막에 내가 칠 명령을 코드 블록으로 출력해 줘:
   claude mcp add --transport stdio mini-memory -- uv run --project mini_memory mini-memory serve
   cd mini_memory
   uv run mm remember "나는 데이터 분석에 Python을 주로 쓴다" --type semantic
   uv run mm recall "Python"
```
