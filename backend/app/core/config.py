import os
from pathlib import Path


class Settings:
    PROJECT_ROOT = Path(__file__).resolve().parents[2]
    API_V1_PREFIX = "/api/v1"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    AUTH_TOKEN_PREFIX = "dummy-token-for-"
    AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
    AWS_DYNAMODB_TABLE_INTERACTIONS = os.getenv(
        "AWS_DYNAMODB_TABLE_INTERACTIONS",
        "movie-recommendation-interactions",
    )
    AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE = os.getenv(
        "AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE",
        "movie-recommendation-cache",
    )
    RECOMMENDATION_CACHE_TTL_SECONDS = int(
        os.getenv("RECOMMENDATION_CACHE_TTL_SECONDS", "300")
    )


settings = Settings()
