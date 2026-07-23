import os
from pathlib import Path


class Settings:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    API_V1_PREFIX = "/api/v1"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    AUTH_TOKEN_PREFIX = "dummy-token-for-"


settings = Settings()
