"""미니 메모리: AI 기억 설계 실습에서 직접 만드는 작은 기억 저장소.

실습 03에서 시작해 한 편씩 자란다. 계약은 labs/03/INTERFACE.md + labs/04/INTERFACE.md.
- store.py  : SQLite events(원본, 추가 전용)·claims(기억 한 조각), record_event()·remember()·supersede()·recall(), 시계 함수
- server.py : stdio MCP 서버 (도구 remember, recall, record_event, supersede). `mini-memory serve` = `python -m mini_memory.server`
- cli.py    : 터미널 명령 `mm record-event`, `mm remember`, `mm supersede`, `mm recall`과 `mini-memory serve`
"""
