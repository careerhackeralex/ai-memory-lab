# AI 기억 설계 실습. 사용법: make check-env → make models → make start EP=01 → make check EP=01
EP ?= 01
SHELL := /bin/bash
PY312 := $(shell command -v python3.12 || command -v python3)
export HF_HOME := $(CURDIR)/.cache/huggingface
export UV_PROJECT_ENVIRONMENT := $(CURDIR)/.venv

.PHONY: help check-env install models start stop check reset

help:
	@echo "make check-env       준비물 확인 (check_00)"
	@echo "make models          패키지(.venv)와 모델(.cache, Ollama) 받기"
	@echo "make start EP=01     Hindsight 시작 (127.0.0.1:8888)"
	@echo "make stop EP=01      Hindsight 종료"
	@echo "make check EP=01     test_01(통과/실패) + check_01(측정)"
	@echo "make reset           실습 기억 지우기 (내장 DB memory-lab + 로그)"

check-env:
	@$(PY312) labs/00/check_00.py

install:
	@uv sync --frozen --quiet

models: install
	@.venv/bin/python hindsight/download_models.py

start: install
	@test "$(EP)" = "01" || { echo "이 저장소에는 EP=01까지만 있습니다"; exit 1; }
	@bash hindsight/start.sh

stop:
	@bash hindsight/stop.sh

check: install
	@test "$(EP)" = "01" || { echo "이 저장소에는 EP=01까지만 있습니다"; exit 1; }
	@echo "== test_01 (환경 검사) =="
	@.venv/bin/python -m pytest labs/01/tests -v -s --no-header -p no:warnings
	@echo
	@echo "== check_01 (측정) =="
	@.venv/bin/python labs/01/check_01.py

reset:
	@bash hindsight/reset.sh
