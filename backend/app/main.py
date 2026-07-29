import logging
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import settings


def configure_logging() -> None:
    logging.basicConfig(
        level=getattr(logging, settings.logging.level),
        format=settings.logging.format,
        datefmt=settings.logging.date_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )


configure_logging()
logger = logging.getLogger("movie_recommendation")

from app.api.v1.routes import auth as auth_routes
from app.api.v1.routes import interactions as interaction_routes
from app.api.v1.routes import movies as movie_routes
from app.container import jwt_service
from app.middleware.authentication import JWTAuthenticationMiddleware

app = FastAPI(
    title=settings.application.title,
    version=settings.application.version,
    description=settings.application.description,
    debug=settings.application.debug,
    docs_url=settings.api.docs_path,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.api.cors_allowed_origins),
    allow_credentials=settings.api.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    JWTAuthenticationMiddleware,
    jwt_service=jwt_service,
)

app.include_router(
    auth_routes.router,
    prefix=settings.api.prefix,
    tags=["auth"],
)
app.include_router(
    movie_routes.router,
    prefix=settings.api.prefix,
    tags=["movies"],
)
app.include_router(
    interaction_routes.router,
    prefix=settings.api.prefix,
    tags=["interactions"],
)


@app.get(settings.api.health_path)
def health_check() -> dict[str, str]:
    logger.info("Health check requested")
    return {"status": "ok"}
