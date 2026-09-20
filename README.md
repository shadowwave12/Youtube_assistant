# YouTube Assistant

A learning-oriented full-stack foundation for converting the existing Jupyter Notebook YouTube RAG chatbot into a production-oriented application.

## Repository structure

```text
Youtube_assistant/
|-- backend/       FastAPI API and future RAG services
|-- frontend/      React + JavaScript + Vite browser application
|-- notebooks/     Jupyter experiments and prototype investigations
|-- tests/         Automated unit and integration tests
|-- docs/          Implementation and operational documentation
|-- *.md           Product requirements and architecture decisions
```

### Directory purposes

- `backend/`: The server boundary. It will validate requests, coordinate application services, and keep provider credentials and AI orchestration out of the browser.
- `frontend/`: The browser boundary. It will contain the user interface and typed HTTP calls to the backend.
- `notebooks/`: A safe place for exploration and experiments while learning. Stable code should move into the backend rather than being imported from notebooks.
- `tests/`: The project-wide home for automated checks, organized into focused unit tests and broader integration tests.
- `docs/`: Implementation-facing notes that do not belong in source code. The numbered root documents remain the product and architecture reference.

## Simple architecture

```text
React frontend  ->  FastAPI backend  ->  future transcript, embedding, vector search, and LLM services
```

The backend owns future RAG behavior. The frontend only talks to the backend over HTTP/JSON. This keeps the first production shape understandable for a junior developer and leaves room to add services one at a time.

## Current status

This commit creates the project structure and application shells only. Transcript loading, chunking, embeddings, retrieval, LLM calls, authentication, and persistence are intentionally not implemented yet.

## Run locally

### Backend

```powershell
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend

```powershell
cd frontend
npm install
npm run dev
```
