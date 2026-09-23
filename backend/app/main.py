"""FastAPI application entry point."""

from pathlib import Path
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .api.routes import router
from .core.config import LLMSettings

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

logger = logging.getLogger(__name__)

local_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]
production_origins = ["https://yt-assistant-omega.vercel.app"]
configured_frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")
allowed_origins = local_origins + production_origins
if configured_frontend_url and configured_frontend_url not in allowed_origins:
    allowed_origins.append(configured_frontend_url)

app = FastAPI(
    title="YouTube Assistant API",
    version="0.1.0",
    description="API for processing YouTube transcripts and asking grounded questions.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=production_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers = ["*"]
)

app.include_router(router)


@app.on_event("startup")
def validate_llm_configuration() -> None:
    """Validate provider config without invoking a paid model call during startup."""

    settings = LLMSettings.from_env(required=False)
    if settings:
        logger.info("[LLM] Provider configured provider=%s model=%s", settings.provider, settings.model)
    else:
        logger.warning("[LLM] Provider is not configured")


@app.get("/health", tags=["system"], summary="Check API health")
def health() -> dict[str, object]:
    """Return liveness and redacted provider configuration state."""

    settings = LLMSettings.from_env(required=False)
    return {
        "status": "ok",
        "llm": {
            "provider": settings.provider if settings else None,
            "model": settings.model if settings else None,
            "configured": settings is not None,
        },
    }
