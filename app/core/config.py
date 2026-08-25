from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_env: str = "development"
    log_level : str = "INFO"

    llm_provider :str = "groq"
    llm_api_key : str = ""

    model_config = SettingsConfigDict(
        env_file = ".env",
        extra = "ignore"
    )

settings = Settings()