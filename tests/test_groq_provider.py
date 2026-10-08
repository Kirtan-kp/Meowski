import pytest

from app.core.config import settings
import app.llm.providers.groq as groq


@pytest.fixture
def captured(monkeypatch):
    seen = {}
    monkeypatch.setattr(groq, "ChatGroq", lambda **kwargs: seen.update(kwargs) or object())
    monkeypatch.setattr(settings, "llm_api_key", "k")
    return seen


def test_gpt_oss_defaults_to_low_reasoning_effort(captured, monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "openai/gpt-oss-20b")
    monkeypatch.setattr(settings, "llm_reasoning_effort", "")
    groq.GroqLLM()
    assert captured["reasoning_effort"] == "low" and captured["max_tokens"] == settings.llm_max_output_tokens


def test_other_models_get_no_reasoning_parameter(captured, monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "llama-3.3-70b-versatile")
    monkeypatch.setattr(settings, "llm_reasoning_effort", "")
    groq.GroqLLM()
    assert "reasoning_effort" not in captured


def test_explicit_effort_is_respected(captured, monkeypatch):
    monkeypatch.setattr(settings, "llm_model", "qwen/qwen3-32b")
    monkeypatch.setattr(settings, "llm_reasoning_effort", "medium")
    groq.GroqLLM()
    assert captured["reasoning_effort"] == "medium"
