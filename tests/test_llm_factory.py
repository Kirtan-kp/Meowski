import pytest
from app.core.config import settings
from app.llm.factory import create_llm

def test_create_llm_returns_groq(monkeypatch):

    class FakeGroqLLM:
        pass

    monkeypatch.setattr(
        "app.llm.factory.GroqLLM",
        FakeGroqLLM,
    )

    settings.llm_provider = "groq"

    llm = create_llm()

    assert isinstance(llm, FakeGroqLLM)

def test_create_llm_rejects_unsupported_provider(monkeypatch):

    monkeypatch.setattr(
        settings,
        "llm_provider",
        "unsupported",
    )

    with pytest.raises(
        ValueError,
        match="Unsupported LLM provider",
    ):
        create_llm()