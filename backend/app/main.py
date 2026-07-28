import logging
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.api.v1.routes import movies as movie_routes
from app.api.v1.routes import auth as auth_routes
from app.api.v1.routes import interactions as interaction_routes
from app.container import jwt_service
from app.middleware.authentication import JWTAuthenticationMiddleware


def configure_logging() -> None:
    log_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_name, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


configure_logging()
logger = logging.getLogger("movie_recommendation")

app = FastAPI(
    title="Movie Recommendation API",
    version="1.0.0",
    description="Production-ready FastAPI backend for movie browsing and authentication",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    JWTAuthenticationMiddleware,
    jwt_service=jwt_service,
)

app.include_router(auth_routes.router, prefix="/api/v1", tags=["auth"])
app.include_router(movie_routes.router, prefix="/api/v1", tags=["movies"])
app.include_router(interaction_routes.router, prefix="/api/v1", tags=["interactions"])


@app.get("/health")
def health_check() -> dict[str, str]:
    logger.info("Health check requested")
    return {"status": "ok"}
