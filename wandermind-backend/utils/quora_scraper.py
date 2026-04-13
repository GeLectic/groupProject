from typing import Dict, List

import httpx
from bs4 import BeautifulSoup

from utils.tavily_client import TavilySearchClient


PROMO_TERMS = ("click here", "buy now", "sponsored")


def _is_promotional(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in PROMO_TERMS)


async def scrape_quora(destination: str, month: str, tavily_client: TavilySearchClient) -> List[Dict]:
    query = f"site:quora.com {destination} travel tips {month}"
    results = await tavily_client.search(query=query, max_results=4, include_raw_content=True)

    result_rows = [r for r in results if isinstance(r, dict) and r.get("url")]
    if not result_rows:
        return []

    items: List[Dict] = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for row in result_rows:
            url = row.get("url")
            try:
                resp = await client.get(url, timeout=12)
                html_text = resp.text if resp.status_code == 200 else ""

                long_paragraphs: List[str] = []
                joined = ""
                if html_text:
                    soup = BeautifulSoup(html_text, "html.parser")
                    blocks = [tag.get_text(" ", strip=True) for tag in soup.find_all("p")]
                    # Some pages render answer content in generic divs.
                    blocks.extend(
                        tag.get_text(" ", strip=True)
                        for tag in soup.find_all("div")
                        if tag.get("class") and any("answer" in c.lower() for c in tag.get("class", []))
                    )

                    for block in blocks:
                        if len(block.split()) <= 10:
                            continue
                        if _is_promotional(block):
                            continue
                        long_paragraphs.append(block)

                if not long_paragraphs:
                    fallback_text = " ".join(
                        x
                        for x in [
                            row.get("title", ""),
                            row.get("content", ""),
                            row.get("raw_content", ""),
                        ]
                        if isinstance(x, str)
                    ).strip()
                    if len(fallback_text.split()) > 50 and not _is_promotional(fallback_text):
                        long_paragraphs = [fallback_text]

                if long_paragraphs:
                    joined = "\n\n".join(long_paragraphs)
                    if len(joined.split()) <= 50:
                        joined = ""

                if joined:
                    items.append(
                        {
                            "text": joined,
                            "source": "quora",
                            "url": url,
                            "score": 1,
                            "metadata": {
                                "url": url,
                                "title": row.get("title", ""),
                            },
                        }
                    )
            except Exception:
                fallback_text = " ".join(
                    x
                    for x in [
                        row.get("title", ""),
                        row.get("content", ""),
                        row.get("raw_content", ""),
                    ]
                    if isinstance(x, str)
                ).strip()
                if len(fallback_text.split()) > 50 and not _is_promotional(fallback_text):
                    items.append(
                        {
                            "text": fallback_text,
                            "source": "quora",
                            "url": url,
                            "score": 1,
                            "metadata": {
                                "url": url,
                                "title": row.get("title", ""),
                            },
                        }
                    )
                continue

    if not items:
        aggregate_parts = []
        for row in result_rows:
            title = row.get("title", "")
            content = row.get("content", "")
            part = " ".join(x for x in [title, content] if isinstance(x, str)).strip()
            if part and not _is_promotional(part):
                aggregate_parts.append(part)

        aggregate_text = "\n\n".join(aggregate_parts).strip()
        if len(aggregate_text.split()) > 50:
            items.append(
                {
                    "text": aggregate_text,
                    "source": "quora",
                    "url": result_rows[0].get("url", ""),
                    "score": 1,
                    "metadata": {
                        "url": result_rows[0].get("url", ""),
                        "title": "Aggregated Quora traveler tips",
                    },
                }
            )

    return items
