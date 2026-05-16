from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "AInewsroom"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ainewsroom:ainewsroom@db:5432/ainewsroom"
    DATABASE_ECHO: bool = False

    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # Anthropic Claude
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-opus-4-6"
    CLAUDE_FAST_MODEL: str = "claude-haiku-4-5-20251001"

    # Security
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    ALGORITHM: str = "HS256"

    # Feed sources (RSS/API)
    RSS_POLL_INTERVAL_SECONDS: int = 60
    MAX_FEED_ITEMS: int = 200

    # Copyright
    COPYRIGHT_SIMILARITY_THRESHOLD: float = 0.30  # 30% = warning
    COPYRIGHT_DANGER_THRESHOLD: float = 0.60  # 60% = danger

    # TTS - ElevenLabs (optional)
    ELEVENLABS_API_KEY: str = ""
    ELEVENLABS_BASE_URL: str = "https://api.elevenlabs.io/v1"

    # API Key auth (leave empty to disable in dev mode)
    API_KEY: str = ""

    # Token cost tracking budget (0 = no limit)
    MONTHLY_TOKEN_BUDGET: int = 0

    # Social publishing (optional — leave empty to disable each platform)
    LINE_NOTIFY_TOKEN: str = ""
    FACEBOOK_PAGE_ID: str = ""
    FACEBOOK_PAGE_ACCESS_TOKEN: str = ""
    TWITTER_BEARER_TOKEN: str = ""
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_SECRET: str = ""

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
