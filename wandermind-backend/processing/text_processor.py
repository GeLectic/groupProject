import asyncio
from typing import Any, Dict, List

from config import settings
from utils.groq_client import GroqClient


async def _summarize_single_chunk(
    chunk: Dict[str, Any],
    destination: str,
    groq_client: GroqClient,
) -> str:
    text = chunk.get("text", "")[: settings.max_groq_input_chars]

    if not groq_client.enabled:
        return text[:350]

    try:
        summary = await groq_client.chat(
            system_prompt="You are a travel information summarizer.",
            user_prompt=(
                "Summarize the key travel insights from this text in 3-5 concise sentences. "
                f"Focus only on specific, actionable information for someone visiting {destination}. "
                f"Ignore generic advice. Text: {text}"
            ),
            max_tokens=settings.max_groq_output_tokens,
            temperature=0.2,
        )
        return summary.strip()
    except Exception:
        return text[:350]


async def summarize_chunks(
    chunks: List[Dict[str, Any]],
    destination: str,
    groq_client: GroqClient,
) -> List[Dict[str, Any]]:
    if not chunks:
        return []

    summarized: List[Dict[str, Any]] = []
    batch_size = 3
    llm_budget = max(0, settings.max_llm_summary_chunks)

    for start in range(0, len(chunks), batch_size):
        batch = chunks[start : start + batch_size]
        tasks = []
        for offset, chunk in enumerate(batch):
            global_index = start + offset
            if not groq_client.enabled or global_index >= llm_budget:
                # Fast-path fallback keeps indexing quality reasonable while avoiding long waits.
                tasks.append(asyncio.sleep(0, result=chunk.get("text", "")[:350]))
            else:
                tasks.append(
                    _summarize_single_chunk(
                        chunk=chunk,
                        destination=destination,
                        groq_client=groq_client,
                    )
                )

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for chunk, summary in zip(batch, results):
            chunk_copy = dict(chunk)
            if isinstance(summary, Exception):
                chunk_copy["summary"] = chunk.get("text", "")[:350]
            else:
                chunk_copy["summary"] = summary
            summarized.append(chunk_copy)

        if start + batch_size < len(chunks) and groq_client.enabled:
            await asyncio.sleep(0.2)

    return summarized
