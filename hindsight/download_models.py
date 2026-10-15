"""make models: 실습 전체가 쓰는 모델을 미리 받는다 (저장소 안 .cache/huggingface).

- 임베딩 intfloat/multilingual-e5-small (onnx/model.onnx + 토크나이저)
- 재순위가 local이면 그 모델도
- LLM 공급자가 ollama면 ollama pull
"""
import os
import pathlib
import shutil
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent.parent
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")

EMBED_ID = "intfloat/multilingual-e5-small"


def read_env() -> dict:
    p = ROOT / "hindsight" / ".env"
    if not p.exists():
        p = ROOT / "hindsight" / ".env.example"
        print("  (hindsight/.env가 없어 .env.example 기준으로 받습니다)")
    env = {}
    for line in p.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def main() -> int:
    from huggingface_hub import snapshot_download

    env = read_env()
    rows = []

    t = time.time()
    snap = snapshot_download(
        repo_id=EMBED_ID,
        allow_patterns=["onnx/model.onnx", "onnx/model.onnx_data", "*.json", "sentencepiece.bpe.model", "tokenizer*"],
    )
    # 오프라인으로 다시 불러 384차원이 나오는지 확인
    os.environ["HF_HUB_OFFLINE"] = "1"
    import numpy as np
    import onnxruntime as ort
    from transformers import AutoTokenizer

    tok = AutoTokenizer.from_pretrained(EMBED_ID)
    sess = ort.InferenceSession(os.path.join(snap, "onnx", "model.onnx"), providers=["CPUExecutionProvider"])
    enc = tok(["query: 테스트"], return_tensors="np")
    feeds = {i.name: enc[i.name] for i in sess.get_inputs() if i.name in enc}
    if "token_type_ids" in [i.name for i in sess.get_inputs()] and "token_type_ids" not in feeds:
        feeds["token_type_ids"] = np.zeros_like(enc["input_ids"])
    dim = sess.run(None, feeds)[0].shape[-1]
    rows.append((EMBED_ID, f"{dim}차원", f"{time.time() - t:.1f}초"))
    os.environ.pop("HF_HUB_OFFLINE")

    if env.get("HINDSIGHT_API_RERANKER_PROVIDER", "local") == "local":
        rid = env.get("HINDSIGHT_API_RERANKER_LOCAL_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
        t = time.time()
        snapshot_download(repo_id=rid, allow_patterns=["*.json", "*.txt", "model.safetensors"])
        rows.append((rid, "재순위", f"{time.time() - t:.1f}초"))

    if env.get("HINDSIGHT_API_LLM_PROVIDER") == "ollama":
        model = env.get("HINDSIGHT_API_LLM_MODEL", "gemma3:12b")
        if not shutil.which("ollama"):
            print("✗ ollama 명령이 없습니다. labs/01/README.md의 Ollama 설치를 보세요.")
            return 1
        t = time.time()
        print(f"• ollama pull {model}")
        if subprocess.run(["ollama", "pull", model]).returncode != 0:
            print(f"✗ ollama pull {model} 실패")
            return 1
        rows.append((f"ollama {model}", "LLM", f"{time.time() - t:.1f}초"))

    print("\n받은 모델 (캐시: .cache/huggingface, Ollama는 ~/.ollama)")
    for name, kind, sec in rows:
        print(f"  {name:<45} {kind:<8} {sec}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
