import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    aria_model: str = "claude-haiku-4-5-20251001"
    fallback_model: str = "claude-haiku-4-5-20251001"

    # Phase 3 — RAG
    openai_api_key: str = ""
    chroma_path: str = os.path.join(os.path.dirname(__file__), "..", "chroma_data")

    # Phase 4 — Auth (override JWT_SECRET in .env for production)
    jwt_secret: str = "aria-dev-secret-change-in-prod-xx"  # ≥32 bytes required
    jwt_expire_minutes: int = 480  # 8 hours for dev convenience

    # Phase 4 — SQLite usage DB
    db_path: str = os.path.join(os.path.dirname(__file__), "..", "aria_usage.db")

    # Phase 4 — Rate limiting: token bucket capacity and refill per second
    # Defaults give ~10 calls/min burst of 5.
    rate_limit_capacity: float = 5.0
    rate_limit_refill_rate: float = 0.167  # tokens/sec ≈ 10/min

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
