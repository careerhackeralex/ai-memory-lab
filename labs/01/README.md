# 실습 01 — 내 컴퓨터에서 Hindsight를 띄우고 Claude Code에 연결하기

## 목표

- 제공 스크립트로 Hindsight(`hindsight-api==1.0.0`)를 `127.0.0.1:8888`에 띄운다. 내장 DB 인스턴스 `memory-lab`, 메모리 뱅크 `lab`.
- Claude Code에 MCP(`/mcp/lab/`)로 연결한다.
- 세션 A에서 가상 인물의 사실을 저장하고, 새 세션 B에서 Hindsight recall 도구로 다시 꺼낸다.
- 데이터가 어디에 남고 어디로 나가는지 그림 한 장으로 정리한다.

이어지는 실습: 없음(시작점). 내부 구조(네 네트워크, retain·recall)는 EP3에서 연다.

## 준비 (프롬프트를 붙여 넣기 전)

1. **준비물 확인**: `make check-env` (check_00). Python 3.12·uv·git·Claude Code, 포트 8888, LLM 공급자를 본다. Windows는 WSL2 안에서 저장소를 받는다.
2. **LLM 공급자 고르기**: `cp hindsight/.env.example hindsight/.env`.
   - 기본은 **Ollama**(키 없음, 내 컴퓨터에서 실행). macOS는 `brew install ollama && brew services start ollama`(끄기: `brew services stop ollama`), Linux는 ollama.com의 설치 스크립트. 권장 모델 `gemma3:12b`(내려받기 8.2GB, 실행 중 메모리 약 8GB). Hindsight 서버도 약 2GB를 쓰므로 메모리 16GB 미만 컴퓨터는 API 키 공급자를 쓴다.
   - **API 키 공급자**(anthropic·openai 등)를 쓰려면 `.env`의 Ollama 네 줄을 주석 처리하고 대안 블록을 연다. 키는 `.env`에만 둔다(.gitignore에 들어 있음).
   - `HINDSIGHT_API_HOST=127.0.0.1`, `HINDSIGHT_API_EMBEDDINGS_PROVIDER=onnx`, `HINDSIGHT_API_RERANKER_PROVIDER=rrf`, `HINDSIGHT_API_MCP_ENABLED_TOOLS=sync_retain,recall` 줄은 지우지 않는다.
   - LLM 요청 추적은 기본으로 켜져 있고 1일 보관된다(`HINDSIGHT_API_LLM_TRACE_RETENTION_DAYS`).
3. **모델 받기**: `make models`. 저장소 안 `.venv`에 패키지(hindsight-api 1.0.0, 약 1.8GB)를, `.cache/huggingface`에 임베딩 모델 `intfloat/multilingual-e5-small`(384차원, 다국어)을 받고, Ollama면 모델을 `ollama pull`한다. 모델은 첫 데이터를 넣기 전에 정한다. 데이터를 넣은 뒤 바꾸려면 `make reset` 뒤 다시 넣는다.

## 진행

1. 이 폴더에서 Claude Code를 연다: `claude` (자동 기억까지 확실히 끄려면 `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude`). 처음 열면 '이 폴더를 신뢰하나요' 질문과 함께 `.claude/settings.json`이 미리 허용한 권한 26개(실습 02용 4개, 실습 03용 6개, 실습 04용 2개 포함)가 표시된다. 아래 '미리 허용한 것'과 같은지 보고 `Yes, I trust this folder`를 고른다. 신뢰하지 않은 폴더에서는 Claude Code가 이 허용 목록을 무시한다(`claude -p`도 마찬가지).
2. `labs/01/PROMPT.md`의 상자 안 글을 붙여 넣는다. Claude가 `make check-env` → `make start EP=01` → `make check EP=01`을 실행해 결과를 보여 주고, MCP 연결 명령과 데이터 흐름 세 줄을 출력한다. 이 명령들은 `.claude/settings.json`에서 미리 허용해 두어 권한 질문 없이 실행된다(아래 '미리 허용한 것').
3. Claude Code를 끄고(`/exit`) 같은 폴더의 터미널에서 MCP를 연결한다:
   ```bash
   claude mcp add --transport http hindsight http://127.0.0.1:8888/mcp/lab/
   claude mcp list      # hindsight: ... - ✓ Connected
   ```
4. **세션 A**: `claude`로 새 세션을 열고 `/mcp`에서 hindsight가 connected인지, 도구 목록에 sync_retain과 recall이 있는지 본다(`.env`에서 이 둘만 열었다). 그다음
   > 내 기억에 저장해 줘: 나는 데이터 분석에 Python을 주로 쓰고, 지금은 Acme에서 일한다

   Claude가 `hindsight - sync_retain` 도구를 부르는지 화면에서 확인한다. sync_retain은 추출이 끝날 때까지 기다린다(Ollama gemma3:12b 기준 약 7~15초, 첫 호출은 모델을 메모리에 올리느라 더 걸린다).
5. **세션 B**: `/exit` 뒤 새 세션에서
   > 내가 주로 쓰는 언어는?

   Claude가 `hindsight - recall` 도구를 부르고 Python이라고 답하는지 본다.
6. `make check EP=01`로 test_01 6개 통과와 check_01 표를 다시 확인한다.
7. 데이터 흐름 그림을 채운다(아래).

### 세션 B의 답은 어디서 오나

- 저장소 `.claude/settings.json`의 `autoMemoryEnabled: false`로 Claude Code 자체 기억(auto memory)을 꺼 두었다.
- 저장소 `CLAUDE.md`에는 '개인 정보 질문은 먼저 hindsight recall로 확인한다' 한 줄만 있다. 이 줄은 recall 도구를 부르라는 **안내**일 뿐 사실을 담고 있지 않다. 'Python'이라는 사실은 Hindsight 데이터(내장 DB)에서 온다.
- 확인 방법: 세션 B 화면에 `hindsight - recall (MCP)` 호출과 그 결과(`User primarily uses Python ...`)가 보여야 한다.

## 데이터 흐름

```
Claude Code ──(대화 전체)──▶ Anthropic API
     │
     │ MCP (HTTP, 127.0.0.1:8888/mcp/lab/)
     ▼
Hindsight 서버 (내 컴퓨터, 127.0.0.1만)
     ├─ 임베딩: intfloat/multilingual-e5-small, onnx, 내 CPU에서 계산 (.cache/huggingface)
     ├─ 추출·통합 LLM ──▶ Ollama(내 컴퓨터, 127.0.0.1:11434)  또는  API 공급자(클라우드)
     └─ 내장 DB pg0 인스턴스 memory-lab (~/.pg0/instances/memory-lab/data)
           ├─ 기억(사실·관찰·임베딩)
           └─ LLM 요청 추적: 추출 요청 원문·응답, 기본 켜짐, 1일 보관
```

- 내 컴퓨터에 남는 것: 기억 DB(`~/.pg0/instances/memory-lab/data`), 서버 로그(`data/logs/hindsight.log`), LLM 요청 추적(같은 DB, 1일), 모델 파일(`.cache/huggingface`, Ollama는 `~/.ollama`).
- 추출 때 문장이 나가는 곳: Ollama면 내 컴퓨터 밖으로 나가지 않는다. API 키 공급자면 그 공급자 서버로 retain 문장과 추출 프롬프트가 간다.
- 대화가 나가는 곳: Claude Code 대화(recall 결과 포함)는 Anthropic으로 간다.

## 미리 허용한 것 (`.claude/settings.json`)

| 허용 | 이유 |
|---|---|
| `make check-env`, `make models`, `make start/stop/check EP=01` | 실습 스크립트 실행 |
| `curl -s http://127.0.0.1:8888/*` | 로컬 서버 상태 확인 |
| `lsof -i :8888`, `tail -n 50 data/logs/hindsight.log` | FAQ 진단 |
| `mcp__hindsight__retain`, `mcp__hindsight__sync_retain`, `mcp__hindsight__recall` | 세션 A/B의 저장·회상 |
| `Edit`·`Write(./labs/02/compare.py)`, `.venv/bin/python labs/02/compare.py --dry-run` | 실습 02: compare.py 쓰기와 호출 없는 확인 |
| `Edit`·`Write(./mini_memory/**)`, `uv run --project mini_memory mm *`·`mini-memory *`(미니 메모리의 두 명령만. `python` 등 다른 실행 파일은 매번 묻는다), `mcp__mini-memory__remember`·`recall` | 실습 03: 미니 메모리 코드 쓰기·실행, MCP 도구 저장·회상 |
| `mcp__mini-memory__record_event`·`supersede` | 실습 04: 원본 기록 추가, 사실 대체 (코드 쓰기·`mm` 실행은 실습 03 허용 그대로) |

막아 둔 것: `hindsight/.env` 읽기·편집·`cat`. `make reset`은 허용하지 않았으니 부르면 Claude Code가 물어본다. Hindsight 쪽에서도 `.env`의 `HINDSIGHT_API_MCP_ENABLED_TOOLS=sync_retain,recall`로 MCP 도구를 둘만 연다(1.0.0 기본은 delete_bank·clear_memories를 포함한 36개). `mcp__hindsight__retain` 허용은 이 줄을 지운 경우를 위해 남겨 두었다.

## 테스트와 측정

- `test_01_*`(통과/실패, 결정적): env(.env 존재·claude-code 아님·git 무시), bind(127.0.0.1:8888만), embedding(onnx·e5 모델, 로그에 bge 없음), mcp(`/mcp/lab/` tools/list에 retain 또는 sync_retain, recall), automem_off(autoMemoryEnabled=false, CLAUDE.md 안내 줄), no_key_leak(로그·추적·추적 파일에 키 문자열 없음).
- `check_01_*`(측정, 표로만 표시): roundtrip(REST retain → '내가 주로 쓰는 언어는?' recall에 Python), restart(stop → start 뒤 같은 recall). check는 세션 A/B와 섞이지 않게 별도 뱅크 `lab-check`를 매번 새로 만든다.

## FAQ (막혔을 때, 위에서부터)

1. **포트 8888이 이미 사용 중** → `lsof -i :8888`로 확인해 그 프로그램을 끈다. 바꾸려면 `.env`의 `HINDSIGHT_API_PORT`와 MCP 주소를 함께 바꾼다.
2. **Intel Mac에서 설치 실패** → hindsight-api의 의존성(torch)이 Intel Mac 휠을 내지 않는다. start.sh가 감지해 멈춘다. Hindsight 문서의 `hindsight-all-slim` 설치 안내를 따른다(이 저장소 스크립트 밖).
3. **첫 실행이 오래 걸림** → 오래 걸리는 것은 `make models`다: 패키지 약 1.8GB(.venv), 임베딩 모델 약 470MB(.cache), Ollama 모델 8.2GB. 리허설(Mac mini M4 Pro, 캐시 없음)에서 약 2분이 걸렸다. 내장 DB(PostgreSQL 18, pgvector)는 패키지 안에 들어 있어 첫 `make start` 때 `~/.pg0`에 풀기만 한다(약 2초, 내려받기 없음). 프록시 환경이면 `HF_ENDPOINT`나 수동 다운로드(Hugging Face에서 `intfloat/multilingual-e5-small`의 `onnx/model.onnx`와 토크나이저 파일을 `.cache/huggingface/hub/`에)를 쓴다.
4. **같은 네트워크에서 접근 가능해 보임** → hindsight-api 1.0.0의 기본 호스트는 0.0.0.0이다(config.py 1514행). start.sh가 `HINDSIGHT_API_HOST=127.0.0.1`을 강제하고 test_01_bind가 확인한다.
5. **MCP 서버가 안 보임** → `claude mcp add`의 기본 범위는 local(현재 프로젝트)이다. 이 폴더에서 추가했는지 `claude mcp list`로 확인하고 새 세션을 연다. 주소 끝의 `/`까지 정확히 쓴다.
6. **새 세션이 Hindsight 없이도 기억하는 것처럼 보임** → Claude Code 자동 기억이 켜져 있으면 생긴다. `/memory`에서 꺼져 있는지 보고, `CLAUDE_CODE_DISABLE_AUTO_MEMORY=1 claude`로 연다.
7. **recall 결과가 비어 있음(Ollama)** → 세션 A가 비동기 `retain`을 불렀다면 추출이 끝나기 전일 수 있다(`.env`에 `HINDSIGHT_API_MCP_ENABLED_TOOLS=sync_retain,recall`이 있는지 본다). 30초 뒤 다시 묻는다. 그래도 비면 `tail -n 50 data/logs/hindsight.log`에서 LLM 오류를 보고, 권장 모델(gemma3:12b)인지, `HINDSIGHT_API_LLM_OLLAMA_NUM_CTX=16384`가 있는지 확인한다. 작은 모델(4B 이하)은 추출이 빈약할 수 있다. 그래도 안 되면 API 키 공급자로 바꾼다.
8. **한국어 질문에 엉뚱한 기억이 먼저 나옴** → 재순위 기본값 local은 영어 전용 `cross-encoder/ms-marco-MiniLM-L-6-v2`다. `.env`에 `HINDSIGHT_API_RERANKER_PROVIDER=rrf`가 있는지 본다. 임베딩 기본값 local도 영어 전용 `BAAI/bge-small-en-v1.5`(config.py 1222–1223행)라 `.env`를 새로 만들었다면 `.env.example`에서 onnx 줄을 다시 복사하고 test_01_embedding으로 확인한다.
9. **데이터를 넣은 뒤 임베딩 공급자를 바꿨더니 recall이 이상함** → 기본 모델과 e5 모델은 둘 다 384차원이라 서버가 오류 없이 옛 벡터와 새 벡터를 섞는다(migrations.py 640–717행: 차원이 같으면 표를 그대로 둔다). `make reset` 뒤 다시 넣는다.
10. **세션 B가 recall을 부르지 않고 모른다고 답함** → 도구를 부를지는 모델이 정한다. CLAUDE.md의 recall 안내 줄이 있는지 보고, 'Hindsight에서 찾아서'를 붙여 다시 묻는다.
11. **도구 목록에 retain이 없고 sync_retain만 보임** → 정상이다. 이 실습의 `.env`가 sync_retain과 recall만 연다. test_01_mcp는 retain·sync_retain 중 하나와 recall이 있으면 통과한다(1.0.0 기본 설정은 둘 다 노출).
12. **Windows에서 start.sh가 실행되지 않음** → WSL2 안에서 저장소를 받아 실행한다.
13. **저장소를 새로 받았는데 예전 기억이 나옴** → 내장 DB는 저장소 밖 `~/.pg0/instances/memory-lab`에 있어 저장소를 지우거나 다시 받아도 남는다. 처음부터 하려면 `make reset`.
14. **실패가 반복됨** → `make reset`으로 memory-lab 인스턴스와 로그를 지우고 `make start EP=01`부터 다시 한다.

## 비용

두 갈래로 따로 적는다. 숫자는 2026-10-15 리허설(Mac mini M4 Pro 48GB) 기준이다.

- Claude Code 사용: 프롬프트 1회와 대화 세션 2개. 구독이면 사용량 한도에서 차감, API 키면 사용량 과금. 리허설 측정값은 REHEARSAL 기록을 본다.
- Hindsight의 LLM: retain 한 번에 추출 1회 + 통합 1회(입력 약 2,000~3,300 토큰). Ollama는 로컬 연산이라 0원, API 키 공급자는 그 공급자 요금.
