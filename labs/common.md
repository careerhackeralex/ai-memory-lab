# 공통: `claude -p` 측정의 격리 설정

`claude -p`(대화 없이 한 번 실행)로 무언가를 잴 때는(check_02·04·09·12) 프로젝트의 MCP 서버, CLAUDE.md, 자동 기억이 결과에 섞이지 않게 아래 설정을 쓴다. 각 편의 측정 결과 파일에는 실제로 쓴 명령줄을 함께 적는다.

## 기본값 (구독·API 키 모두)

```bash
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
claude -p "<질문>" \
  --safe-mode \
  --tools "" \
  --no-session-persistence \
  --output-format json < /dev/null
```

| 설정 | 하는 일 (Claude Code 2.1.300 `claude --help` 기준) |
|---|---|
| `--safe-mode` | CLAUDE.md, 스킬, 플러그인, 훅, MCP 서버, 사용자 명령 등 모든 사용자 설정을 끄고 시작한다. 인증·모델 선택·권한은 그대로. `CLAUDE_CODE_SAFE_MODE=1`을 켠다 |
| `--tools ""` | 내장 도구를 모두 끈다 (`"default"`는 전부 켬) |
| `--no-session-persistence` | 세션을 디스크에 저장하지 않는다 (`--print`에서만) |
| `--output-format json` | 결과 하나를 JSON으로 (`total_cost_usd`, `usage` 포함) |
| `< /dev/null` | 표준 입력을 닫는다. 없으면 파이프·스크립트 안에서 'no stdin data received in 3s' 경고와 함께 3초를 기다린다 |
| `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1` | Claude Code 자동 기억(auto memory)을 끈다. `--safe-mode`는 자동 기억을 끄지 않으므로 환경 변수로 따로 끈다 |

## API 키 사용자 대안

`--bare`는 훅·LSP·플러그인 동기화·자동 기억·CLAUDE.md 자동 탐색을 모두 건너뛰는 최소 모드다. 다만 인증을 `ANTHROPIC_API_KEY`(또는 `--settings`의 apiKeyHelper)로만 하고 OAuth(구독 로그인)와 키체인을 읽지 않는다. 그래서 기본값으로 쓰지 않고, API 키 사용자만 쓴다.

```bash
claude -p "<질문>" --bare --tools "" --no-session-persistence --output-format json
```

## 특정 MCP 서버만 켜야 할 때 (check_09)

```bash
CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 \
claude -p "<질문>" --strict-mcp-config --mcp-config <미니 메모리만 적은 JSON> \
  --no-session-persistence --output-format json
```

`--strict-mcp-config`는 `--mcp-config`에 적은 서버만 쓰고 나머지 MCP 설정을 모두 무시한다.

## 대화형 실습 세션 (EP1 세션 A/B)

대화형 세션은 격리하지 않는다. 저장소의 `.claude/settings.json`(`autoMemoryEnabled: false`)과 CLAUDE.md의 recall 안내 한 줄이 적용된 상태에서, `claude mcp add`로 붙인 Hindsight MCP만 기억 역할을 한다. 확실히 하려면 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude`로 연다.

리허설 확인(2026-10-15, Claude Code 2.1.300): 위 기본값으로 `claude -p "한 단어로: 2+2는?"`가 오류 없이 답했고(`is_error: false`), JSON에 `total_cost_usd`와 `usage`가 들어 있었다.

리허설 확인(2026-10-16, Claude Code 2.1.301, 실습 02): 위 플래그가 모두 그대로 있고, 구독 로그인에서 `--safe-mode`와 `-p`가 함께 동작했다(답변 60회, 오류 0). JSON의 입력 토큰은 `usage.input_tokens`(캐시되지 않은 부분, 2 정도) + `usage.cache_creation_input_tokens` + `usage.cache_read_input_tokens`의 합이다. Claude Code가 시스템 프롬프트를 자동으로 캐시하므로 `input_tokens` 하나만 보면 안 된다.
