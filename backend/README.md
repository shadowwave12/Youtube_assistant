# Backend

The FastAPI service will own the application API and all future AI/RAG orchestration.

## Layout

- `app/main.py`: FastAPI application entry point.
- `app/api/`: HTTP routes and request/response schemas.
- `app/services/`: Application use cases such as transcript ingestion and question answering.
- `app/models/`: Domain and API data models.
- `app/integrations/`: Adapters for YouTube transcripts, embeddings, vector search, and LLM providers.
- `app/core/`: Configuration, error handling, and shared infrastructure.

Only the entry point exists initially. The folders above are planned boundaries, not implemented business logic.

## Local development

```powershell
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```
