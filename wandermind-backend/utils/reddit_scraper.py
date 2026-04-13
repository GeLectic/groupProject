import asyncio
import re
from typing import Dict, List

import httpx


HEADERS = {"User-Agent": "WanderMind/1.0 (travel itinerary bot)"}
BASE_URL = "https://www.reddit.com"


async def search_subreddit(client: httpx.AsyncClient, subreddit: str, query: str) -> List[Dict]:
    url = f"{BASE_URL}/r/{subreddit}/search.json"
    params = {"q": query, "sort": "top", "t": "all", "limit": 10, "restrict_sr": 1}

    for attempt in range(2):
        try:
            resp = await client.get(url, params=params, headers=HEADERS, timeout=10)
            if resp.status_code == 429:
                await asyncio.sleep(3)
                if attempt == 0:
                    continue
                return []
            if resp.status_code in (403, 404):
                return []
            if resp.status_code != 200:
                return []

            posts = resp.json().get("data", {}).get("children", [])
            results = []
            for post in posts:
                p = post.get("data", {})
                score = int(p.get("score", 0))
                body = p.get("selftext", "")
                if score < 5:
                    continue
                if len(body) < 80:
                    continue

                permalink = p.get("permalink", "")
                results.append(
                    {
                        "title": p.get("title", ""),
                        "body": body[:2000],
                        "url": f"{BASE_URL}{permalink}",
                        "permalink": permalink,
                        "score": score,
                        "source": "reddit",
                    }
                )
            return results
        except Exception:
            if attempt == 1:
                return []
    return []


async def fetch_post_comments(client: httpx.AsyncClient, permalink: str) -> List[str]:
    url = f"{BASE_URL}{permalink}.json"
    params = {"sort": "top", "limit": 8, "depth": 1}
    try:
        resp = await client.get(url, params=params, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            return []
        payload = resp.json()
        if not isinstance(payload, list) or len(payload) < 2:
            return []

        comments_data = payload[1].get("data", {}).get("children", [])
        comments: List[str] = []
        for item in comments_data:
            data = item.get("data", {})
            body = data.get("body", "")
            if int(data.get("score", 0)) > 3 and len(body) > 50:
                comments.append(body[:800])
        return comments
    except Exception:
        return []


def _destination_slug(destination: str) -> str:
    primary = destination.lower().split(",")[0].strip()
    return re.sub(r"[^a-z0-9]", "", primary)


async def scrape_reddit(destination: str, month: str, days: int) -> List[Dict]:
    destination_slug = _destination_slug(destination) or "travel"
    target_subreddits = [
        "travel",
        "solotravel",
        "backpacking",
        "digitalnomad",
        "shoestring",
        destination_slug,
    ]
    priority_queries = [
        f"{destination} hidden gems",
        f"{destination} travel tips {month}",
        f"{destination} itinerary {days} days",
        f"{destination} hotels budget stay",
        f"{destination} things to know before visiting",
        f"{destination} avoid tourist trap",
    ]

    all_posts: List[Dict] = []
    seen_urls = set()
    sem = asyncio.Semaphore(3)

    async with httpx.AsyncClient() as client:
        async def bounded(subreddit: str, query: str) -> List[Dict]:
            async with sem:
                await asyncio.sleep(0.5)
                return await search_subreddit(client, subreddit, query)

        tasks = [bounded(sub, q) for sub in target_subreddits for q in priority_queries]
        batches = await asyncio.gather(*tasks, return_exceptions=True)

        for batch in batches:
            if isinstance(batch, Exception):
                continue
            for post in batch:
                if post.get("url") in seen_urls:
                    continue
                seen_urls.add(post.get("url"))
                all_posts.append(post)

        all_posts.sort(key=lambda x: x.get("score", 0), reverse=True)
        all_posts = all_posts[:15]

        comment_tasks = [
            fetch_post_comments(client, post.get("permalink", ""))
            for post in all_posts[:8]
            if post.get("permalink")
        ]
        comment_results = await asyncio.gather(*comment_tasks, return_exceptions=True)

        for idx, comments in enumerate(comment_results):
            if idx >= len(all_posts):
                break
            if isinstance(comments, Exception):
                comments = []
            all_posts[idx]["comments"] = comments
            body = all_posts[idx].get("body", "")
            all_posts[idx]["full_text"] = body + "\n\n" + "\n".join(comments)

    return all_posts
