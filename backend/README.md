# Backend Guide

The backend is a small FastAPI application that owns the YouTube RAG pipeline. The browser sends JSON requests; Python retrieves transcript information and asks the configured LLM for a grounded answer.

## Start Here

Read these files in order:

1. `app/main.py` - creates FastAPI and exposes `/health`.
2. `app/api/routes.py` - shows the two application endpoints.
3. `app/services/assistant_service.py` - shows the complete workflow.
4. `app/services/transcript_service.py` - gets the transcript.
5. `app/services/chunking_service.py` - creates searchable chunks.
6. `app/services/retrieval_service.py` - creates embeddings and searches FAISS.
7. `app/services/answer_service.py` - creates the prompt and calls the LLM.
8. `app/core/llm_factory.py` - selects Gemini or Groq.

## Endpoints

- `GET /health`: returns server status and redacted provider/model configuration.
- `POST /api/videos/process`: fetches a transcript, chunks it, creates embeddings, and stores a FAISS index in memory.
- `POST /api/chat`: retrieves related chunks and returns a grounded answer plus sources.

The processed index is intentionally process-local. Restarting FastAPI means the video must be processed again.

## Environment

Create `backend/.env` from `.env.example`:

```env
LLM_PROVIDER=groq
LLM_MODEL=openai/gpt-oss-120b
LLM_API_KEY=your-groq-api-key
```

For Gemini, use `LLM_PROVIDER=gemini`, a supported Gemini model, and a Gemini key. The provider-specific factory is the only place that chooses `ChatGoogleGenerativeAI` or `ChatGroq`.

## Run and test

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

From the repository root:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```
