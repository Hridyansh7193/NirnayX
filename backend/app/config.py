from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # Application
    APP_NAME: str = "NirnayX"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nirnayx"
    DATABASE_URL_SYNC: str = "postgresql://postgres:postgres@localhost:5432/nirnayx"

    # Infrastructure (Queue/Cache/Stream)
    REDIS_URL: str = "redis://localhost:6379/0" # Redis queue URL
    CACHE_URL: str = "redis://localhost:6380/0" # Redis Cache URL
    REDPANDA_URL: str = "localhost:9092"

    # JWT Auth
    SECRET_KEY: str = "nirnayx-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:3001"]

    # RL Engine & Architecture Constraints
    RL_BATCH_INTERVAL_HOURS: int = 24  # Batch processing vs real-time
    RL_MAX_SHIFT_PER_EPOCH: float = 0.05
    RL_LEARNING_RATE: float = 0.01  # Backward compatibility for rl_engine.py
    RL_MIN_FEEDBACK_CYCLES: int = 5
    MAX_TOKENS_PER_DOMAIN: int = 4000
    
    # Agent Defaults
    DEFAULT_AGENT_COUNT: int = 5
    MAX_AGENT_COUNT: int = 15
    MIN_AGENT_COUNT: int = 3

    # Aggregation
    LOW_CONSENSUS_THRESHOLD: float = 0.6

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()
