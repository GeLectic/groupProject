import asyncio
from typing import List, Optional

import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings


class EmbeddingService:
    def __init__(self, model_name: Optional[str] = None) -> None:
        self.model_name = model_name or settings.embedding_model
        self.model: Optional[SentenceTransformer] = None
        self._lock = asyncio.Lock()

    async def ensure_loaded(self) -> None:
        if self.model is not None:
            return
        async with self._lock:
            if self.model is not None:
                return

            def _load() -> SentenceTransformer:
                return SentenceTransformer(self.model_name)

            self.model = await asyncio.to_thread(_load)

    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, 384), dtype=np.float32)
        await self.ensure_loaded()

        assert self.model is not None

        def _encode() -> np.ndarray:
            arr = self.model.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
            return arr.astype(np.float32)

        return await asyncio.to_thread(_encode)
