from __future__ import annotations

import os
import sys

from .config import LLMSettings
from .llm_factory import create_llm


def smoke_test(provider: str | None = None, model: str | None = None, api_key: str | None = None) -> str:
    if provider is not None:
        os.environ["LLM_PROVIDER"] = provider
    if model is not None:
        os.environ["LLM_MODEL"] = model
    if api_key is not None:
        os.environ["LLM_API_KEY"] = api_key

    settings = LLMSettings.from_env()
    llm = create_llm(settings)
    response = llm.invoke("Respond with exactly: LLM connection successful")

    text = str(response.content if hasattr(response, "content") else response)
    cleaned = text.strip()
    if cleaned != "LLM connection successful":
        raise RuntimeError(f"Provider smoke test failed for {settings.provider}: {cleaned!r}")
    print(f"Provider: {settings.provider}")
    print(f"Model: {settings.model}")
    return cleaned


if __name__ == "__main__":
    try:
        smoke_test()
    except Exception as error:
        print(f"LLM smoke test failed: {error}")
        sys.exit(1)