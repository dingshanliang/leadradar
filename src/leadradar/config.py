from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    app_name: str = "LeadRadar"
    database_url: str = "sqlite:///./leadradar.db"
    redis_url: str = "redis://localhost:6379/0"

    llm_provider: str = "mock"
    llm_api_key: str | None = None
    llm_base_url: str | None = None
    llm_model: str = "mock-extractor"

    crawl_user_agent: str = "LeadRadarBot/0.1"
    crawl_requests_per_minute: int = 30
    crawl_timeout_seconds: int = 20

    allow_public_business_contacts: bool = True
    allow_personal_phone_collection: bool = False
    allow_automated_outbound_calls: bool = False

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
