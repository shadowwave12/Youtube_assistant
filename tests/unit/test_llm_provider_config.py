import pytest

from backend.app.core.config import LLMSettings
from backend.app.core.llm_factory import create_llm


def test_gemini_config_requires_supported_values(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("LLM_API_KEY", "gemini-key")

    settings = LLMSettings.from_env()

    assert settings.provider == "gemini"
    assert settings.model == "gemini-2.5-flash"
    assert settings.api_key == "gemini-key"


def test_groq_config_requires_supported_values(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("LLM_API_KEY", "groq-key")

    settings = LLMSettings.from_env()

    assert settings.provider == "groq"
    assert settings.model == "openai/gpt-oss-120b"
    assert settings.api_key == "groq-key"


def test_unsupported_provider_raises_configuration_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("LLM_MODEL", "gpt-4o-mini")
    monkeypatch.setenv("LLM_API_KEY", "test-key")

    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMSettings.from_env()


def test_missing_api_key_raises_configuration_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_MODEL", "gemini-2.5-flash")
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    with pytest.raises(ValueError, match="LLM_API_KEY"):
        LLMSettings.from_env()


def test_factory_uses_gemini_adapter_for_gemini_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("LLM_MODEL", "gemini-2.5-flash")
    monkeypatch.setenv("LLM_API_KEY", "gemini-key")

    model = create_llm(LLMSettings.from_env())

    assert model is not None
    assert getattr(model, "model", None) == "gemini-2.5-flash"


def test_factory_uses_groq_adapter_for_groq_provider(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "groq")
    monkeypatch.setenv("LLM_MODEL", "openai/gpt-oss-120b")
    monkeypatch.setenv("LLM_API_KEY", "groq-key")

    model = create_llm(LLMSettings.from_env())

    assert model is not None
    assert getattr(model, "model_name", None) == "openai/gpt-oss-120b"
