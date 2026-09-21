"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .api.routes import router

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(
    title="YouTube Assistant API",
    version="0.1.0",
    description="API for processing YouTube transcripts and asking grounded questions.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(router)


@app.get("/health", tags=["system"], summary="Check API health")
def health() -> dict[str, str]:
    """Return a lightweight liveness response."""

    return {"status": "ok"}
