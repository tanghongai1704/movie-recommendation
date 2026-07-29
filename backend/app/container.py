"""Application composition root for security, services, and repositories."""

import boto3
from botocore.config import Config as BotocoreConfig

from app.core.config import settings
from app.core.security import JWTService, PasswordHasher
from app.repositories.movies_repository import MoviesRepository
from app.repositories.recommendation_cache_repository import (
    RecommendationCacheRepository,
)
from app.repositories.user_interactions_repository import (
    UserInteractionsRepository,
)
from app.repositories.users_repository import UsersRepository
from app.services.auth_service import AuthService
from app.services.interaction_service import InteractionService
from app.services.mock_recommendation_provider import MockRecommendationProvider
from app.services.movie_service import MovieService
from app.services.recommendation_service import RecommendationService

aws_client_config = BotocoreConfig(
    connect_timeout=settings.aws.connect_timeout_seconds,
    read_timeout=settings.aws.read_timeout_seconds,
    retries={
        "max_attempts": settings.aws.max_attempts,
        "mode": settings.aws.retry_mode,
    },
)
dynamodb_resource = boto3.resource(
    "dynamodb",
    region_name=settings.aws.region,
    endpoint_url=settings.aws.endpoint_url,
    config=aws_client_config,
)

users_repository = UsersRepository(
    table_name=settings.dynamodb.users_table,
    region_name=settings.aws.region,
    table=dynamodb_resource.Table(settings.dynamodb.users_table),
)
movies_repository = MoviesRepository(
    table_name=settings.dynamodb.movies_table,
    region_name=settings.aws.region,
    table=dynamodb_resource.Table(settings.dynamodb.movies_table),
)
recommendation_cache_repository = RecommendationCacheRepository(
    table_name=settings.dynamodb.recommendation_cache_table,
    region_name=settings.aws.region,
    table=dynamodb_resource.Table(
        settings.dynamodb.recommendation_cache_table
    ),
)
user_interactions_repository = UserInteractionsRepository(
    table_name=settings.dynamodb.interactions_table,
    region_name=settings.aws.region,
    table=dynamodb_resource.Table(settings.dynamodb.interactions_table),
)
password_hasher = PasswordHasher(
    iterations=settings.authentication.password_hash_iterations
)
jwt_service = JWTService(
    secret=settings.authentication.secret_key,
    algorithm=settings.authentication.algorithm,
    issuer=settings.authentication.issuer,
    audience=settings.authentication.audience,
    access_token_minutes=(
        settings.authentication.access_token_expire_minutes
    ),
)
auth_service = AuthService(
    users=users_repository,
    password_hasher=password_hasher,
    allow_legacy_dev_login=(
        settings.authentication.allow_legacy_dev_login
    ),
)
interaction_service = InteractionService(
    repository=user_interactions_repository,
)
recommendation_provider = MockRecommendationProvider(
    repository=movies_repository,
)
recommendation_service = RecommendationService(
    provider=recommendation_provider,
    cache=recommendation_cache_repository,
    movie_repository=movies_repository,
    cache_ttl_seconds=settings.cache.ttl_seconds,
    scenario=settings.cache.scenario,
    model_version=settings.cache.model_version,
)
movie_service = MovieService(
    repository=movies_repository,
    recommendation_service=recommendation_service,
)
