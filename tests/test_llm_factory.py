import pytest

from app.core.config import settings
from app.llm.factory import create_llm
from app.llm.providers.groq import GroqLLM


def test_create_llm_returns_groq():
    original_provider = settings.llm_provider

    try:
        settings.llm_provider = "groq"

        llm = create_llm()

        assert isinstance(llm, GroqLLM)
        assert llm.llm is not None

    finally:
        settings.llm_provider = original_provider


def test_create_llm_rejects_unsupported_provider():
    original_provider = settings.llm_provider

    try:
        settings.llm_provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported LLM provider"):
            create_llm()

    finally:
        settings.llm_provider = original_provider