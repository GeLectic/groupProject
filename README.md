# AI Evidence-Based Tour Planner

This project is a full-stack AI tour planning system that creates reliable, personalized itineraries from real-world travel signals. It combines community and web evidence (YouTube, Reddit, Quora, web search) with retrieval and verification before generating the final plan.

## 1) Use Cases

- Build complete day-wise itineraries for a destination using trip preferences.
- Get hotel suggestions by budget level with supporting context.
- Include practical travel details such as hidden gems, warnings, food tips, and packing guidance.
- Save generated itineraries per user account for later access.
- Export generated itinerary to PDF for sharing or submission.

## 2) What Is Used

### Backend

- FastAPI (REST + SSE)
- SQLAlchemy + PostgreSQL (auth and itinerary persistence)
- JWT auth with password hashing (python-jose + bcrypt)
- FAISS + sentence-transformers (retrieval index)
- Groq API (summarization and itinerary generation)
- Tavily search (web enrichment)
- YouTube transcript/search + Reddit/Quora scraping pipelines

### Frontend

- React + Vite
- Tailwind CSS
- Framer Motion
- Zustand
- Axios

## 3) Project Structure

```text
MajorProject/
  README.md
  requirements.txt
  docs/
    sample-output.svg
    wandermind-system-design-workflow.svg
    wandermind-interview-architecture.svg
  wandermind-backend/
    main.py
    auth.py
    db.py
    config.py
    requirements.txt
    generation/
    pipelines/
    processing/
    query/
    verification/
    models/
    utils/
  wandermind-frontend/
    package.json
    src/
```

## 4) Architecture Discussion

### High-level Architecture

1. React frontend collects user input and authenticates users.
2. FastAPI backend orchestrates data ingestion, retrieval, verification, and generation.
3. External sources provide destination evidence:
   - YouTube transcripts/videos
   - Reddit public JSON
   - Quora pages
   - Tavily web search context
4. Processing layer summarizes chunks, embeds them, and stores vectors in FAISS.
5. Query layer retrieves the best context chunks for the requested destination/month.
6. Verification layer identifies conflicts and improves reliability.
7. Generation layer creates final itinerary JSON and stores it in PostgreSQL.
8. Backend streams progress and final result via Server-Sent Events (SSE).

### Request Flow (Generate Itinerary)

```text
Frontend -> POST /api/generate-itinerary (Bearer token)
         -> Backend starts SSE stream
         -> Build/load FAISS knowledge base for destination
         -> Verify evidence and retrieve context
         -> Generate itinerary + hotels + tips
         -> Persist final output in PostgreSQL
         -> Stream final result to frontend
```

### Architecture Diagrams

- Full system/workflow: docs/wandermind-system-design-workflow.svg
- Interview-style architecture: docs/wandermind-interview-architecture.svg

## 5) Setup Guide

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm 9+
- PostgreSQL 14+ (or compatible)

## Step A: Backend Setup

```bash
cd wandermind-backend
python -m venv .venv
```

Activate environment:

- Windows PowerShell: `.venv\Scripts\Activate.ps1`
- macOS/Linux: `source .venv/bin/activate`

Install dependencies:

```bash
pip install -r ../requirements.txt
```

Create environment file:

```bash
copy .env.example .env
```

Set values in `.env`:

```env
GROQ_API_KEY=your_groq_api_key
TAVILY_API_KEY=your_tavily_api_key
EMBEDDING_MODEL=all-MiniLM-L6-v2
FAISS_INDEX_DIR=./faiss_indices
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/wandermind
JWT_SECRET_KEY=replace_with_a_strong_secret
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
MAX_LLM_SUMMARY_CHUNKS=12
MAX_COMMUNITY_CHUNKS_FOR_EXTRACTION=12
```

Run backend:

```bash
uvicorn main:app --reload --port 8000
```

## Step B: Frontend Setup

```bash
cd ../wandermind-frontend
npm install
copy .env.example .env
npm run dev
```

Frontend default URL: http://localhost:5173

## Step C: Quick Health Check

```bash
curl http://localhost:8000/api/health
```

Expected response includes flags for Groq, Tavily, and FAISS readiness.

## 6) API Summary

### Authentication

- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me
- DELETE /api/auth/me

### Itinerary History

- GET /api/itineraries
- GET /api/itineraries/{itinerary_id}
- DELETE /api/itineraries/{itinerary_id}
- DELETE /api/itineraries

### Generation and Export

- POST /api/generate-itinerary (SSE stream, requires auth)
- POST /api/export-pdf

### Example Generate Payload

```json
{
  "destination": "Manali, Himachal Pradesh",
  "days": 7,
  "month": "October",
  "budget_level": "mid-range",
  "travel_style": "adventure"
}
```

SSE event types:

- {"type":"progress", ...}
- {"type":"result", "data": {...}}
- {"type":"error", "message": "..."}

## 7) Notes

- First run for a new destination may take longer because source ingestion, summarization, and FAISS index build happen together.
- Repeat runs for the same destination are faster due to destination index reuse.
- Ensure PostgreSQL is running before starting backend.
