from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.routes import movies as movie_routes
from app.api.v1.routes import auth as auth_routes

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

app.include_router(auth_routes.router, prefix="/api/v1", tags=["auth"])
app.include_router(movie_routes.router, prefix="/api/v1", tags=["movies"])

@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
