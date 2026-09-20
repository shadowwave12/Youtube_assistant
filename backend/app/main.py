"""FastAPI application entry point."""

from fastapi import FastAPI

from .api.routes import router

app = FastAPI(
    title="YouTube Assistant API",
    version="0.1.0",
    description="API for processing YouTube transcripts and asking grounded questions.",
)

app.include_router(router)


@app.get("/health", tags=["system"], summary="Check API health")
def health() -> dict[str, str]:
    """Return a lightweight liveness response."""

    return {"status": "ok"}
