import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BACKEND_DIR = Path(__file__).resolve().parent

# Prefer backend-local .env, then fall back to parent discovery.
load_dotenv(BACKEND_DIR / ".env")
load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_name: str = "WanderMind API"
    app_version: str = "1.0.0"

    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    tavily_api_key: str = os.getenv("TAVILY_API_KEY", "")

    groq_model: str = "llama-3.3-70b-versatile"
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    faiss_index_dir: str = os.getenv("FAISS_INDEX_DIR", "./faiss_indices")
    max_groq_output_tokens: int = 1500
    max_groq_input_chars: int = 1500

    tavily_max_calls_per_trip: int = 8
    max_llm_summary_chunks: int = int(os.getenv("MAX_LLM_SUMMARY_CHUNKS", "12"))
    max_community_chunks_for_extraction: int = int(os.getenv("MAX_COMMUNITY_CHUNKS_FOR_EXTRACTION", "12"))

    database_url: str = os.getenv("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/wandermind")
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "10080"))

    sse_progress_events: tuple = (
        {"stage": 1, "label": "Fetching YouTube vlogs...", "progress": 10},
        {"stage": 2, "label": "Mining Reddit & Quora...", "progress": 25},
        {"stage": 3, "label": "Building knowledge base...", "progress": 40},
        {"stage": 4, "label": "Verifying information...", "progress": 60},
        {"stage": 5, "label": "Crafting your itinerary...", "progress": 80},
        {"stage": 6, "label": "Done!", "progress": 100},
    )

    @property
    def faiss_base_path(self) -> Path:
        configured = Path(self.faiss_index_dir)
        if configured.is_absolute():
            return configured
        return (BACKEND_DIR / configured).resolve()


settings = Settings()
