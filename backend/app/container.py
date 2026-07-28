"""Application composition root for security, services, and repositories."""

from app.core.config import settings
from app.core.security import JWTService, PasswordHasher
from app.repositories.movies_repository import MoviesRepository
from app.repositories.recommendation_cache_repository import (
    RecommendationCacheRepository,
)
from app.repositories.users_repository import UsersRepository
from app.services.auth_service import AuthService
from app.services.mock_recommendation_provider import MockRecommendationProvider
from app.services.movie_service import MovieService
from app.services.recommendation_service import RecommendationService

users_repository = UsersRepository(
    table_name=settings.AWS_DYNAMODB_TABLE_USERS,
    region_name=settings.AWS_REGION,
)
movies_repository = MoviesRepository(
    table_name=settings.AWS_DYNAMODB_TABLE_MOVIES,
    region_name=settings.AWS_REGION,
)
recommendation_cache_repository = RecommendationCacheRepository(
    table_name=settings.AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE,
    region_name=settings.AWS_REGION,
)
password_hasher = PasswordHasher(iterations=settings.PASSWORD_HASH_ITERATIONS)
jwt_service = JWTService(
    secret=settings.JWT_SECRET,
    issuer=settings.JWT_ISSUER,
    audience=settings.JWT_AUDIENCE,
    access_token_minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES,
)
auth_service = AuthService(
    users=users_repository,
    password_hasher=password_hasher,
    allow_legacy_dev_login=settings.ALLOW_LEGACY_DEV_LOGIN,
)
recommendation_provider = MockRecommendationProvider(
    repository=movies_repository,
)
recommendation_service = RecommendationService(
    provider=recommendation_provider,
    cache=recommendation_cache_repository,
    movie_repository=movies_repository,
    cache_ttl_seconds=settings.RECOMMENDATION_CACHE_TTL_SECONDS,
)
movie_service = MovieService(
    repository=movies_repository,
    recommendation_service=recommendation_service,
)
