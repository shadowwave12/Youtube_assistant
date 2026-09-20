"""FastAPI application entry point.

Business services and API routes will be added in later implementation phases.
"""

from fastapi import FastAPI

app = FastAPI(
    title="YouTube Assistant API",
    version="0.1.0",
    description="Backend shell for the YouTube RAG assistant.",
)
