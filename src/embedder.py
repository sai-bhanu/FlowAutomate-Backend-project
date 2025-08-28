from __future__ import annotations
from typing import Optional
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    _HAS_ST = True
except Exception:
    _HAS_ST = False

try:
    from PIL import Image
    import base64, io
except Exception:
    Image = None

from .config import settings

class Embedder:
    def __init__(self):
        self.text_model = SentenceTransformer(settings.TEXT_MODEL) if _HAS_ST else None
        # For simplicity, reuse text model for table text; image model omitted in minimal setup.
        # You can load CLIP like: SentenceTransformer(settings.IMAGE_MODEL)
        self.dim = settings.EMBEDDING_DIM

    def embed_text(self, s: str) -> list[float]:
        if self.text_model:
            v = self.text_model.encode([s], normalize_embeddings=True)[0]
            return v.tolist()
        # Fallback: deterministic hash -> random-like vector (not semantic, but placeholder)
        rng = np.random.default_rng(abs(hash(s)) % (2**32))
        v = rng.normal(size=(self.dim,))
        v = v / np.linalg.norm(v)
        return v.tolist()

    def embed_image_b64(self, image_b64: str) -> list[float]:
        # Optional: if you load a CLIP model, convert to embedding.
        # Here we just fallback to hashing the bytes for a placeholder.
        import base64
        raw = base64.b64decode(image_b64.encode())
        rng = np.random.default_rng(abs(hash(raw)) % (2**32))
        v = rng.normal(size=(self.dim,))
        v = v / np.linalg.norm(v)
        return v.tolist()
