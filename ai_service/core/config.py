import os
from typing import List


class Settings:
    # API Settings
    API_PREFIX: str = "/api/v1"

    # Google Gemini API Settings
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Service Settings
    DEFAULT_MAX_RECOMMENDATIONS: int = 20


settings = Settings()
