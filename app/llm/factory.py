from app.core.config import settings
from app.llm.base import BaseLLM
from app.llm.providers.groq import GroqLLM

def create_llm() -> BaseLLM:

    if settings.llm_provider == "groq":
        return GroqLLM()

    raise ValueError(f"Unsupported LLM provider: {settings.llm_provider}")