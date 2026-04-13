# WanderMind Backend

FastAPI backend for agentic travel itinerary generation.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill your keys:

```env
GROQ_API_KEY=...
TAVILY_API_KEY=...
EMBEDDING_MODEL=all-MiniLM-L6-v2
FAISS_INDEX_DIR=./faiss_indices
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/wandermind
JWT_SECRET_KEY=replace_with_a_long_random_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
```

## Run

```bash
uvicorn main:app --reload --port 8000
```

## Endpoints

- `GET /api/health`
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `DELETE /api/auth/me` (requires password in request body)
- `GET /api/itineraries`
- `GET /api/itineraries/{id}`
- `DELETE /api/itineraries/{id}`
- `DELETE /api/itineraries`
- `POST /api/generate-itinerary` (SSE stream, requires Bearer auth)

## PostgreSQL Quick Start

1. Create a database named `wandermind` in PostgreSQL.
2. Set `DATABASE_URL` in `.env` to your local credentials.
3. Start the API. Tables are auto-created on startup.
