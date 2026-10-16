# AI 기억 설계 실습. 사용법: make check-env → make models → make start EP=01 → make check EP=01
# 실습 02: make start EP=02 (Hindsight + 뱅크 lab02에 메모 50개 한 번) → compare.py → make check EP=02
EP ?= 01
SHELL := /bin/bash
PY312 := $(shell command -v python3.12 || command -v python3)
export HF_HOME := $(CURDIR)/.cache/huggingface
export UV_PROJECT_ENVIRONMENT := $(CURDIR)/.venv

.PHONY: help check-env install models start stop check check-01 check-02 reset

help:
	@echo "make check-env       준비물 확인 (check_00)"
	@echo "make models          패키지(.venv)와 모델(.cache, Ollama) 받기"
	@echo "make start EP=01     Hindsight 시작 (127.0.0.1:8888)"
	@echo "make start EP=02     Hindsight 시작 + 뱅크 lab02에 연습 메모 50개 넣기(한 번만)"
	@echo "make stop            Hindsight 종료"
	@echo "make check EP=01     test_01(통과/실패) + check_01(측정)"
	@echo "make check EP=02     test_02(통과/실패) + check_02(채점 표)"
	@echo "make reset           실습 기억 지우기 (내장 DB memory-lab + 로그)"

check-env:
	@$(PY312) labs/00/check_00.py

install:
	@uv sync --frozen --quiet

models: install
	@.venv/bin/python hindsight/download_models.py

start: install
	@case "$(EP)" in 01|02) ;; *) echo "이 저장소에는 EP=01, EP=02가 있습니다"; exit 1;; esac
	@bash hindsight/start.sh
	@if [ "$(EP)" = "02" ]; then echo; echo "seed (뱅크 lab02)"; .venv/bin/python labs/02/seed_02.py; fi

stop:
	@bash hindsight/stop.sh

check: install
	@case "$(EP)" in 01|02) ;; *) echo "이 저장소에는 EP=01, EP=02가 있습니다"; exit 1;; esac
	@if [ "$(EP)" = "02" ]; then $(MAKE) --no-print-directory check-02; else $(MAKE) --no-print-directory check-01; fi

check-02:
	@echo "== test_02 (데이터·결과 파일 검사) =="
	@.venv/bin/python -m pytest labs/02/tests -v -s --no-header -p no:warnings
	@echo
	@echo "== check_02 (채점) =="
	@.venv/bin/python labs/02/check_02.py

check-01:
	@echo "== test_01 (환경 검사) =="
	@.venv/bin/python -m pytest labs/01/tests -v -s --no-header -p no:warnings
	@echo
	@echo "== check_01 (측정) =="
	@.venv/bin/python labs/01/check_01.py

reset:
	@bash hindsight/reset.sh
