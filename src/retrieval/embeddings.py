from __future__ import annotations

from functools import lru_cache

from langchain_core.embeddings import Embeddings
from sentence_transformers import SentenceTransformer


@lru_cache(maxsize=2)
def _load_model(model_name: str) -> SentenceTransformer:
    # Pin inference to CPU and prefer an existing Hugging Face cache. Recent
    # Transformers versions otherwise make a metadata HEAD request even when
    # all model files are already cached, which breaks offline reruns.
    try:
        return SentenceTransformer(model_name, device="cpu", local_files_only=True)
    except Exception:
        # First-time setup still downloads the requested model normally.
        return SentenceTransformer(model_name, device="cpu")


class MiniLMEmbeddings(Embeddings):
    def __init__(self, model_name: str):
        self.model = _load_model(model_name)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self.model.encode(texts, normalize_embeddings=True).tolist()

    def embed_query(self, text: str) -> list[float]:
        return self.model.encode([text], normalize_embeddings=True)[0].tolist()
