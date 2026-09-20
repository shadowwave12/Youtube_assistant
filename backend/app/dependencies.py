"""FastAPI dependency providers."""

from functools import lru_cache

from .services.assistant_service import AssistantService


@lru_cache
def get_assistant_service() -> AssistantService:
    """Create the process-local application service on first use."""

    return AssistantService()