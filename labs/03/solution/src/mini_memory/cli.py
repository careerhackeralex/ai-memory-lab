"""터미널 명령: `mm remember`, `mm recall` (JSON 출력)과 `mini-memory serve`.

MCP 도구와 같은 store 함수를 부르고 반환 객체를 JSON 하나로 stdout에 쓴다. 오류는 stderr + 종료 코드 1.
"""
import argparse
import json
import sys

from mini_memory import store


def mm(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="mm", description="미니 메모리 터미널 명령")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("remember", help="기억 한 조각(claim)을 저장한다")
    p.add_argument("content")
    p.add_argument("--type", required=True, choices=store.TYPES)

    p = sub.add_parser("recall", help="부분 문자열로 기억을 찾는다")
    p.add_argument("query")
    p.add_argument("--type", choices=store.TYPES)
    p.add_argument("--limit", type=int, default=5)

    args = parser.parse_args(argv)
    try:
        if args.command == "remember":
            out = store.remember(args.content, args.type)
        else:
            out = store.recall(args.query, args.type, args.limit)
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
