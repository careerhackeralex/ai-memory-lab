# mini_memory (실습 04 참고 구현)

> `labs/04/solution`: 실습 03 위에 원본 기록(이벤트)과 대체 이력을 더한 참고 구현이다. 내 구현이 막혔을 때 비교용으로 본다. 계약은 [`labs/03/INTERFACE.md`](../../03/INTERFACE.md) + [`labs/04/INTERFACE.md`](../INTERFACE.md).

- **event** = 원본 기록(대화 한 줄, 문서 한 단락). `events` 테이블에 추가만 한다. SQLite 트리거가 DELETE와 UPDATE를 거부한다. id는 `evt_…`.
- **claim** = 기억 한 조각. `derived_from`으로 근거(이벤트·claim id)를 가리키고, `quote`(원문 인용)는 근거 이벤트 원문에 있어야 저장된다. id는 `clm_…`.
- 사실이 바뀌면 `supersede`: 새 claim을 만들고 옛 claim은 지우지 않고 `status=superseded`로 둔다. `recall`은 기본으로 현재 사실(active)만, `include_history=true`면 이력까지 시간 순으로 준다.

## 실행

저장소 폴더에서:

```bash
uv run --project mini_memory mini-memory serve        # MCP 서버 (도구 remember·recall·record_event·supersede)

uv run --project mini_memory mm record-event "Acme 팀 플랜은 월 9,900원이야." --source conv_04.jsonl#t01
uv run --project mini_memory mm remember "벨로랩의 Acme 팀 플랜은 월 9,900원이다" --type semantic --derived-from evt_… --quote "월 9,900원"
uv run --project mini_memory mm supersede clm_… "벨로랩의 Acme 팀 플랜은 월 12,900원이다"
uv run --project mini_memory mm recall "Acme" --include-history

make check EP=04                                      # test_03 + test_04
```
