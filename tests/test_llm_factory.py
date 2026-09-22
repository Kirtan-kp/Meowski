import pytest
from app.core.config import settings
from app.llm.factory import create_llm, ProviderRouterLLM

def test_create_llm_builds_provider_router(monkeypatch):
    class FakeGroqLLM:
        @property
        def llm(self):
            return object()

    monkeypatch.setattr("app.llm.factory.GroqLLM", FakeGroqLLM)
    monkeypatch.setattr(settings, "llm_provider", "groq")
    monkeypatch.setattr(settings, "llm_enabled_providers", "groq")
    monkeypatch.setattr(settings, "llm_fallback_providers", "")

    llm = create_llm()

    assert isinstance(llm, ProviderRouterLLM)
    assert [name for name, _ in llm.providers] == ["groq"]


def test_create_llm_includes_explicit_ollama_fallback(monkeypatch):
    class FakeGroqLLM:
        @property
        def llm(self):
            return object()

    class FakeOllamaLLM:
        @property
        def llm(self):
            return object()

    monkeypatch.setattr("app.llm.factory.GroqLLM", FakeGroqLLM)
    monkeypatch.setattr("app.llm.factory.OllamaLLM", FakeOllamaLLM)
    monkeypatch.setattr(settings, "llm_provider", "groq")
    monkeypatch.setattr(settings, "llm_enabled_providers", "groq,ollama")
    monkeypatch.setattr(settings, "llm_fallback_providers", "ollama")

    llm = create_llm()

    assert [name for name, _ in llm.providers] == ["groq", "ollama"]


def test_create_llm_rejects_when_no_provider_is_enabled(monkeypatch):
    monkeypatch.setattr(settings, "llm_provider", "groq")
    monkeypatch.setattr(settings, "llm_provider_enabled", False)
    monkeypatch.setattr(settings, "llm_enabled_providers", "")
    monkeypatch.setattr(settings, "llm_fallback_providers", "")

    with pytest.raises(ValueError, match="No enabled zero-cost LLM providers"):
        create_llm()