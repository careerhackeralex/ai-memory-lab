# AI 기억 설계 실습. 사용법: make check-env → make models → make start EP=01 → make check EP=01
# 실습 02: make start EP=02 (Hindsight + 뱅크 lab02에 메모 50개 한 번) → compare.py → make check EP=02
# 실습 03: make start EP=03 (Hindsight + mini_memory/ 틀) → PROMPT.md → make check EP=03 → show_hindsight.py
# 실습 04: make start EP=04 (test_03 확인, 안 되면 labs/03/solution으로 시작) → PROMPT.md → make check EP=04 → (선택) check_04.py
EP ?= 01
SHELL := /bin/bash
PY312 := $(shell command -v python3.12 || command -v python3)
export HF_HOME := $(CURDIR)/.cache/huggingface
export UV_PROJECT_ENVIRONMENT := $(CURDIR)/.venv

.PHONY: help check-env install models start start-03 start-04 stop check check-01 check-02 check-03 check-04 reset

help:
	@echo "make check-env       준비물 확인 (check_00)"
	@echo "make models          패키지(.venv)와 모델(.cache, Ollama) 받기"
	@echo "make start EP=01     Hindsight 시작 (127.0.0.1:8888)"
	@echo "make start EP=02     Hindsight 시작 + 뱅크 lab02에 연습 메모 50개 넣기(한 번만)"
	@echo "make stop            Hindsight 종료"
	@echo "make start EP=03     Hindsight 시작 + 미니 메모리 틀(mini_memory/) 준비 + INTERFACE.md 보기"
	@echo "make start EP=04     test_03 확인(통과 못 하면 내 코드를 backup/에 두고 labs/03/solution 복사) + INTERFACE.md 보기"
	@echo "make check EP=01     test_01(통과/실패) + check_01(측정)"
	@echo "make check EP=02     test_02(통과/실패) + check_02(채점 표)"
	@echo "make check EP=03     test_03 8개 (미니 메모리 MCP·CLI·SQLite)"
	@echo "make check EP=04     test_03 8개 + test_04 8개 (events 추가 전용·supersede·이력·인용 검사)"
	@echo "make reset           실습 기억 지우기 (내장 DB memory-lab, 미니 메모리 DB, 로그, check_04 결과)"

check-env:
	@$(PY312) labs/00/check_00.py

install:
	@uv sync --frozen --quiet

models: install
	@.venv/bin/python hindsight/download_models.py

start: install
	@case "$(EP)" in 01|02|03|04) ;; *) echo "이 저장소에는 EP=01~04가 있습니다"; exit 1;; esac
	@if [ "$(EP)" = "03" ]; then $(MAKE) --no-print-directory start-03; exit; fi; if [ "$(EP)" = "04" ]; then $(MAKE) --no-print-directory start-04; exit; fi; bash hindsight/start.sh
	@if [ "$(EP)" = "02" ]; then echo; echo "seed (뱅크 lab02)"; .venv/bin/python labs/02/seed_02.py; fi

# 미니 메모리는 저장소 .venv(Hindsight)와 따로 mini_memory/.venv를 쓴다. UV_PROJECT_ENVIRONMENT를 풀어야 섞이지 않는다.
start-03:
	@echo "== Hindsight (6단계 show_hindsight.py용. 꺼져 있어도 1~5단계는 진행할 수 있다) =="
	@bash hindsight/start.sh || echo "• Hindsight 없이 계속: 6단계 전에 make start EP=03을 다시 실행하세요."
	@echo
	@echo "== 미니 메모리 틀 (mini_memory/) =="
	@if [ -f mini_memory/pyproject.toml ]; then echo "• mini_memory/가 이미 있음 → 그대로 둔다 (틀부터 다시 하려면 mini_memory/를 지우고 다시 실행)"; \
	 else cp -R labs/03/skeleton mini_memory && echo "• labs/03/skeleton → mini_memory/ (pyproject.toml, uv.lock, src/mini_memory/의 빈 모듈 store·server·cli)"; fi
	@env -u UV_PROJECT_ENVIRONMENT uv sync --project mini_memory --quiet
	@echo "• mini_memory/.venv 준비: mcp $$(mini_memory/.venv/bin/python -c 'import importlib.metadata as m; print(m.version("mcp"))'), 진입점 mm·mini-memory는 아직 없음(프롬프트에서 Claude가 등록)"
	@echo "• 미니 메모리 DB: $${MINI_MEMORY_DB:-data/mini_memory.db} ($$([ -f "$${MINI_MEMORY_DB:-data/mini_memory.db}" ] && echo 있음 || echo '아직 없음, 처음 저장할 때 만들어짐'))"
	@echo
	@echo "== labs/03/INTERFACE.md =="
	@cat labs/03/INTERFACE.md

# 실습 04는 Hindsight를 쓰지 않는다. 앞 편 확인과 시작점 복사는 labs/04/start_04.sh
start-04:
	@bash labs/04/start_04.sh

stop:
	@bash hindsight/stop.sh

check: install
	@case "$(EP)" in 01|02|03|04) ;; *) echo "이 저장소에는 EP=01~04가 있습니다"; exit 1;; esac
	@$(MAKE) --no-print-directory check-$(EP)

check-02:
	@echo "== test_02 (데이터·결과 파일 검사) =="
	@.venv/bin/python -m pytest labs/02/tests -v -s --no-header -p no:warnings
	@echo
	@echo "== check_02 (채점) =="
	@.venv/bin/python labs/02/check_02.py

check-03:
	@if [ ! -f mini_memory/pyproject.toml ]; then echo "✗ mini_memory/가 없습니다. 먼저 make start EP=03"; exit 1; fi
	@echo "== test_03 (미니 메모리: MCP 도구·CLI·SQLite, 테스트마다 임시 DB) =="
	@env -u UV_PROJECT_ENVIRONMENT .venv/bin/python -m pytest labs/03/tests -v --no-header -p no:warnings

check-04:
	@if [ ! -f mini_memory/pyproject.toml ]; then echo "✗ mini_memory/가 없습니다. 먼저 make start EP=04"; exit 1; fi
	@echo "== test_03 (앞 편 계약) =="
	@env -u UV_PROJECT_ENVIRONMENT .venv/bin/python -m pytest labs/03/tests -v --no-header -p no:warnings; r3=$$?; \
	 echo; echo "== test_04 (events 추가 전용·supersede·이력·인용 검사, 테스트마다 임시 DB) =="; \
	 env -u UV_PROJECT_ENVIRONMENT .venv/bin/python -m pytest labs/04/tests -v --no-header -p no:warnings; r4=$$?; \
	 [ $$r3 = 0 ] && [ $$r4 = 0 ]

check-01:
	@echo "== test_01 (환경 검사) =="
	@.venv/bin/python -m pytest labs/01/tests -v -s --no-header -p no:warnings
	@echo
	@echo "== check_01 (측정) =="
	@.venv/bin/python labs/01/check_01.py

reset:
	@bash hindsight/reset.sh
