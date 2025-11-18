# app/core/config.py
import os
from typing import List

# Using standard dict instead of Pydantic's BaseSettings
class Settings:
    # API Settings
    API_PREFIX: str = "/api/v1"

    # Codeforces API Settings
    CODEFORCES_API_KEY: str = os.getenv("CODEFORCES_API_KEY", "b75b7326b9d66839baf9ba6e86c0801fa6227127")
    CODEFORCES_API_SECRET: str = os.getenv("CODEFORCES_API_SECRET", "0029c7b2b79ebc7c729907f22b5c127c8f2ad6c7")

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

settings = Settings()