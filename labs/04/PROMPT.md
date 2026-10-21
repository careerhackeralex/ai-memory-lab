# 실습 04 프롬프트

아래 상자 안의 글을 그대로 복사해 이 저장소 폴더에서 연 Claude Code에 붙여 넣는다.
붙여 넣기 전에 `make start EP=04`가 test_03을 확인하고(통과하지 못하면 내 코드를 `backup/`에 옮기고 `labs/03/solution`을 복사) INTERFACE.md를 출력했는지 확인한다(README 진행 1).

```text
이 저장소(ai-memory-lab)의 실습 04를 진행해 줘. 목표는 실습 03에서 만든 mini_memory/에 '원본은 지키고 사실은 고치는' 기능을 더하는 것이야. 원본 기록(이벤트)을 지우지 않고 쌓는 events 테이블과 MCP 도구 record_event, claim의 근거(derived_from)와 원문 인용(quote) 검사, 사실이 바뀌면 옛 claim을 지우지 않고 대체하는 supersede, 이력까지 보는 recall(include_history)이다.

먼저 읽을 것: labs/04/INTERFACE.md(이 편 계약), labs/03/INTERFACE.md(앞 편 계약), labs/04/tests/(테스트 8개), mini_memory/의 지금 코드(pyproject.toml, src/mini_memory/), data/conv_04.jsonl의 첫 줄.

지킬 것
1. 앞 편을 깨지 않는다: 도구·명령의 이름과 인자는 그대로 두고, 새 인자는 모두 기본값이 있는 선택 인자로 더한다. remember(content, type)만으로 실습 03과 똑같이 동작해야 하고, recall은 {"results": [...]} 모양을 유지한 채 항목에 status·supersedes·derived_from을 더한다.
2. events(id, content, source, recorded_at)는 추가만 한다. 지우거나 고치는 기능을 만들지 않고, SQLite 트리거로도 DELETE와 UPDATE를 거부한다. 트리거 오류는 문구가 아니라 예외 종류(sqlite3.DatabaseError 계열)로만 판단한다. 이벤트 id는 evt_, claim id는 clm_로 시작한다.
3. claims에 status(active|superseded), supersedes, derived_from 열을 더한다. 실습 03에서 만든 DB가 이미 있어도 동작하도록, 빠진 열은 연결할 때 ALTER TABLE로 더한다.
4. supersede(old_id, content, type?, derived_from?, quote?)는 새 claim을 만들고(supersedes = 옛 id, type을 생략하면 옛 claim의 type) 옛 claim은 지우지도 content를 바꾸지도 않고 status만 superseded로 바꾼다. 한 트랜잭션으로 하고, 이미 대체된 claim을 다시 대체하면 오류다.
5. recall은 기본으로 active만 돌려준다. include_history=true면 대체된 claim까지 (recorded_at, id) 오름차순으로 준다.
6. quote가 있으면 INTERFACE.md의 정규화(NFC, 따옴표 통일, 연속 공백 하나로) 뒤 derived_from에 든 이벤트 원문 가운데 하나에 부분 문자열로 있어야 저장하고, 아니면 저장하지 않고 이유를 도구 오류로 돌려준다.
7. 모든 시각(events.recorded_at 포함)은 실습 03의 시계 함수 하나에서 얻는다(MINI_MEMORY_NOW, UTC, 끝에 Z).
8. mm에 record-event와 supersede 하위 명령, remember의 --derived-from·--quote, recall의 --include-history를 더한다. MCP 도구와 같은 함수를 부르고 JSON 하나를 출력한다.
9. labs/03/tests와 labs/04/tests의 파일은 고치지 않는다. 실패하면 구현을 고친다. mini_memory/ 밖의 파일은 고치지 않고 hindsight/.env는 열지 않는다. 직접 실행할 때는 저장소 폴더에서 uv run --project mini_memory mm … 형태로, 명령을 한 줄에 하나씩 부른다(미리 허용한 명령은 하나 단위로 맞춰 두었다). 셸 반복문·변수와 python -c 같은 임시 확인 스크립트는 쓰지 않고, 동작 확인은 make check EP=04와 mm 명령으로 한다. 파일과 설치된 패키지 소스는 파일 읽기·검색 도구로 본다.
10. mini_memory/README.md에 event와 claim의 뜻을 한 줄씩 더하고(event = 원본 기록, 지우지 않는다 / claim = 원본에서 뽑은 기억 한 조각, 고칠 때는 대체한다) 새 명령을 적는다.

순서
1. mini_memory/src/mini_memory/의 store.py·server.py·cli.py를 고친다.
2. make check EP=04 를 실행해 test_03 8개와 test_04 8개가 모두 통과할 때까지 구현을 고친다.
3. 마지막에 내가 칠 명령을 코드 블록으로 출력해 줘(evt_…·clm_…는 앞 명령의 출력에서 복사):
   cd mini_memory
   uv run mm record-event "벨로랩 데이터팀은 협업 도구로 Acme를 써. 팀 플랜이고 요금은 월 9,900원이야." --source conv_04.jsonl#t01
   uv run mm remember "벨로랩의 Acme 팀 플랜은 월 9,900원이다" --type semantic --derived-from evt_… --quote "월 9,900원"
   uv run mm supersede clm_… "벨로랩의 Acme 팀 플랜은 월 12,900원이다"
   uv run mm recall "Acme 팀 플랜" --include-history
```
