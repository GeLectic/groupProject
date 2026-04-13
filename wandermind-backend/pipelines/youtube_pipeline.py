import asyncio
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from langchain_text_splitters import RecursiveCharacterTextSplitter
from youtube_transcript_api import YouTubeTranscriptApi
from youtubesearchpython import VideosSearch

from config import settings
from utils.tavily_client import TavilySearchClient


def _parse_view_count(raw: str) -> int:
    if not raw:
        return 0
    lowered = raw.lower().replace("views", "").strip()
    lowered = lowered.replace(",", "")

    multiplier = 1
    if lowered.endswith("k"):
        multiplier = 1_000
        lowered = lowered[:-1]
    elif lowered.endswith("m"):
        multiplier = 1_000_000
        lowered = lowered[:-1]

    try:
        return int(float(lowered) * multiplier)
    except ValueError:
        match = re.search(r"(\d+)", lowered)
        return int(match.group(1)) if match else 0


def _is_recent_publish(published_text: str, max_years: int = 2) -> bool:
    if not published_text:
        return False
    text = published_text.lower()
    match = re.search(r"(\d+)\s+(year|month|week|day)", text)
    if not match:
        return False

    value = int(match.group(1))
    unit = match.group(2)

    if unit == "year":
        return value <= max_years
    if unit == "month":
        return value <= max_years * 12
    if unit == "week":
        return value <= max_years * 52
    return value <= max_years * 365


def _video_score(video: Dict[str, Any]) -> float:
    views = int(video.get("view_count", 0))
    published = str(video.get("publish_date", ""))

    score = 0.0
    if views > 10_000:
        score += 2.0
    score += min(views / 100_000, 20)

    if _is_recent_publish(published, max_years=2):
        score += 10.0

    return score


def _normalize_video_result(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    video_id = item.get("id")
    if not video_id:
        return None

    view_meta = item.get("viewCount") or {}
    view_text = view_meta.get("text") or view_meta.get("short") or ""
    channel = item.get("channel") or {}

    return {
        "video_id": video_id,
        "title": item.get("title", ""),
        "channel_name": channel.get("name", ""),
        "view_count": _parse_view_count(view_text),
        "publish_date": item.get("publishedTime", ""),
        "url": item.get("link", f"https://www.youtube.com/watch?v={video_id}"),
    }


async def _search_youtube_query(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    def _run() -> List[Dict[str, Any]]:
        search = VideosSearch(query, limit=limit)
        payload = search.result() or {}
        return payload.get("result", [])

    try:
        items = await asyncio.wait_for(asyncio.to_thread(_run), timeout=12)
    except Exception:
        return []

    normalized = []
    for item in items:
        video = _normalize_video_result(item)
        if video:
            normalized.append(video)
    return normalized


def _extract_video_id_from_url(url: str) -> Optional[str]:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()

    if "youtube.com" in host:
        params = parse_qs(parsed.query)
        if params.get("v"):
            return params["v"][0]
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2 and parts[0] in {"shorts", "embed"}:
            return parts[1]
    if "youtu.be" in host:
        path = parsed.path.strip("/")
        return path or None
    return None


async def _augment_with_tavily_youtube_links(
    destination: str,
    tavily_client: Optional[TavilySearchClient],
) -> List[Dict[str, Any]]:
    if not tavily_client:
        return []

    queries = [
        f"site:youtube.com {destination} vlog",
        f"site:youtube.com {destination} travel guide english",
    ]

    results: List[Dict[str, Any]] = []
    for query in queries:
        tavily_results = await tavily_client.search(query=query, max_results=10)
        for item in tavily_results:
            url = item.get("url", "")
            video_id = _extract_video_id_from_url(url)
            if not video_id:
                continue
            results.append(
                {
                    "video_id": video_id,
                    "title": item.get("title", "Tavily YouTube result"),
                    "channel_name": "Unknown",
                    "view_count": 0,
                    "publish_date": "",
                    "url": url,
                }
            )
    return results


async def search_top_videos(
    destination: str,
    month: str,
    tavily_client: Optional[TavilySearchClient] = None,
) -> List[Dict[str, Any]]:
    queries = [
        f"{destination} travel vlog {month}",
        f"{destination} hidden places travel guide",
        f"{destination} travel tips locals",
    ]

    collected: List[Dict[str, Any]] = []
    seen = set()

    for query in queries:
        videos = await _search_youtube_query(query, limit=5)
        if not videos:
            videos = await _search_youtube_query(destination, limit=5)

        for video in videos:
            vid = video["video_id"]
            if vid in seen:
                continue
            seen.add(vid)
            collected.append(video)

    if tavily_client and len(collected) < 8:
        tavily_videos = await _augment_with_tavily_youtube_links(destination, tavily_client)
        for video in tavily_videos:
            vid = video["video_id"]
            if vid in seen:
                continue
            seen.add(vid)
            collected.append(video)

    collected.sort(key=_video_score, reverse=True)
    return collected[:8]


async def fetch_transcript_text(video_id: str) -> Optional[str]:
    def _run() -> Optional[str]:
        # Support both old (class static) and newer (instance fetch) package APIs.
        transcript_rows: List[Dict[str, Any]] = []

        if hasattr(YouTubeTranscriptApi, "get_transcript"):
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
            if isinstance(transcript, list):
                transcript_rows = [row for row in transcript if isinstance(row, dict)]
        else:
            api = YouTubeTranscriptApi()
            fetched = api.fetch(video_id, languages=["en"])
            if hasattr(fetched, "to_raw_data"):
                transcript_rows = fetched.to_raw_data()
            elif isinstance(fetched, list):
                transcript_rows = [row for row in fetched if isinstance(row, dict)]
            else:
                transcript_rows = [
                    {
                        "text": getattr(row, "text", ""),
                        "start": getattr(row, "start", 0),
                        "duration": getattr(row, "duration", 0),
                    }
                    for row in fetched
                ]

        return " ".join(item.get("text", "") for item in transcript_rows if item.get("text"))

    try:
        transcript_text = await asyncio.wait_for(asyncio.to_thread(_run), timeout=18)
        if transcript_text and len(transcript_text.split()) > 40:
            return transcript_text
        return None
    except Exception as exc:
        # Skip known transcript issues and continue pipeline.
        name = exc.__class__.__name__
        if name in {"TranscriptsDisabled", "NoTranscriptFound"}:
            return None
        return None


async def run_youtube_pipeline(
    destination: str,
    month: str,
    tavily_client: Optional[TavilySearchClient] = None,
) -> Dict[str, Any]:
    videos = await search_top_videos(destination, month, tavily_client=tavily_client)

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)
    chunks: List[Dict[str, Any]] = []
    videos_used: List[Dict[str, Any]] = []

    sem = asyncio.Semaphore(4)

    async def _bounded_fetch(video: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[str]]:
        async with sem:
            transcript_text = await fetch_transcript_text(video["video_id"])
            return video, transcript_text

    transcript_results = await asyncio.gather(*[_bounded_fetch(v) for v in videos], return_exceptions=True)

    for result in transcript_results:
        if isinstance(result, Exception):
            continue
        video, transcript = result
        if not transcript:
            continue

        videos_used.append(video)
        for chunk in splitter.split_text(transcript):
            chunks.append(
                {
                    "text": chunk,
                    "extracted": None,
                    "source": "youtube",
                    "metadata": {
                        "video_title": video.get("title", ""),
                        "channel_name": video.get("channel_name", ""),
                        "video_url": video.get("url", ""),
                        "publish_date": video.get("publish_date", ""),
                        "view_count": video.get("view_count", 0),
                    },
                }
            )

    # Graceful fallback for environments where transcript retrieval is blocked.
    if not chunks and videos:
        for video in videos[:3]:
            videos_used.append(video)
            fallback_text = (
                f"YouTube travel reference for {destination} ({month}). "
                f"Video: {video.get('title', 'Unknown title')}. "
                f"Channel: {video.get('channel_name', 'Unknown channel')}. "
                "Transcript unavailable for this video in the current environment. "
                "Use this only as weak supporting context and verify locally."
            )
            chunks.append(
                {
                    "text": fallback_text,
                    "extracted": None,
                    "source": "youtube",
                    "metadata": {
                        "video_title": video.get("title", ""),
                        "channel_name": video.get("channel_name", ""),
                        "video_url": video.get("url", ""),
                        "publish_date": video.get("publish_date", ""),
                        "view_count": video.get("view_count", 0),
                        "transcript_unavailable": True,
                    },
                }
            )

    return {"chunks": chunks, "videos_used": videos_used}
