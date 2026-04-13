from typing import Any, Dict, List, Set

import numpy as np

from processing.embedder import EmbeddingService


class QueryProcessor:
    def __init__(self, embedding_service: EmbeddingService) -> None:
        self.embedding_service = embedding_service

    def build_queries(self, destination: str, month: str) -> List[str]:
        return [
            f"{destination} best places visit {month}",
            f"{destination} hidden gems local secrets off beaten path",
            f"{destination} hotels accommodation cost per night",
            f"{destination} local food must eat dishes restaurants",
            f"{destination} day trips nearby excursions activities",
            f"{destination} transport getting around tips warnings",
        ]

    async def retrieve_contexts(
        self,
        destination: str,
        month: str,
        faiss_index: Any,
        metadata_store: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        queries = self.build_queries(destination, month)
        unique_indices: Set[int] = set()

        for query in queries:
            q_emb = await self.embedding_service.embed_texts([query])
            if q_emb.size == 0:
                continue
            _, indices = faiss_index.search(np.array(q_emb, dtype=np.float32), 8)
            unique_indices.update(int(i) for i in indices[0] if i >= 0)

        if len(unique_indices) < 5:
            broader = destination.split(",")[-1].strip() if "," in destination else destination.split()[-1]
            q_emb = await self.embedding_service.embed_texts([f"{broader} travel guide highlights"])
            if q_emb.size:
                _, indices = faiss_index.search(np.array(q_emb, dtype=np.float32), 12)
                unique_indices.update(int(i) for i in indices[0] if i >= 0)

        records = [
            {"idx": idx, **metadata_store[idx]}
            for idx in unique_indices
            if 0 <= idx < len(metadata_store)
        ]
        records.sort(key=lambda x: x.get("confidence", 0.0), reverse=True)

        char_budget = 12000
        consumed = 0
        chosen: List[Dict[str, Any]] = []
        for item in records:
            summary = item.get("summary") or item.get("original_text", "")[:500]
            rendered = (
                f"[SOURCE: {item.get('source')}] [CONFIDENCE: {item.get('confidence', 0):.2f}]\n"
                f"{summary}\n---\n"
            )
            if consumed + len(rendered) > char_budget:
                continue
            consumed += len(rendered)
            chosen.append(item)

        def _render(items: List[Dict[str, Any]]) -> str:
            return "\n".join(
                (
                    f"[SOURCE: {item.get('source')}] [CONFIDENCE: {item.get('confidence', 0):.2f}]\n"
                    f"{item.get('summary') or item.get('original_text', '')[:500]}\n---"
                )
                for item in items
            )

        hotel_keywords = ("hotel", "stay", "accommodation", "hostel", "resort", "price", "cost")
        places_keywords = (
            "place",
            "attraction",
            "sightseeing",
            "trek",
            "museum",
            "beach",
            "waterfall",
            "viewpoint",
            "temple",
        )
        food_keywords = ("food", "restaurant", "eat", "dish", "cafe", "street")

        hotel_items = []
        places_items = []
        food_items = []
        community_items = []

        for item in chosen:
            text = (item.get("summary") or "").lower()
            if any(k in text for k in hotel_keywords):
                hotel_items.append(item)
            if any(k in text for k in places_keywords):
                places_items.append(item)
            if any(k in text for k in food_keywords):
                food_items.append(item)
            if item.get("source") in {"reddit", "quora"}:
                community_items.append(item)

        full_context = _render(chosen)
        notices: List[str] = []
        if len(full_context) < 2000:
            notices.append("Limited data found, itinerary may rely partly on general knowledge")

        return {
            "combined_context": full_context,
            "hotel_context": _render(hotel_items) or full_context[:2500],
            "places_context": _render(places_items) or full_context[:4000],
            "food_context": _render(food_items) or full_context[:2500],
            "community_context": _render(community_items) or full_context[:3000],
            "indices": [item["idx"] for item in chosen],
            "notices": notices,
        }
