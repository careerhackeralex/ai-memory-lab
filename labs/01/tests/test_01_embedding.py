from conftest import LOG_PATH

E5 = "intfloat/multilingual-e5-small"


def test_01_embedding(env):
    assert env.get("HINDSIGHT_API_EMBEDDINGS_PROVIDER") == "onnx", "HINDSIGHT_API_EMBEDDINGS_PROVIDER=onnx 줄이 없습니다"
    model = env.get("HINDSIGHT_API_EMBEDDINGS_ONNX_MODEL_ID")
    assert model in (None, E5), f"임베딩 모델이 {E5}가 아닙니다: {model}"
    assert LOG_PATH.exists(), "서버 로그(data/logs/hindsight.log)가 없습니다. make start EP=01 먼저"
    log = LOG_PATH.read_text(errors="replace")
    assert "bge-small-en-v1.5" not in log, "로그에 영어 전용 기본 모델(bge-small-en-v1.5)을 불러온 기록이 있습니다"
    assert f"initializing ONNX provider with model {E5}" in log, "로그에 multilingual-e5-small 초기화 기록이 없습니다"
