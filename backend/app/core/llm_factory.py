from __future__ import annotations

from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from .config import LLMSettings


def create_llm(settings: LLMSettings | None = None) -> Any:
    resolved_settings = settings or LLMSettings.from_env()

    if resolved_settings.provider == "gemini":
        # LangChain adapter for Google's Gemini chat models.
        kwargs: dict[str, Any] = {
            "model": resolved_settings.model,
            "google_api_key": resolved_settings.api_key,
            "temperature": resolved_settings.temperature,
            "timeout": resolved_settings.timeout,
            "max_retries": resolved_settings.max_retries,
        }
        if resolved_settings.max_tokens is not None:
            kwargs["max_output_tokens"] = resolved_settings.max_tokens
        return ChatGoogleGenerativeAI(**kwargs)

    if resolved_settings.provider == "groq":
        # LangChain adapter for Groq-hosted chat models.
        kwargs = {
            "model_name": resolved_settings.model,
            "groq_api_key": resolved_settings.api_key,
            "temperature": resolved_settings.temperature,
            "request_timeout": resolved_settings.timeout,
            "max_retries": resolved_settings.max_retries,
        }
        if resolved_settings.max_tokens is not None:
            kwargs["max_tokens"] = resolved_settings.max_tokens
        return ChatGroq(**kwargs)

    raise ValueError(f"Unsupported LLM provider '{resolved_settings.provider}'.")