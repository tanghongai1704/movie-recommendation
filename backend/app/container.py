"""Application composition root for security, services, and repositories."""

from app.aws.infrastructure import create_aws_clients
from app.aws.s3_storage import S3DatasetStorage
from app.core.config import settings
from app.core.security import JWTService, PasswordHasher
from app.repositories.movies_repository import MoviesRepository
from app.repositories.popular_movies_repository import PopularMoviesRepository
from app.repositories.recommendation_cache_repository import (
    RecommendationCacheRepository,
)
from app.repositories.user_interactions_repository import (
    UserInteractionsRepository,
)
from app.repositories.users_repository import UsersRepository
from app.services.auth_service import AuthService
from app.services.interaction_service import InteractionService
from app.services.movie_service import MovieService
from app.services.popular_movie_service import PopularMovieService
from app.services.recommendation_service import RecommendationService
from app.services.sagemaker_recommendation_provider import (
    SageMakerRecommendationProvider,
)

aws_clients = create_aws_clients(settings)
dynamodb_resource = aws_clients.dynamodb_resource

users_repository = UsersRepository(
    table_name=settings.dynamodb.users_table,
    region_name=settings.aws.region,
    table=dynamodb_resource.Table(settings.dynamodb.users_table),
)
movies_repository = MoviesRepository(
    table_name=settings.dynamodb.movies_table,
    region_name=settings.aws.region,
    table=dynamodb_resource.Table(settings.dynamodb.movies_table),
    batch_reader=dynamodb_resource,
    batch_max_attempts=settings.aws.max_attempts,
)
popular_movies_repository = PopularMoviesRepository(
    table_name=settings.dynamodb.popular_table,
    region_name=settings.aws.region,
    table=dynamodb_resource.Table(settings.dynamodb.popular_table),
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
popular_movie_service = PopularMovieService(
    popular_movies=popular_movies_repository,
    movies=movies_repository,
    list_id=settings.dynamodb.popular_list_id,
)
recommendation_provider = SageMakerRecommendationProvider(
    runtime_client=aws_clients.sagemaker_runtime_client,
    control_client=aws_clients.sagemaker_client,
    endpoint_name=settings.sagemaker.endpoint_name,
    recommendation_limit=settings.sagemaker.recommendation_limit,
    content_type=settings.sagemaker.content_type,
    accept=settings.sagemaker.accept,
    fallback_model_version=settings.cache.model_version,
    enabled=settings.sagemaker.enabled,
)
recommendation_service = RecommendationService(
    provider=recommendation_provider,
    cache=recommendation_cache_repository,
    movie_repository=movies_repository,
    users=users_repository,
    interactions=user_interactions_repository,
    fallback_movies=popular_movie_service,
    cache_ttl_seconds=settings.cache.ttl_seconds,
    model_version=settings.cache.model_version,
)
movie_service = MovieService(
    repository=movies_repository,
    recommendation_service=recommendation_service,
    popular_movie_service=popular_movie_service,
)
s3_dataset_storage = S3DatasetStorage(
    client=aws_clients.s3_client,
    bucket=settings.s3.bucket,
)
