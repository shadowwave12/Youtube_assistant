from __future__ import annotations

import os
from dataclasses import dataclass

SUPPORTED_PROVIDERS = {"gemini", "groq"}


@dataclass(frozen=True, slots=True)
class LLMSettings:
    provider: str
    model: str
    api_key: str
    temperature: float = 0.2
    timeout: float = 60.0
    max_retries: int = 2
    max_tokens: int | None = None

    @classmethod
    def from_env(cls, required: bool = True) -> "LLMSettings | None":
        provider = _read_env_value("LLM_PROVIDER")
        if not provider:
            if not required:
                return None
            raise ValueError("LLM_PROVIDER is required. Set it to 'gemini' or 'groq'.")
        provider = provider.strip().lower()
        if provider not in SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported LLM provider '{provider}'. Supported providers: {sorted(SUPPORTED_PROVIDERS)}")

        model = _read_env_value("LLM_MODEL")
        if not model:
            raise ValueError("LLM_MODEL is required for the selected provider.")
        model = model.strip()

        if provider == "gemini" and not model.lower().startswith("gemini-"):
            raise ValueError("Gemini model names must start with 'gemini-'.")
        if provider == "groq" and model.lower().startswith("gemini-"):
            raise ValueError("Groq model names must not use a Gemini model name.")

        api_key = _read_api_key(provider)
        if not api_key:
            raise ValueError(f"LLM_API_KEY is required for provider '{provider}'.")

        temperature = _read_float_env("LLM_TEMPERATURE", default=0.2)
        timeout = _read_float_env("LLM_TIMEOUT_SECONDS", default=60.0)
        max_retries = _read_int_env("LLM_MAX_RETRIES", default=2)
        max_tokens = _read_int_env("LLM_MAX_TOKENS", default=None)

        return cls(
            provider=provider,
            model=model,
            api_key=api_key,
            temperature=temperature,
            timeout=timeout,
            max_retries=max_retries,
            max_tokens=max_tokens,
        )


def _read_api_key(provider: str) -> str:
    candidates = ["LLM_API_KEY"]
    if provider == "gemini":
        candidates.extend(["GEMINI_API_KEY", "GOOGLE_API_KEY"])
    elif provider == "groq":
        candidates.extend(["GROQ_API_KEY", "GROQ_API-KEY"])

    for key in candidates:
        value = _read_env_value(key)
        if value:
            return value
    return ""


def _read_env_value(key: str) -> str:
    value = os.getenv(key)
    if value is None:
        return ""
    return value.strip()


def _read_float_env(key: str, default: float) -> float:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError as error:
        raise ValueError(f"Environment variable '{key}' must be a float.") from error


def _read_int_env(key: str, default: int | None) -> int | None:
    raw = os.getenv(key)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as error:
        raise ValueError(f"Environment variable '{key}' must be an integer.") from error