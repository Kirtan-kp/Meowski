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
    persona_prompt_version: int = 1
    llm_timeout_seconds: int = 30
    llm_max_retries: int = 2

    llm_provider_enabled: bool = True
    llm_daily_token_budget: int = 30000
    llm_rolling_token_budget: int = 8000
    llm_rolling_window_seconds: int = 3600
    llm_session_daily_token_budget: int = 10000
    llm_provider_daily_token_budget: int = 40000
    llm_max_request_tokens: int = 8192
    llm_max_output_tokens: int = 512
    llm_token_estimate_safety_factor: float = 1.2
    llm_concurrency_limit: int = 2
    llm_fallback_providers: str = ""
    llm_enabled_providers: str = "groq"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:3b"
    llm_provider_failure_threshold: int = 3
    llm_provider_circuit_cooldown_seconds: int = 30

    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    upload_rate_limit_requests: int = 10
    upload_rate_limit_window_seconds: int = 60
    session_rate_limit_requests: int = 20
    session_rate_limit_window_seconds: int = 60

    cleanup_interval_seconds: int = 3600

    metrics_token: str = ""
    max_upload_pages: int = 50
    max_upload_text_chars: int = 200000
    parser_timeout_seconds: int = 15
    parser_concurrency_limit: int = 2
    max_request_body_bytes: int = 256 * 1024
    max_upload_request_bytes: int = 12 * 1024 * 1024

    @property
    def llm_fallback_provider_list(self) -> list[str]:
        return [item.strip().lower() for item in self.llm_fallback_providers.split(",") if item.strip()]

    def is_provider_enabled(self, provider: str) -> bool:
        if provider == self.llm_provider and not self.llm_provider_enabled:
            return False
        enabled = {item.strip().lower() for item in self.llm_enabled_providers.split(",") if item.strip()}
        return provider.lower() in enabled

    model_config = SettingsConfigDict(env_file = ".env" , extra = "ignore")

settings = Settings()