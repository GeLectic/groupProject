import re
from typing import Any, Dict, List

from utils.groq_client import GroqClient, run_batched_json_extractions
from utils.quora_scraper import scrape_quora
from utils.reddit_scraper import scrape_reddit
from utils.tavily_client import TavilySearchClient
from config import settings


PROMO_TERMS = ("click here", "buy now", "sponsored")


def _word_set(text: str) -> set:
    return set(re.findall(r"\w+", text.lower()))


def _similarity(a: str, b: str) -> float:
    wa = _word_set(a)
    wb = _word_set(b)
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def _is_pure_question(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return True
    sentence_like = stripped.count(".") + stripped.count("!")
    return stripped.endswith("?") and sentence_like <= 1


def _contains_promo(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in PROMO_TERMS)


def _filter_and_deduplicate(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    filtered = []
    for item in items:
        text = item.get("text", "")
        if len(text.split()) < 50:
            continue
        if _contains_promo(text):
            continue
        if _is_pure_question(text):
            continue
        filtered.append(item)

    filtered.sort(key=lambda x: x.get("score", 0), reverse=True)
    deduped: List[Dict[str, Any]] = []
    for item in filtered:
        text = item.get("text", "")
        duplicate = False
        for kept in deduped:
            if _similarity(text, kept.get("text", "")) > 0.70:
                duplicate = True
                break
        if not duplicate:
            deduped.append(item)

    return deduped


async def run_community_pipeline(
    destination: str,
    month: str,
    days: int,
    groq_client: GroqClient,
    tavily_client: TavilySearchClient,
) -> Dict[str, Any]:
    reddit_posts = await scrape_reddit(destination=destination, month=month, days=days)
    quora_items = await scrape_quora(destination=destination, month=month, tavily_client=tavily_client)

    normalized: List[Dict[str, Any]] = []

    for post in reddit_posts:
        text = post.get("full_text") or post.get("body", "")
        normalized.append(
            {
                "text": text,
                "source": "reddit",
                "score": post.get("score", 0),
                "metadata": {
                    "title": post.get("title", ""),
                    "url": post.get("url", ""),
                    "score": post.get("score", 0),
                },
            }
        )

    for item in quora_items:
        normalized.append(
            {
                "text": item.get("text", ""),
                "source": "quora",
                "score": item.get("score", 1),
                "metadata": {"url": item.get("url", "")},
            }
        )

    filtered = _filter_and_deduplicate(normalized)
    # Bound expensive extraction calls to keep first-run latency predictable.
    filtered = filtered[: settings.max_community_chunks_for_extraction]

    extracted_payloads: List[Dict[str, Any]] = []
    if groq_client.enabled and filtered:
        extracted_payloads = await run_batched_json_extractions(
            groq_client=groq_client,
            texts=[f["text"] for f in filtered],
            batch_size=5,
        )
    else:
        extracted_payloads = [
            {
                "places_mentioned": [],
                "food_tips": [],
                "transport_tips": [],
                "hidden_gems": [],
                "warnings": [],
                "estimated_costs": [],
                "best_time_tips": [],
            }
            for _ in filtered
        ]

    chunks: List[Dict[str, Any]] = []
    for item, extracted in zip(filtered, extracted_payloads):
        chunks.append(
            {
                "text": item["text"],
                "extracted": extracted,
                "source": item["source"],
                "metadata": item["metadata"],
            }
        )

    return {
        "chunks": chunks,
        "reddit_posts_used": len([c for c in chunks if c["source"] == "reddit"]),
        "quora_pages_used": len([c for c in chunks if c["source"] == "quora"]),
    }
