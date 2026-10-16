# ai-memory-lab

강의 시리즈 「AI 기억 설계」의 실습 저장소. 가짜 데이터만 쓴다.

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
```

| 경로 | 내용 |
|---|---|
| `hindsight/` | start.sh·stop.sh·reset.sh, .env.example (hindsight-api==1.0.0, 127.0.0.1:8888, 내장 DB memory-lab) |
| `labs/00/` | check_00: 준비물 확인 |
| `labs/01/` | README(목표·준비·FAQ), PROMPT, tests(test_01_*), check_01 |
| `labs/02/` | README·PROMPT·INTERFACE, seed_02(메모 50개 → 뱅크 lab02), tests(test_02_*), check_02 |
| `data/*_02.jsonl` | 실습 02 입력: 가상 인물·가상 회사 메모 50개, 질문 10개 |
| `labs/tokens.py` | `count_tokens()` 입력 토큰 어림값 |
| `labs/common.md` | `claude -p` 측정의 격리 플래그 |

환경: macOS(Apple Silicon)·Linux, Python 3.12, uv, git, Claude Code. Windows는 WSL2.
