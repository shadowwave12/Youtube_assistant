# Learning Guide

Follow this order to learn the project without trying to understand every library at once.

## 1. Basic Python

Learn functions, classes, imports, lists, dictionaries, exceptions, and type hints.

Open `backend/app/services/transcript_service.py` and `backend/app/api/schemas.py`. Notice the dataclasses, function arguments, return types, and `try/except` blocks.

## 2. FastAPI

Open `backend/app/main.py`, `backend/app/api/routes.py`, and `backend/app/api/schemas.py`. Learn how Python functions become HTTP endpoints and how Pydantic validates JSON.

## 3. APIs and JSON

Open `frontend/src/api/client.js` and trace `processVideo(...)` from JavaScript to `process_video(...)` in Python. Then trace `sendChat(...)` to `chat(...)`.

## 4. YouTube transcripts

Open `backend/app/services/transcript_service.py`. Learn how a URL becomes a video ID and how caption segments become Python data.

## 5. Chunking

Open `backend/app/services/chunking_service.py` and `tests/unit/test_chunking_service.py`. Learn why a long transcript is divided into smaller documents and why timing metadata is preserved.

## 6. Embeddings and vector search

Open `backend/app/services/retrieval_service.py` and `tests/unit/test_retrieval_service.py`. `HuggingFaceEmbeddings` converts text into vectors, and FAISS finds vectors close to the question vector. FAISS does not write answers.

## 7. Prompts

Open `backend/app/services/answer_service.py`. Read the actual `PromptTemplate`: it combines instructions, retrieved context, and the user's question.

## 8. LLM providers

Open `backend/app/core/config.py`, `backend/app/core/llm_factory.py`, and `backend/.env.example`. Learn the difference between a provider, a model, and an API key. The rest of the RAG pipeline does not change when switching Gemini and Groq.

## 9. Complete RAG flow

Read these files in order:

1. `backend/app/services/assistant_service.py`
2. `backend/app/services/transcript_service.py`
3. `backend/app/services/chunking_service.py`
4. `backend/app/services/retrieval_service.py`
5. `backend/app/services/answer_service.py`
6. `backend/app/api/routes.py`
7. `frontend/src/App.jsx`

The complete flow is:

```text
YouTube URL
 -> transcript
 -> chunks with metadata
 -> embeddings
 -> FAISS index
 -> retrieved chunks
 -> prompt
 -> LLM response
 -> cleaned answer
 -> JSON API response
 -> React Markdown rendering
```

## Small experiments

Make one change at a time and run the tests afterward:

- Change `chunk_size` in `ChunkingService` and observe `chunk_count`.
- Change `top_k` in `RetrievalService` and inspect returned sources.
- Add a supported transcript language to the process request.
- Add a unit test for another invalid YouTube URL.
- Add an API test for a provider error.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```