# 실습 01 프롬프트

아래 상자 안의 글을 그대로 복사해 이 저장소 폴더에서 연 Claude Code에 붙여 넣는다.
붙여 넣기 전에 README의 준비 1~3(`make check-env`, `make models`, `hindsight/.env` 만들기)을 끝낸다.

```text
이 저장소(ai-memory-lab)의 실습 01을 진행해 줘. 목표는 제공된 스크립트로 Hindsight(hindsight-api==1.0.0 고정)를 내 컴퓨터에 띄우고, Claude Code에 MCP로 연결할 준비를 마치는 것이야.

지킬 것
1. 제공된 make 명령과 hindsight/ 스크립트만 쓴다. 저장소 밖에 패키지를 설치하지 않고(.venv와 .cache는 저장소 안), Docker를 쓰지 않는다.
2. LLM 공급자는 hindsight/.env에 적힌 것(ollama 또는 API 키 공급자)만 쓴다. claude-code 공급자는 쓰지 않는다.
3. hindsight/.env는 열거나 출력하지 않는다. 키는 .env에만 있고 화면·로그·커밋에 남기지 않는다. 설정 확인은 make check-env와 make start가 출력하는 요약으로 한다.
4. 서버는 127.0.0.1:8888에만 연다(hindsight-api 1.0.0의 기본 호스트가 0.0.0.0이라 start.sh가 HINDSIGHT_API_HOST=127.0.0.1을 강제한다). 내장 DB 인스턴스는 memory-lab, 메모리 뱅크는 lab이다.
5. 임베딩은 HINDSIGHT_API_EMBEDDINGS_PROVIDER=onnx(intfloat/multilingual-e5-small, 'query: '·'passage: ' 접두어)로 쓴다. 이 줄을 지우거나 바꾸지 않고, 실행 중에 다른 모델을 내려받지 않는다. 데이터를 넣은 뒤에는 모델을 바꾸지 않는다(바꾸려면 make reset).
6. CLAUDE.md의 '개인 정보 질문은 먼저 hindsight recall로 확인한다' 줄과 .claude/settings.json의 autoMemoryEnabled=false를 지우지 않는다.

순서
1. make check-env 를 실행하고 결과 표를 그대로 보여 줘.
2. make start EP=01 을 실행하고 마지막 '상태' 블록을 그대로 보여 줘.
3. make check EP=01 을 실행하고 test_01 결과 6줄과 check_01 표를 그대로 보여 줘.
4. 실패하면 labs/01/README.md의 FAQ를 위에서부터 차례로 확인해 원인을 찾아. 스크립트나 설정을 고쳐야 하면 고치기 전에 무엇을 왜 바꿀지 먼저 말하고 내 답을 기다려.
5. 모두 끝나면 아래 MCP 연결 명령을 코드 블록으로 출력해 줘. 실행은 내가 이 폴더의 터미널에서 직접 한다.
   claude mcp add --transport http hindsight http://127.0.0.1:8888/mcp/lab/
6. 마지막으로 데이터 흐름을 세 줄로 설명해 줘: (1) 무엇이 내 컴퓨터에 남는지(기억 DB 위치, 임베딩 계산 위치, LLM 요청 추적), (2) 추출을 위해 문장이 어디로 나가는지(.env의 공급자 기준), (3) 이 대화가 어디로 가는지.
```
