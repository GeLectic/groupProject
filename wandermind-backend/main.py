import asyncio
import json
from collections import Counter
from datetime import datetime, timezone
import re
from typing import Any, AsyncGenerator, Dict, List, Tuple

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from auth import create_access_token, get_current_user, hash_password, verify_password
from config import settings
from db import get_db, init_db
from generation.assembler import assemble_final_itinerary
from generation.itinerary_generator import ItineraryGenerator
from generation.pdf_exporter import build_itinerary_pdf
from models.db_models import StoredItinerary, User
from models.schemas import (
    AuthRequest,
    AuthResponse,
    DeleteAccountRequest,
    HealthResponse,
    ItineraryHistoryItem,
    MessageResponse,
    TripRequest,
    UserProfile,
)
from pipelines.community_pipeline import run_community_pipeline
from pipelines.data_combiner import combine_source_chunks
from pipelines.youtube_pipeline import run_youtube_pipeline
from processing.embedder import EmbeddingService
from processing.faiss_store import FAISSStore
from processing.text_processor import summarize_chunks
from query.query_processor import QueryProcessor
from utils.groq_client import GroqClient
from utils.tavily_client import TavilySearchClient
from verification.verifier import run_verification


app = FastAPI(title=settings.app_name, version=settings.app_version)


@app.on_event("startup")
def _on_startup() -> None:
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


groq_client = GroqClient()
tavily_client = TavilySearchClient()
embedding_service = EmbeddingService(model_name=settings.embedding_model)
faiss_store = FAISSStore()
query_processor = QueryProcessor(embedding_service=embedding_service)
itinerary_generator = ItineraryGenerator(groq_client=groq_client)


def _sse_payload(data: Dict[str, Any]) -> str:
    return f"data: {json.dumps(data, ensure_ascii=True)}\n\n"


def _source_stats_from_metadata(metadata_store: List[Dict[str, Any]]) -> Dict[str, Any]:
    youtube_map: Dict[str, Dict[str, Any]] = {}
    reddit_count = 0
    quora_count = 0

    for item in metadata_store:
        source = item.get("source")
        meta = item.get("metadata", {}) or {}

        if source == "youtube":
            url = meta.get("video_url") or meta.get("url")
            if not url:
                continue
            youtube_map[url] = {
                "title": meta.get("video_title", ""),
                "url": url,
                "channel_name": meta.get("channel_name", ""),
            }
        elif source == "reddit":
            reddit_count += 1
        elif source == "quora":
            quora_count += 1

    return {
        "youtube_videos_used": list(youtube_map.values()),
        "reddit_posts_used": reddit_count,
        "quora_pages_used": quora_count,
    }


def _requires_source_refresh(metadata_store: List[Dict[str, Any]]) -> bool:
    if not metadata_store:
        return True

    counts = Counter(item.get("source") for item in metadata_store)

    # Rebuild when cached corpus is too narrow; this avoids being stuck on earlier bad ingests.
    if len(metadata_store) < 12:
        return True
    if counts.get("youtube", 0) == 0:
        return True
    if counts.get("quora", 0) == 0:
        return True
    return False


def _db_token_from_itinerary_id(itinerary_id: int) -> str:
    return f"db-{itinerary_id}"


def _parse_generated_at(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    if isinstance(value, str) and value.strip():
        normalized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(normalized)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            pass

    return datetime.now(timezone.utc)


def _user_profile(user: User) -> UserProfile:
    return UserProfile(id=user.id, email=user.email, created_at=user.created_at)


def _persist_generated_itinerary(
    db: Session,
    user: User,
    payload: TripRequest,
    final_itinerary: Dict[str, Any],
) -> StoredItinerary:
    generated_at = _parse_generated_at(final_itinerary.get("generated_at"))

    itinerary_payload = dict(final_itinerary)
    itinerary_payload["generated_at"] = generated_at.isoformat()

    row = StoredItinerary(
        user_id=user.id,
        destination=payload.destination,
        days=payload.days,
        month=payload.month,
        budget_level=payload.budget_level,
        travel_style=payload.travel_style,
        itinerary_data=itinerary_payload,
        generated_at=generated_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _history_item_from_row(row: StoredItinerary) -> Dict[str, Any]:
    payload = dict(row.itinerary_data or {})
    payload["itinerary_id"] = row.id

    return {
        "id": _db_token_from_itinerary_id(row.id),
        "createdAt": row.created_at,
        "destination": row.destination,
        "days": row.days,
        "month": row.month,
        "budget_level": row.budget_level,
        "travel_style": row.travel_style,
        "data": payload,
    }


async def _tavily_enrichment(destination: str, month: str) -> Dict[str, str]:
    hotel_query_1 = f"{destination} budget hotels estimated cost per night"
    hotel_query_2 = f"{destination} luxury hotels estimated cost per night"
    events_query = f"{destination} local festivals events {month}"

    hotel_results_1 = await tavily_client.search(hotel_query_1, max_results=4)
    hotel_results_2 = await tavily_client.search(hotel_query_2, max_results=4)
    event_results = await tavily_client.search(events_query, max_results=3)

    def _to_text(rows: List[Dict[str, Any]]) -> str:
        lines = []
        for row in rows:
            title = row.get("title", "")
            content = row.get("content", "")
            url = row.get("url", "")
            lines.append(f"- {title}: {content[:280]} ({url})")
        return "\n".join(lines)

    return {
        "hotel_context": _to_text(hotel_results_1 + hotel_results_2),
        "events_context": _to_text(event_results),
    }


async def _build_or_load_knowledge_base(
    payload: TripRequest,
) -> Tuple[Any, List[Dict[str, Any]], Dict[str, Any], str]:
    destination_slug = faiss_store.destination_slug(payload.destination)
    cached_index, cached_metadata = faiss_store.load_index(destination_slug)

    if cached_index is not None and cached_metadata is not None and not _requires_source_refresh(cached_metadata):
        source_stats = _source_stats_from_metadata(cached_metadata)
        return cached_index, cached_metadata, source_stats, destination_slug

    youtube_result, community_result = await asyncio.gather(
        run_youtube_pipeline(
            destination=payload.destination,
            month=payload.month,
            tavily_client=tavily_client,
        ),
        run_community_pipeline(
            destination=payload.destination,
            month=payload.month,
            days=payload.days,
            groq_client=groq_client,
            tavily_client=tavily_client,
        ),
    )

    master_chunks = combine_source_chunks(
        youtube_chunks=youtube_result.get("chunks", []),
        community_chunks=community_result.get("chunks", []),
    )

    if not master_chunks and cached_index is not None and cached_metadata is not None:
        source_stats = _source_stats_from_metadata(cached_metadata)
        return cached_index, cached_metadata, source_stats, destination_slug

    summarized_chunks = await summarize_chunks(
        chunks=master_chunks,
        destination=payload.destination,
        groq_client=groq_client,
    )

    summary_texts = [chunk.get("summary", "") for chunk in summarized_chunks]
    embeddings = await embedding_service.embed_texts(summary_texts)

    index, metadata_store = faiss_store.build_and_save_index(
        destination_slug=destination_slug,
        chunks=summarized_chunks,
        embeddings=embeddings,
    )

    source_stats = {
        "youtube_videos_used": youtube_result.get("videos_used", []),
        "reddit_posts_used": community_result.get("reddit_posts_used", 0),
        "quora_pages_used": community_result.get("quora_pages_used", 0),
    }

    return index, metadata_store, source_stats, destination_slug


async def _stream_pipeline(payload: TripRequest, db: Session, current_user: User) -> AsyncGenerator[str, None]:
    tavily_client.reset_budget()
    notices: List[str] = []

    try:
        yield _sse_payload(
            {
                "type": "progress",
                "stage": 1,
                "label": "Collecting YouTube + community signals (first run may take 1-3 min)...",
                "progress": 10,
            }
        )

        build_task = asyncio.create_task(_build_or_load_knowledge_base(payload))
        stage_one_progress = 10
        while not build_task.done():
            await asyncio.sleep(6)
            if build_task.done():
                break

            stage_one_progress = min(stage_one_progress + 3, 38)
            yield _sse_payload(
                {
                    "type": "progress",
                    "stage": 1,
                    "label": "Collecting YouTube + community signals (first run may take 1-3 min)...",
                    "progress": stage_one_progress,
                }
            )

        index, metadata_store, source_stats, destination_slug = await build_task

        yield _sse_payload(
            {
                "type": "progress",
                "stage": 2,
                "label": "Mining Reddit & Quora...",
                "progress": 25,
            }
        )

        yield _sse_payload(
            {
                "type": "progress",
                "stage": 3,
                "label": "Building knowledge base...",
                "progress": 40,
            }
        )

        metadata_store, conflicts = await run_verification(
            destination=payload.destination,
            metadata_store=metadata_store,
            groq_client=groq_client,
        )

        faiss_store.save(destination_slug=destination_slug, index=index, metadata_store=metadata_store)

        yield _sse_payload(
            {
                "type": "progress",
                "stage": 4,
                "label": "Verifying information...",
                "progress": 60,
            }
        )

        contexts = await query_processor.retrieve_contexts(
            destination=payload.destination,
            month=payload.month,
            faiss_index=index,
            metadata_store=metadata_store,
        )
        notices.extend(contexts.get("notices", []))

        tavily_context = await _tavily_enrichment(payload.destination, payload.month)
        if tavily_context.get("hotel_context"):
            contexts["hotel_context"] = (
                contexts.get("hotel_context", "") + "\n\nAdditional web pricing context:\n" + tavily_context["hotel_context"]
            )
        if tavily_context.get("events_context"):
            contexts["places_context"] = (
                contexts.get("places_context", "") + "\n\nEvents context:\n" + tavily_context["events_context"]
            )

        yield _sse_payload(
            {
                "type": "progress",
                "stage": 5,
                "label": "Crafting your itinerary...",
                "progress": 80,
            }
        )

        generated = await itinerary_generator.generate(
            destination=payload.destination,
            days=payload.days,
            month=payload.month,
            budget_level=payload.budget_level,
            travel_style=payload.travel_style,
            places_context=contexts.get("places_context", ""),
            hotel_context=contexts.get("hotel_context", ""),
            community_context=contexts.get("community_context", ""),
            conflicts_list=conflicts,
        )

        final_itinerary = assemble_final_itinerary(
            destination=payload.destination,
            days=payload.days,
            month=payload.month,
            budget_level=payload.budget_level,
            travel_style=payload.travel_style,
            itinerary_data=generated.get("itinerary", []),
            hotels=generated.get("hotels", {}),
            tips=generated.get("tips", {}),
            data_sources=source_stats,
            notices=notices,
        )

        try:
            saved = _persist_generated_itinerary(db=db, user=current_user, payload=payload, final_itinerary=final_itinerary)
            final_itinerary["itinerary_id"] = saved.id
            final_itinerary["generated_at"] = _parse_generated_at(final_itinerary.get("generated_at")).isoformat()
        except Exception as exc:
            db.rollback()
            raise RuntimeError("Itinerary generated but could not be saved to the database.") from exc

        yield _sse_payload(
            {
                "type": "progress",
                "stage": 6,
                "label": "Done!",
                "progress": 100,
            }
        )
        yield _sse_payload({"type": "result", "data": final_itinerary})
    except Exception as exc:
        yield _sse_payload({"type": "error", "message": str(exc)})


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        groq=bool(settings.groq_api_key),
        tavily=bool(settings.tavily_api_key),
        faiss_ready=faiss_store.faiss_ready(),
    )


@app.post("/api/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(payload: AuthRequest, db: Session = Depends(get_db)) -> AuthResponse:
    normalized_email = payload.email.strip().lower()
    existing = db.query(User).filter(User.email == normalized_email).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered.")

    user = User(email=normalized_email, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(subject=str(user.id))
    return AuthResponse(access_token=token, user=_user_profile(user))


@app.post("/api/auth/login", response_model=AuthResponse)
def login(payload: AuthRequest, db: Session = Depends(get_db)) -> AuthResponse:
    normalized_email = payload.email.strip().lower()
    user = db.query(User).filter(User.email == normalized_email).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    token = create_access_token(subject=str(user.id))
    return AuthResponse(access_token=token, user=_user_profile(user))


@app.get("/api/auth/me", response_model=UserProfile)
def me(current_user: User = Depends(get_current_user)) -> UserProfile:
    return _user_profile(current_user)


@app.delete("/api/auth/me", response_model=MessageResponse)
def delete_account(
    payload: DeleteAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    if not verify_password(payload.password, current_user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password.")

    user_row = db.query(User).filter(User.id == current_user.id).first()
    if user_row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    (
        db.query(StoredItinerary)
        .filter(StoredItinerary.user_id == current_user.id)
        .delete(synchronize_session=False)
    )
    db.delete(user_row)
    db.commit()

    return MessageResponse(message="Account deleted.")


@app.get("/api/itineraries", response_model=List[ItineraryHistoryItem])
def list_itineraries(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> List[ItineraryHistoryItem]:
    rows = (
        db.query(StoredItinerary)
        .filter(StoredItinerary.user_id == current_user.id)
        .order_by(StoredItinerary.created_at.desc())
        .limit(100)
        .all()
    )
    return [_history_item_from_row(row) for row in rows]


@app.get("/api/itineraries/{itinerary_id}", response_model=Dict[str, Any])
def get_itinerary(
    itinerary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    row = (
        db.query(StoredItinerary)
        .filter(StoredItinerary.id == itinerary_id, StoredItinerary.user_id == current_user.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found.")

    payload = dict(row.itinerary_data or {})
    payload["itinerary_id"] = row.id
    return payload


@app.delete("/api/itineraries/{itinerary_id}", response_model=MessageResponse)
def delete_itinerary(
    itinerary_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MessageResponse:
    row = (
        db.query(StoredItinerary)
        .filter(StoredItinerary.id == itinerary_id, StoredItinerary.user_id == current_user.id)
        .first()
    )
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Itinerary not found.")

    db.delete(row)
    db.commit()
    return MessageResponse(message="Itinerary deleted.")


@app.delete("/api/itineraries", response_model=MessageResponse)
def clear_itineraries(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MessageResponse:
    (
        db.query(StoredItinerary)
        .filter(StoredItinerary.user_id == current_user.id)
        .delete(synchronize_session=False)
    )
    db.commit()
    return MessageResponse(message="All itineraries deleted.")


@app.post("/api/generate-itinerary")
async def generate_itinerary(
    payload: TripRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    return StreamingResponse(_stream_pipeline(payload, db, current_user), media_type="text/event-stream")


@app.post("/api/export-pdf")
async def export_itinerary_pdf(payload: Dict[str, Any]) -> Response:
    pdf_bytes = build_itinerary_pdf(payload)
    destination = str(payload.get("destination", "itinerary")).strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", destination).strip("-") or "itinerary"
    filename = f"wandermind-{slug}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
