# ai-memory-lab

강의 시리즈 「AI 기억 설계」의 실습 저장소. 가짜 데이터만 쓴다.

편별 실습: 1편 → [`labs/01/PROMPT.md`](labs/01/PROMPT.md) ([안내](labs/01/README.md)) · 2편 → [`labs/02/PROMPT.md`](labs/02/PROMPT.md) ([안내](labs/02/README.md)) · 3편 → [`labs/03/PROMPT.md`](labs/03/PROMPT.md) ([안내](labs/03/README.md)) · 4편 → [`labs/04/PROMPT.md`](labs/04/PROMPT.md) ([안내](labs/04/README.md))

```bash
make check-env                             # 준비물 확인 (labs/00)
cp hindsight/.env.example hindsight/.env   # LLM 공급자 고르기 (기본: Ollama)
make models                                # 패키지·모델 받기 (저장소 안 .venv, .cache)
# 이 폴더에서 claude를 열고 labs/01/PROMPT.md를 붙여 넣는다

# 실습 02
make start EP=02                           # Hindsight + 뱅크 lab02에 가상 메모 50개(한 번만)
# claude를 열고 labs/02/PROMPT.md를 붙여 넣는다 → labs/02/compare.py
.venv/bin/python labs/02/compare.py        # claude -p 30회 → data/results_02.csv
make check EP=02                           # test_02 + check_02 표

# 실습 03
make start EP=03                           # Hindsight + 미니 메모리 틀(mini_memory/) + INTERFACE.md
# claude를 열고 labs/03/PROMPT.md를 붙여 넣는다 → Claude가 mini_memory/를 채운다
make check EP=03                           # test_03 8개
.venv/bin/python labs/03/show_hindsight.py # 같은 대화를 Hindsight 뱅크 lab03에 넣고 네트워크 표

# 실습 04
make start EP=04                           # test_03 확인(안 되면 labs/03/solution으로 시작) + INTERFACE.md
# claude를 열고 labs/04/PROMPT.md를 붙여 넣는다 → events·supersede·인용 검사를 더한다
make check EP=04                           # test_03 8개 + test_04 8개
.venv/bin/python labs/04/check_04.py       # (선택) claude -p 추출 → 인용 검사 통과·거절 표
```

| 경로 | 내용 |
|---|---|
| `hindsight/` | start.sh·stop.sh·reset.sh, .env.example (hindsight-api==1.0.0, 127.0.0.1:8888, 내장 DB memory-lab) |
| `labs/00/` | check_00: 준비물 확인 |
| `labs/01/` | README(목표·준비·FAQ), PROMPT, tests(test_01_*), check_01 |
| `labs/02/` | README·PROMPT·INTERFACE, seed_02(메모 50개 → 뱅크 lab02), tests(test_02_*), check_02 |
| `labs/03/` | README·PROMPT·INTERFACE, skeleton(미니 메모리 틀 → `mini_memory/`), solution(참고 구현), tests(test_03_*), show_hindsight |
| `labs/04/` | README·PROMPT·INTERFACE, start_04(앞 편 확인·시작점), tests(test_04_*), check_04(선택 측정), solution(참고 구현) |
| `mini_memory/` | 실습 03부터 내가(Claude와) 만드는 미니 메모리. `make start EP=03`이 틀을 복사한다. 가상환경은 `mini_memory/.venv`로 따로 |
| `backup/` | `make start EP=04`가 test_03을 통과하지 못한 내 `mini_memory/`를 옮겨 두는 곳 (git 무시) |
| `data/*_02.jsonl` | 실습 02 입력: 가상 인물·가상 회사 메모 50개, 질문 10개 |
| `data/conv_03.jsonl`, `data/sample_record_03*.md` | 실습 03 입력: 가상 대화 10턴, 따라 하기 프롬프트용 가상 작업 기록 두 개 |
| `data/conv_04.jsonl`, `data/sample_memory_04_*.md`, `data/sample_source_04.md`, `data/sample_summary_04.md` | 실습 04 입력: 가격이 바뀌는 가상 대화 10턴, 따라 하기 프롬프트용 가상 메모리 파일 |
| `labs/tokens.py` | `count_tokens()` 입력 토큰 어림값 |
| `labs/common.md` | `claude -p` 측정의 격리 플래그 |

환경: macOS(Apple Silicon)·Linux, Python 3.12, uv, git, Claude Code. Windows는 WSL2.
