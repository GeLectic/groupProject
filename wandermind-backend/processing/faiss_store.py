import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import faiss
import numpy as np

from config import settings


class FAISSStore:
    def __init__(self, base_dir: Optional[Path] = None) -> None:
        self.base_dir = base_dir or settings.faiss_base_path
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def destination_slug(self, destination: str) -> str:
        slug = destination.lower().split(",")[0].strip()
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        return slug.strip("-") or "destination"

    def _destination_dir(self, destination_slug: str) -> Path:
        path = self.base_dir / destination_slug
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _index_path(self, destination_slug: str) -> Path:
        return self._destination_dir(destination_slug) / "faiss_index.bin"

    def _metadata_path(self, destination_slug: str) -> Path:
        return self._destination_dir(destination_slug) / "metadata.json"

    def load_index(self, destination_slug: str) -> Tuple[Optional[faiss.Index], Optional[List[Dict[str, Any]]]]:
        index_path = self._index_path(destination_slug)
        metadata_path = self._metadata_path(destination_slug)
        if not index_path.exists() or not metadata_path.exists():
            return None, None

        index = faiss.read_index(str(index_path))
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        return index, metadata

    def build_and_save_index(
        self,
        destination_slug: str,
        chunks: List[Dict[str, Any]],
        embeddings: np.ndarray,
    ) -> Tuple[faiss.Index, List[Dict[str, Any]]]:
        if embeddings.dtype != np.float32:
            embeddings = embeddings.astype(np.float32)

        index = faiss.IndexFlatL2(384)
        if len(embeddings) > 0:
            index.add(embeddings)

        metadata_store = [
            {
                "original_text": chunk.get("text", ""),
                "summary": chunk.get("summary", ""),
                "source": chunk.get("source", ""),
                "extracted_facts": chunk.get("extracted"),
                "metadata": chunk.get("metadata", {}),
                "confidence": 1.0,
                "consensus_score": "single",
            }
            for chunk in chunks
        ]

        self.save(destination_slug=destination_slug, index=index, metadata_store=metadata_store)
        return index, metadata_store

    def save(self, destination_slug: str, index: faiss.Index, metadata_store: List[Dict[str, Any]]) -> None:
        index_path = self._index_path(destination_slug)
        metadata_path = self._metadata_path(destination_slug)

        faiss.write_index(index, str(index_path))
        metadata_path.write_text(json.dumps(metadata_store, ensure_ascii=True, indent=2), encoding="utf-8")

    def faiss_ready(self) -> bool:
        if not self.base_dir.exists():
            return False
        return any(self.base_dir.glob("*/faiss_index.bin"))
