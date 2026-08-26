from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    log_level : str = "INFO"

    llm_provider :str = "groq"
    llm_api_key : str = ""
    llm_model : str = "openai/gpt-oss-20b"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "cat_rag"
    embedding_model: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra = "ignore"
    )

settings = Settings()