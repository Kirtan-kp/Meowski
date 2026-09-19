from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    log_level : str = "INFO"

    llm_provider :str = "groq"
    llm_api_key : str = ""
    llm_model : str = "openai/gpt-oss-20b"

    qdrant_url : str = "http://localhost:6333"
    qdrant_collection : str = "cat_rag"
    embedding_model : str = "all-MiniLM-L6-v2"

    postgres_url : str = "postgresql+psycopg://cat_rag:cat_rag@localhost:5432/cat_rag"
    redis_url : str = "redis://localhost:6379/0"
    redis_cache_url : str = "redis://localhost:6379/0"
    redis_session_url : str = "redis://localhost:6379/1"

    retrieval_cache_version : int = 2

    llm_cache_ttl_seconds: int = 86400
    llm_cache_version: int = 1
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2

    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    upload_rate_limit_requests: int = 10
    upload_rate_limit_window_seconds: int = 60

    cleanup_interval_seconds: int = 3600

    model_config = SettingsConfigDict(env_file = ".env" , extra = "ignore")

settings = Settings()