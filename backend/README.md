# Backend

The FastAPI service will own the application API and all future AI/RAG orchestration.

## Layout

- `app/main.py`: FastAPI application entry point.
- `app/api/`: HTTP routes and request/response schemas.
- `app/services/`: Application use cases such as transcript ingestion and question answering.
- `app/models/`: Domain and API data models.
- `app/integrations/`: Adapters for YouTube transcripts, embeddings, vector search, and LLM providers.
- `app/core/`: Configuration, error handling, and shared infrastructure.

The first implemented service is `app/services/transcript_service.py`. It only validates a YouTube source and fetches typed transcript segments. RAG orchestration remains a later concern.

## API

- `GET /health`: Lightweight liveness check.
- `POST /api/videos/process`: Fetches a transcript, chunks it, creates an in-memory FAISS index, and returns the normalized video ID and chunk count.
- `POST /api/chat`: Retrieves context from a processed video and returns a grounded answer with source chunks.

The API routes are intentionally thin. `AssistantService` coordinates the existing transcript, chunking, retrieval, and answer services. Processed indexes are held in memory and are lost when the backend restarts.

## Environment variables

Keep local secrets in `backend/.env`. This file is ignored by Git and must never be committed or exposed to the frontend.

Copy `.env.example` to `.env` and set the provider-specific values before using `/api/chat`.

Recommended configuration:

```env
LLM_PROVIDER=gemini
LLM_MODEL=gemini-3.6-flash
LLM_API_KEY=your-gemini-api-key
```

Or for Groq:

```env
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
LLM_API_KEY=your-groq-api-key
```

## Local development

```powershell
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

For tests, install `requirements-dev.txt` instead of or in addition to the runtime requirements.
