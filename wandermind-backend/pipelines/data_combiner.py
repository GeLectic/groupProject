from typing import Any, Dict, List


def combine_source_chunks(
    youtube_chunks: List[Dict[str, Any]],
    community_chunks: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    master: List[Dict[str, Any]] = []

    for chunk in youtube_chunks:
        master.append(
            {
                "text": chunk.get("text", ""),
                "extracted": chunk.get("extracted"),
                "source": "youtube",
                "metadata": chunk.get("metadata", {}),
            }
        )

    for chunk in community_chunks:
        master.append(
            {
                "text": chunk.get("text", ""),
                "extracted": chunk.get("extracted"),
                "source": chunk.get("source", "reddit"),
                "metadata": chunk.get("metadata", {}),
            }
        )

    return master
