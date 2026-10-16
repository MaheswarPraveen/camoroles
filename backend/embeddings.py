from typing import List
import os

_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        try:
            from fastembed import TextEmbedding
            # BAAI/bge-small-en-v1.5 produces dense 384-dim embeddings, optimized for retrieval
            _embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")
        except ImportError:
            _embedding_model = None
    return _embedding_model

def generate_embedding(text: str) -> List[float]:
    """Generates a 384-dimensional vector embedding for text."""
    model = get_embedding_model()
    if model is not None:
        generator = model.embed([text])
        for vector in generator:
            return vector.tolist()

    # Fallback or stub if fastembed is not yet installed in current env
    raise RuntimeError("FastEmbed is not installed. Run `pip install fastembed` to enable local CPU embeddings.")
