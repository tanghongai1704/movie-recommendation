"""Centralized, typed application configuration loaded from the environment."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config_validation import (
    boolean_value,
    csv_value,
    environment_value,
    integer_value,
    validate_api_path,
    validate_aws_credentials,
    validate_aws_region,
    validate_cors_origins,
    validate_http_url,
    validate_jwt_algorithm,
    validate_jwt_secret,
    validate_log_level,
    validate_s3_bucket_name,
    validate_s3_prefix,
)


@dataclass(frozen=True)
class ApplicationSettings:
    environment: str
    name: str
    title: str
    version: str
    description: str
    debug: bool


@dataclass(frozen=True)
class APISettings:
    prefix: str
    docs_path: str
    health_path: str
    cors_allowed_origins: tuple[str, ...]
    cors_allow_credentials: bool


@dataclass(frozen=True)
class AuthenticationSettings:
    secret_key: str
    algorithm: str
    issuer: str
    audience: str
    access_token_expire_minutes: int
    password_hash_iterations: int
    allow_legacy_dev_login: bool


@dataclass(frozen=True)
class AWSSettings:
    region: str
    profile: str | None
    endpoint_url: str | None
    connect_timeout_seconds: int
    read_timeout_seconds: int
    max_attempts: int
    retry_mode: str
    validate_credentials: bool


@dataclass(frozen=True)
class DynamoDBSettings:
    movies_table: str
    popular_table: str
    users_table: str
    interactions_table: str
    recommendation_cache_table: str


@dataclass(frozen=True)
class S3Settings:
    bucket: str
    dataset_prefix: str | None
    processed_prefix: str | None
    serving_prefix: str | None
    training_prefix: str | None
    model_prefix: str | None
    output_prefix: str | None


@dataclass(frozen=True)
class SageMakerSettings:
    training_job_name_prefix: str | None
    endpoint_name: str | None
    model_name: str | None
    execution_role: str | None
    instance_type: str | None


@dataclass(frozen=True)
class LoggingSettings:
    level: str
    format: str
    date_format: str


@dataclass(frozen=True)
class CacheSettings:
    ttl_seconds: int
    scenario: str
    model_version: str


@dataclass(frozen=True)
class Settings:
    project_root: Path
    application: ApplicationSettings
    api: APISettings
    authentication: AuthenticationSettings
    aws: AWSSettings
    dynamodb: DynamoDBSettings
    s3: S3Settings
    sagemaker: SageMakerSettings
    logging: LoggingSettings
    cache: CacheSettings

    @classmethod
    def from_environment(cls) -> "Settings":
        region = validate_aws_region(
            str(
                environment_value(
                    "AWS_REGION",
                    aliases=("AWS_DEFAULT_REGION",),
                    required=True,
                )
            )
        )
        endpoint_url = validate_http_url(
            environment_value("AWS_ENDPOINT_URL"),
            name="AWS_ENDPOINT_URL",
        )
        validate_credentials = boolean_value(
            "AWS_VALIDATE_CREDENTIALS",
            default=True,
        )
        validate_aws_credentials(enabled=validate_credentials)

        s3_bucket = validate_s3_bucket_name(
            str(environment_value("AWS_S3_BUCKET", required=True))
        )
        retry_mode = str(
            environment_value("AWS_RETRY_MODE", default="standard")
        ).lower()
        if retry_mode not in {"legacy", "standard", "adaptive"}:
            from app.core.config_validation import ConfigurationError

            raise ConfigurationError(
                "AWS_RETRY_MODE must be legacy, standard, or adaptive"
            )

        return cls(
            project_root=Path(__file__).resolve().parents[2],
            application=ApplicationSettings(
                environment=str(
                    environment_value("APP_ENV", default="development")
                ),
                name=str(
                    environment_value(
                        "APP_NAME",
                        default="movie-recommendation",
                    )
                ),
                title=str(
                    environment_value(
                        "APP_TITLE",
                        default="Movie Recommendation API",
                    )
                ),
                version=str(
                    environment_value("APP_VERSION", default="1.0.0")
                ),
                description=str(
                    environment_value(
                        "APP_DESCRIPTION",
                        default=(
                            "Production-ready FastAPI backend for movie "
                            "browsing and authentication"
                        ),
                    )
                ),
                debug=boolean_value("DEBUG", default=False),
            ),
            api=APISettings(
                prefix=validate_api_path(
                    str(environment_value("API_PREFIX", default="/api/v1")),
                    name="API_PREFIX",
                ),
                docs_path=validate_api_path(
                    str(environment_value("API_DOCS_PATH", default="/docs")),
                    name="API_DOCS_PATH",
                ),
                health_path=validate_api_path(
                    str(
                        environment_value(
                            "API_HEALTH_PATH",
                            default="/health",
                        )
                    ),
                    name="API_HEALTH_PATH",
                ),
                cors_allowed_origins=validate_cors_origins(
                    csv_value(
                        "CORS_ALLOWED_ORIGINS",
                        default="*",
                        required=True,
                    )
                ),
                cors_allow_credentials=boolean_value(
                    "CORS_ALLOW_CREDENTIALS",
                    default=True,
                ),
            ),
            authentication=AuthenticationSettings(
                secret_key=validate_jwt_secret(
                    str(
                        environment_value(
                            "JWT_SECRET_KEY",
                            aliases=("JWT_SECRET",),
                            required=True,
                        )
                    )
                ),
                algorithm=validate_jwt_algorithm(
                    str(
                        environment_value(
                            "JWT_ALGORITHM",
                            default="HS256",
                        )
                    )
                ),
                issuer=str(
                    environment_value(
                        "JWT_ISSUER",
                        default="movie-recommendation-api",
                    )
                ),
                audience=str(
                    environment_value(
                        "JWT_AUDIENCE",
                        default="movie-recommendation-frontend",
                    )
                ),
                access_token_expire_minutes=integer_value(
                    "JWT_ACCESS_TOKEN_EXPIRE_MINUTES",
                    default=60,
                    minimum=1,
                ),
                password_hash_iterations=integer_value(
                    "PASSWORD_HASH_ITERATIONS",
                    default=10_000,
                    minimum=10_000,
                    maximum=2_000_000,
                ),
                allow_legacy_dev_login=boolean_value(
                    "ALLOW_LEGACY_DEV_LOGIN",
                    default=False,
                ),
            ),
            aws=AWSSettings(
                region=region,
                profile=environment_value("AWS_PROFILE"),
                endpoint_url=endpoint_url,
                connect_timeout_seconds=integer_value(
                    "AWS_CONNECT_TIMEOUT_SECONDS",
                    default=3,
                    minimum=1,
                ),
                read_timeout_seconds=integer_value(
                    "AWS_READ_TIMEOUT_SECONDS",
                    default=10,
                    minimum=1,
                ),
                max_attempts=integer_value(
                    "AWS_MAX_ATTEMPTS",
                    default=3,
                    minimum=1,
                ),
                retry_mode=retry_mode,
                validate_credentials=validate_credentials,
            ),
            dynamodb=DynamoDBSettings(
                movies_table=str(
                    environment_value(
                        "AWS_DYNAMODB_MOVIES_TABLE",
                        aliases=("AWS_DYNAMODB_TABLE_MOVIES",),
                        required=True,
                    )
                ),
                popular_table=str(
                    environment_value(
                        "AWS_DYNAMODB_POPULAR_TABLE",
                        aliases=("AWS_DYNAMODB_TABLE_POPULAR",),
                        required=True,
                    )
                ),
                users_table=str(
                    environment_value(
                        "AWS_DYNAMODB_USERS_TABLE",
                        aliases=("AWS_DYNAMODB_TABLE_USERS",),
                        required=True,
                    )
                ),
                interactions_table=str(
                    environment_value(
                        "AWS_DYNAMODB_INTERACTIONS_TABLE",
                        aliases=("AWS_DYNAMODB_TABLE_INTERACTIONS",),
                        required=True,
                    )
                ),
                recommendation_cache_table=str(
                    environment_value(
                        "AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE",
                        aliases=(
                            "AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE",
                        ),
                        required=True,
                    )
                ),
            ),
            s3=S3Settings(
                bucket=s3_bucket,
                dataset_prefix=validate_s3_prefix(
                    environment_value("AWS_S3_DATASET_PREFIX"),
                    name="AWS_S3_DATASET_PREFIX",
                ),
                processed_prefix=validate_s3_prefix(
                    environment_value("AWS_S3_PROCESSED_PREFIX"),
                    name="AWS_S3_PROCESSED_PREFIX",
                ),
                serving_prefix=validate_s3_prefix(
                    environment_value("AWS_S3_SERVING_PREFIX"),
                    name="AWS_S3_SERVING_PREFIX",
                ),
                training_prefix=validate_s3_prefix(
                    environment_value("AWS_S3_TRAINING_PREFIX"),
                    name="AWS_S3_TRAINING_PREFIX",
                ),
                model_prefix=validate_s3_prefix(
                    environment_value("AWS_S3_MODEL_PREFIX"),
                    name="AWS_S3_MODEL_PREFIX",
                ),
                output_prefix=validate_s3_prefix(
                    environment_value("AWS_S3_OUTPUT_PREFIX"),
                    name="AWS_S3_OUTPUT_PREFIX",
                ),
            ),
            sagemaker=SageMakerSettings(
                training_job_name_prefix=environment_value(
                    "AWS_SAGEMAKER_TRAINING_JOB_NAME_PREFIX"
                ),
                endpoint_name=environment_value(
                    "AWS_SAGEMAKER_ENDPOINT_NAME"
                ),
                model_name=environment_value("AWS_SAGEMAKER_MODEL_NAME"),
                execution_role=environment_value(
                    "AWS_SAGEMAKER_EXECUTION_ROLE"
                ),
                instance_type=environment_value(
                    "AWS_SAGEMAKER_INSTANCE_TYPE"
                ),
            ),
            logging=LoggingSettings(
                level=validate_log_level(
                    str(environment_value("LOG_LEVEL", default="INFO"))
                ),
                format=str(
                    environment_value(
                        "LOG_FORMAT",
                        default=(
                            "%(asctime)s %(levelname)s %(name)s %(message)s"
                        ),
                    )
                ),
                date_format=str(
                    environment_value(
                        "LOG_DATE_FORMAT",
                        default="%Y-%m-%d %H:%M:%S",
                    )
                ),
            ),
            cache=CacheSettings(
                ttl_seconds=integer_value(
                    "RECOMMENDATION_CACHE_TTL_SECONDS",
                    default=300,
                    minimum=1,
                ),
                scenario=str(
                    environment_value(
                        "RECOMMENDATION_CACHE_SCENARIO",
                        default="default",
                    )
                ),
                model_version=str(
                    environment_value(
                        "RECOMMENDATION_MODEL_VERSION",
                        default="mock-v1",
                    )
                ),
            ),
        )


settings = Settings.from_environment()
