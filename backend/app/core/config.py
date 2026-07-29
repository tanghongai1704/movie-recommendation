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
    validate_iam_role_arn,
    validate_jwt_algorithm,
    validate_jwt_secret,
    validate_log_level,
    validate_s3_bucket_name,
    validate_s3_prefix,
    validate_sagemaker_resource_name,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    validate_resources: bool


@dataclass(frozen=True)
class DynamoDBSettings:
    movies_table: str
    popular_table: str
    users_table: str
    interactions_table: str
    recommendation_cache_table: str
    popular_list_id: str


@dataclass(frozen=True)
class S3Settings:
    bucket: str
    dataset_prefix: str
    raw_prefix: str
    processed_prefix: str
    features_prefix: str
    serving_prefix: str
    training_prefix: str
    model_prefix: str
    output_prefix: str
    interaction_export_prefix: str


@dataclass(frozen=True)
class SageMakerSettings:
    enabled: bool
    training_job_name_prefix: str | None
    endpoint_name: str | None
    model_name: str | None
    execution_role: str | None
    instance_type: str | None
    content_type: str
    accept: str
    recommendation_limit: int


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
        validate_resources = boolean_value(
            "AWS_VALIDATE_RESOURCES",
            default=True,
        )

        s3_bucket = validate_s3_bucket_name(
            str(environment_value("AWS_S3_BUCKET", required=True))
        )
        configured_endpoint_name = environment_value(
            "AWS_SAGEMAKER_ENDPOINT_NAME"
        )
        sagemaker_enabled = boolean_value(
            "AWS_SAGEMAKER_ENABLED",
            # Existing deployments predate the explicit enable flag. A
            # configured endpoint therefore enables inference unless an
            # operator deliberately sets this flag to false.
            default=bool(configured_endpoint_name),
        )
        sagemaker_endpoint_name = validate_sagemaker_resource_name(
            configured_endpoint_name,
            name="AWS_SAGEMAKER_ENDPOINT_NAME",
            required=sagemaker_enabled,
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
            project_root=PROJECT_ROOT,
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
                validate_resources=validate_resources,
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
                popular_list_id=str(
                    environment_value(
                        "AWS_DYNAMODB_POPULAR_LIST_ID",
                        required=True,
                    )
                ),
            ),
            s3=S3Settings(
                bucket=s3_bucket,
                dataset_prefix=str(validate_s3_prefix(
                    environment_value(
                        "AWS_S3_DATASET_PREFIX",
                        required=True,
                    ),
                    name="AWS_S3_DATASET_PREFIX",
                    required=True,
                )),
                raw_prefix=str(validate_s3_prefix(
                    environment_value("AWS_S3_RAW_PREFIX", required=True),
                    name="AWS_S3_RAW_PREFIX",
                    required=True,
                )),
                processed_prefix=str(validate_s3_prefix(
                    environment_value(
                        "AWS_S3_PROCESSED_PREFIX",
                        required=True,
                    ),
                    name="AWS_S3_PROCESSED_PREFIX",
                    required=True,
                )),
                features_prefix=str(validate_s3_prefix(
                    environment_value(
                        "AWS_S3_FEATURES_PREFIX",
                        required=True,
                    ),
                    name="AWS_S3_FEATURES_PREFIX",
                    required=True,
                )),
                serving_prefix=str(validate_s3_prefix(
                    environment_value(
                        "AWS_S3_SERVING_PREFIX",
                        required=True,
                    ),
                    name="AWS_S3_SERVING_PREFIX",
                    required=True,
                )),
                training_prefix=str(validate_s3_prefix(
                    environment_value(
                        "AWS_S3_TRAINING_PREFIX",
                        required=True,
                    ),
                    name="AWS_S3_TRAINING_PREFIX",
                    required=True,
                )),
                model_prefix=str(validate_s3_prefix(
                    environment_value(
                        "AWS_S3_MODEL_PREFIX",
                        required=True,
                    ),
                    name="AWS_S3_MODEL_PREFIX",
                    required=True,
                )),
                output_prefix=str(validate_s3_prefix(
                    environment_value(
                        "AWS_S3_OUTPUT_PREFIX",
                        required=True,
                    ),
                    name="AWS_S3_OUTPUT_PREFIX",
                    required=True,
                )),
                interaction_export_prefix=str(validate_s3_prefix(
                    environment_value(
                        "AWS_S3_INTERACTION_EXPORT_PREFIX",
                        required=True,
                    ),
                    name="AWS_S3_INTERACTION_EXPORT_PREFIX",
                    required=True,
                )),
            ),
            sagemaker=SageMakerSettings(
                enabled=sagemaker_enabled,
                training_job_name_prefix=validate_sagemaker_resource_name(
                    environment_value(
                        "AWS_SAGEMAKER_TRAINING_JOB_NAME_PREFIX"
                    ),
                    name="AWS_SAGEMAKER_TRAINING_JOB_NAME_PREFIX",
                ),
                endpoint_name=sagemaker_endpoint_name,
                model_name=validate_sagemaker_resource_name(
                    environment_value("AWS_SAGEMAKER_MODEL_NAME"),
                    name="AWS_SAGEMAKER_MODEL_NAME",
                ),
                execution_role=validate_iam_role_arn(
                    environment_value("AWS_SAGEMAKER_EXECUTION_ROLE")
                ),
                instance_type=environment_value(
                    "AWS_SAGEMAKER_INSTANCE_TYPE"
                ),
                content_type=str(
                    environment_value(
                        "AWS_SAGEMAKER_CONTENT_TYPE",
                        default="application/json",
                    )
                ),
                accept=str(
                    environment_value(
                        "AWS_SAGEMAKER_ACCEPT",
                        default="application/json",
                    )
                ),
                recommendation_limit=integer_value(
                    "AWS_SAGEMAKER_RECOMMENDATION_LIMIT",
                    default=10,
                    minimum=1,
                    maximum=50,
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
                        default="endpoint-unversioned",
                    )
                ),
            ),
        )


settings = Settings.from_environment()
