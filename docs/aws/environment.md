# Environment Variables

`.env.example` is the machine-readable template. `.env` is untracked. Empty
values are not examples of real resources; they must be supplied per
environment.

## Application, API and logging

| Variable | Purpose | Service | Required | Example | Used by | Verification |
|---|---|---|---|---|---|---|
| `APP_ENV` | Environment label | Application | No | `production` | backend settings | inspect `/docs` metadata/logs |
| `APP_NAME` | Internal app name | Application | No | `movie-recommendation` | backend settings | startup |
| `APP_TITLE` | OpenAPI title | API | No | `Movie Recommendation API` | FastAPI | open `/docs` |
| `APP_VERSION` | API application version | API | No | `1.0.0` | FastAPI | open `/docs` |
| `APP_DESCRIPTION` | OpenAPI description | API | No | descriptive text | FastAPI | open `/docs` |
| `DEBUG` | FastAPI debug mode | Application | No | `False` | FastAPI | startup logs |
| `API_PREFIX` | Stable route prefix | API | No | `/api/v1` | router composition | call `/api/v1/movies` |
| `API_DOCS_PATH` | OpenAPI UI path | API | No | `/docs` | FastAPI | open path |
| `API_HEALTH_PATH` | Health route/healthcheck path | API/Docker | No | `/health` | FastAPI, Compose | curl path |
| `CORS_ALLOWED_ORIGINS` | Browser origins | API | Yes | `https://app.example.com` | CORS middleware | browser preflight |
| `CORS_ALLOW_CREDENTIALS` | Credentialed CORS | API | No | `True` | CORS middleware | browser preflight |
| `LOG_LEVEL` | Minimum log level | Logging | No | `INFO` | backend logging | inspect logs |
| `LOG_FORMAT` | Python log format | Logging | No | standard format | backend logging | inspect logs |
| `LOG_DATE_FORMAT` | Log timestamp format | Logging | No | `%Y-%m-%d %H:%M:%S` | backend logging | inspect logs |

## Authentication

| Variable | Purpose | Service | Required | Example | Used by | Verification |
|---|---|---|---|---|---|---|
| `JWT_SECRET_KEY` | JWT HMAC secret, at least 32 bytes | Auth | Yes | generated secret | `JWTService` | login/profile test |
| `JWT_ALGORITHM` | Implemented signing algorithm | Auth | No | `HS256` | `JWTService` | config test |
| `JWT_ISSUER` | Token issuer | Auth | No | `movie-recommendation-api` | `JWTService` | decode token |
| `JWT_AUDIENCE` | Token audience | Auth | No | `movie-recommendation-frontend` | `JWTService` | decode token |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | Access-token lifetime | Auth | No | `60` | `JWTService` | token claims |
| `PASSWORD_HASH_ITERATIONS` | PBKDF2 iterations | Auth | No | `10000` | `PasswordHasher` | security tests |
| `ALLOW_LEGACY_DEV_LOGIN` | Restricted seed compatibility | Auth | No | `False` | `AuthService` | must be false in production |

`JWT_SECRET` remains a temporary read alias for `JWT_SECRET_KEY`.

## AWS SDK

| Variable | Purpose | Service | Required | Example | Used by | Verification |
|---|---|---|---|---|---|---|
| `AWS_REGION` | Canonical AWS Region | All AWS | Yes | `ap-southeast-1` | backend and ML | `aws configure get region` |
| `AWS_DEFAULT_REGION` | CLI/SDK alias; must match | All AWS | No | same as region | AWS tooling | STS command |
| `AWS_PROFILE` | Local SSO/profile name | IAM/STS | No | `project-dev` | boto3/CLI | `aws sts get-caller-identity` |
| `AWS_ACCESS_KEY_ID` | Temporary local access key | IAM | No | secret | SDK chain | STS command |
| `AWS_SECRET_ACCESS_KEY` | Temporary local secret key | IAM | No | secret | SDK chain | STS command |
| `AWS_SESSION_TOKEN` | Temporary session token | IAM | No | secret | SDK chain | STS command |
| `AWS_ENDPOINT_URL` | Explicit custom AWS endpoint | AWS SDK | No | private endpoint URL | SDK clients | startup |
| `AWS_VALIDATE_CREDENTIALS` | Check credential provider chain | STS | No | `True` | config startup | remove credentials and verify failure |
| `AWS_VALIDATE_RESOURCES` | Check identity/tables/S3/endpoint | AWS | No | `True` | startup validator | backend startup |
| `AWS_CONNECT_TIMEOUT_SECONDS` | SDK connect timeout | AWS SDK | No | `3` | botocore | config test |
| `AWS_READ_TIMEOUT_SECONDS` | SDK read timeout | AWS SDK | No | `10` | botocore | config test |
| `AWS_MAX_ATTEMPTS` | SDK and BatchGet attempts | AWS SDK | No | `3` | botocore/repository | config test |
| `AWS_RETRY_MODE` | SDK retry strategy | AWS SDK | No | `standard` | botocore | config test |

Prefer IAM roles or SSO. Never commit the three explicit credential variables.

## DynamoDB

| Variable | Purpose | Required | Example | Used by | Verification |
|---|---|---|---|---|---|
| `AWS_DYNAMODB_MOVIES_TABLE` | Movies table name | Yes | `Movies` | `MoviesRepository` | `describe-table` |
| `AWS_DYNAMODB_POPULAR_TABLE` | PopularMovies table name | Yes | `PopularMovies` | `PopularMoviesRepository` | `describe-table` |
| `AWS_DYNAMODB_USERS_TABLE` | Users table name | Yes | `Users` | `UsersRepository` | `describe-table` |
| `AWS_DYNAMODB_INTERACTIONS_TABLE` | UserInteractions table name | Yes | `UserInteractions` | repository and ML exporter | `describe-table` |
| `AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE` | Cache table name | Yes | `RecommendationCache` | cache repository | `describe-table` |
| `AWS_DYNAMODB_POPULAR_LIST_ID` | Guest ranking key | Yes | `top_rated_all` | `PopularMovieService` | `get-item` |

The former `AWS_DYNAMODB_TABLE_*` names remain migration aliases only.

## Amazon S3

| Variable | Purpose | Required | Example suffix | Used by | Verification |
|---|---|---|---|---|---|
| `AWS_S3_BUCKET` | Durable data bucket | Yes | globally unique name | backend/ML | `head-bucket` |
| `AWS_S3_DATASET_PREFIX` | Data root | Yes | `app/dev/data/` | mapping/validation | list prefix |
| `AWS_S3_RAW_PREFIX` | Raw source data | Yes | `data/raw/` | S3 sync | list prefix |
| `AWS_S3_PROCESSED_PREFIX` | Cleaned data | Yes | `data/processed/` | S3 sync | list prefix |
| `AWS_S3_FEATURES_PREFIX` | Feature tables | Yes | `data/features/` | S3 sync | list prefix |
| `AWS_S3_SERVING_PREFIX` | Serving exports | Yes | `data/serving/` | S3 sync | list prefix |
| `AWS_S3_TRAINING_PREFIX` | Splits/training input | Yes | `data/splits/` | training | list prefix |
| `AWS_S3_MODEL_PREFIX` | Versioned artifacts | Yes | `artifacts/` | training/deployment | list prefix |
| `AWS_S3_OUTPUT_PREFIX` | Reports/job outputs | Yes | `outputs/` | training | list prefix |
| `AWS_S3_INTERACTION_EXPORT_PREFIX` | Interaction JSONL/export | Yes | `events/` | ML exporter | list prefix |

## SageMaker and recommendation cache

| Variable | Purpose | Required | Example | Used by | Verification |
|---|---|---|---|---|---|
| `AWS_SAGEMAKER_ENABLED` | Enable endpoint provider | No | `False` | provider/startup | cache-miss test |
| `AWS_SAGEMAKER_TRAINING_JOB_NAME_PREFIX` | Job naming | For job | `movie-rec-train` | ML launcher | dry run |
| `AWS_SAGEMAKER_ENDPOINT_NAME` | Real-time endpoint | When enabled | versioned name | provider | `describe-endpoint` |
| `AWS_SAGEMAKER_MODEL_NAME` | Deployed model resource | For deployment | versioned name | deployment docs | `describe-model` |
| `AWS_SAGEMAKER_EXECUTION_ROLE` | Execution role ARN | For job/deploy | role ARN | ML launcher | `iam get-role` |
| `AWS_SAGEMAKER_INSTANCE_TYPE` | Training/processing instance | For job | `ml.m5.xlarge` | ML launcher | dry run |
| `AWS_SAGEMAKER_CONTENT_TYPE` | Request media type | No | `application/json` | provider | contract test |
| `AWS_SAGEMAKER_ACCEPT` | Response media type | No | `application/json` | provider | contract test |
| `AWS_SAGEMAKER_RECOMMENDATION_LIMIT` | Endpoint result count | No | `10` | provider | provider test |
| `RECOMMENDATION_CACHE_TTL_SECONDS` | Cache validity | No | `300` | service | service test |
| `RECOMMENDATION_CACHE_SCENARIO` | Cache/provider scenario | No | `default` | service/provider | cache key |
| `RECOMMENDATION_MODEL_VERSION` | Version written to new cache | Before inference | version string | service | inspect cache |

## Frontend and Docker

| Variable | Purpose | Required | Example | Used by | Verification |
|---|---|---|---|---|---|
| `VITE_API_URL` | Backend API base URL | Yes | `http://127.0.0.1:8000/api/v1` | frontend config | browser network |
| `VITE_TMDB_POSTER_BASE_URL` | TMDB image base | Yes | `https://image.tmdb.org/t/p/w500` | movie service | poster request |
| `VITE_HOST` | Vite bind host | No | `0.0.0.0` | Vite/Compose | container logs |
| `VITE_PORT` | Native Vite port | No | `5173` | Vite | frontend URL |
| `COMPOSE_PROJECT_NAME` | Compose project | No | `movie-recommendation` | Compose | `compose ps` |
| `ENV_FILE` | Compose environment file | No | `.env` | Compose | `compose config` |
| `BACKEND_CONTAINER_NAME` | Backend container name | No | `movie-backend` | Compose | `compose ps` |
| `BACKEND_HOST` | Uvicorn bind host | No | `0.0.0.0` | backend image | logs |
| `BACKEND_HOST_PORT` | Backend host port | No | `8000` | Compose | curl |
| `BACKEND_CONTAINER_PORT` | Backend container port | No | `8000` | image/Compose | healthcheck |
| `BACKEND_RELOAD` | Uvicorn reload | No | `False` | backend image | process command |
| `FRONTEND_CONTAINER_NAME` | Frontend container name | No | `movie-frontend` | Compose | `compose ps` |
| `FRONTEND_HOST_PORT` | Frontend host port | No | `5173` | Compose | browser |
| `FRONTEND_CONTAINER_PORT` | Frontend container port | No | `5173` | Vite/Compose | logs |
| `HEALTHCHECK_INTERVAL` | Health cadence | No | `30s` | Compose | inspect container |
| `HEALTHCHECK_TIMEOUT` | Health timeout | No | `5s` | Compose | inspect container |
| `HEALTHCHECK_RETRIES` | Failure threshold | No | `5` | Compose | inspect container |
