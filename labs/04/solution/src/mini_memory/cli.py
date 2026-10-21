"""터미널 명령: `mm remember`, `mm recall`(실습 03) + `mm record-event`, `mm supersede`(실습 04)와 `mini-memory serve`.

MCP 도구와 같은 store 함수를 부르고 반환 객체를 JSON 하나로 stdout에 쓴다. 오류는 stderr + 종료 코드 1.
"""
import argparse
import json
import sys

from mini_memory import store


def mm(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="mm", description="미니 메모리 터미널 명령")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("record-event", help="원본 기록(이벤트)을 추가한다 (고치거나 지우지 않는다)")
    p.add_argument("content")
    p.add_argument("--source")

    p = sub.add_parser("remember", help="기억 한 조각(claim)을 저장한다")
    p.add_argument("content")
    p.add_argument("--type", required=True, choices=store.TYPES)
    p.add_argument("--derived-from", nargs="+", metavar="ID", help="근거 id (evt_… 또는 clm_…)")
    p.add_argument("--quote", help="원문 인용 (derived_from 이벤트 원문에 있어야 저장)")

    p = sub.add_parser("supersede", help="옛 claim을 지우지 않고 새 claim으로 대체한다")
    p.add_argument("old_id")
    p.add_argument("content")
    p.add_argument("--type", choices=store.TYPES, help="생략하면 옛 claim의 type")
    p.add_argument("--derived-from", nargs="+", metavar="ID")
    p.add_argument("--quote")

    p = sub.add_parser("recall", help="부분 문자열로 기억을 찾는다")
    p.add_argument("query")
    p.add_argument("--type", choices=store.TYPES)
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--include-history", action="store_true", help="대체된 옛 claim까지 시간 순으로")

    args = parser.parse_args(argv)
    try:
        if args.command == "record-event":
            out = store.record_event(args.content, args.source)
        elif args.command == "remember":
            out = store.remember(args.content, args.type, args.derived_from, args.quote)
        elif args.command == "supersede":
            out = store.supersede(args.old_id, args.content, args.type, args.derived_from, args.quote)
        else:
            out = store.recall(args.query, args.type, args.limit, args.include_history)
    except ValueError as e:
        print(f"mm: {e}", file=sys.stderr)
        sys.exit(1)
    print(json.dumps(out, ensure_ascii=False, indent=2))


def mini_memory(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="mini-memory", description="미니 메모리")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("serve", help="stdio MCP 서버를 띄운다 (python -m mini_memory.server와 같다)")
    parser.parse_args(argv)

    from mini_memory import server
    server.main()
