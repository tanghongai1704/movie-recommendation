# Environment Variables

`.env.example` is the machine-readable template. `.env` is untracked. Required
secrets are left empty; optional credential variables are omitted unless they
are actually used.

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
| `AWS_ACCESS_KEY_ID` | Temporary local access key | IAM | No | secret | SDK chain | STS command |
| `AWS_SECRET_ACCESS_KEY` | Temporary local secret key | IAM | No | secret | SDK chain | STS command |
| `AWS_SESSION_TOKEN` | Temporary session token | IAM | No | secret | SDK chain | STS command |
| `AWS_ENDPOINT_URL` | Explicit custom AWS endpoint | AWS SDK | No | private endpoint URL | SDK clients | startup |
| `AWS_VALIDATE_CREDENTIALS` | Check credential provider chain | STS | No | `True` | config startup | remove credentials and verify failure |
| `AWS_VALIDATE_RESOURCES` | Strictly check identity/tables/S3; warn on endpoint health | AWS | No | `True` | startup validator | backend startup |
| `AWS_CONNECT_TIMEOUT_SECONDS` | SDK connect timeout | AWS SDK | No | `3` | botocore | config test |
| `AWS_READ_TIMEOUT_SECONDS` | SDK read timeout | AWS SDK | No | `10` | botocore | config test |
| `AWS_MAX_ATTEMPTS` | SDK and BatchGet attempts | AWS SDK | No | `3` | botocore/repository | config test |
| `AWS_RETRY_MODE` | SDK retry strategy | AWS SDK | No | `standard` | botocore | config test |

Prefer IAM roles on AWS-hosted workloads. Never commit the three explicit
credential values.
`.env.example` keeps the complete blank placeholders for discoverability; the
backend removes blank optional AWS variables before boto3 resolves its default
credential chain.

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
| `AWS_S3_BUCKET` | Durable data bucket | Yes | `movie-recommendation-fcaj` | backend/ML | `head-bucket` |
| `AWS_S3_DATASET_PREFIX` | Dataset and DynamoDB-export root | Yes | `datasets/` | mapping/validation | list prefix |
| `AWS_S3_RAW_PREFIX` | Raw source data | Yes | `datasets/raw/` | S3 sync | list prefix |
| `AWS_S3_PROCESSED_PREFIX` | Cleaned data and feature tables | Yes | `datasets/processed/` | S3 sync | list prefix |
| `AWS_S3_SERVING_PREFIX` | Model inference lookup tables | Yes | `inference/` | S3 sync/endpoint bundle | list prefix |
| `AWS_S3_TRAINING_PREFIX` | Split/training input | Yes | `training/` | training | list prefix |
| `AWS_S3_MODEL_PREFIX` | Versioned artifacts and bundles | Yes | `models/` | training/deployment | list prefix |
| `AWS_S3_OUTPUT_PREFIX` | Evaluation reports | Yes | `evaluation/` | training | list prefix |
| `AWS_S3_INTERACTION_EXPORT_PREFIX` | Interaction JSONL exports | Yes | `datasets/exports/` | ML exporter | list prefix |

Feature tables intentionally share `datasets/processed/`, so the former
`AWS_S3_FEATURES_PREFIX` variable was removed. DynamoDB table snapshots remain
under `datasets/serving/` and are not endpoint lookup files.

## SageMaker and recommendation cache

| Variable | Purpose | Required | Example | Used by | Verification |
|---|---|---|---|---|---|
| `AWS_SAGEMAKER_ENABLED` | Enable endpoint provider; endpoint name also enables it when omitted | No | `True` | provider/startup | cache-miss test |
| `AWS_SAGEMAKER_ENDPOINT_NAME` | Real-time endpoint | When enabled | `movie-rec-endpoint` | provider | `describe-endpoint` |
| `AWS_SAGEMAKER_CONTENT_TYPE` | Request media type | No | `application/json` | provider | contract test |
| `AWS_SAGEMAKER_ACCEPT` | Response media type | No | `application/json` | provider | contract test |
| `AWS_SAGEMAKER_RECOMMENDATION_LIMIT` | Endpoint result count | No | `10` | provider | provider test |
| `RECOMMENDATION_CACHE_TTL_SECONDS` | Cache validity | No | `300` | service | service test |
| `RECOMMENDATION_MODEL_VERSION` | Fallback only when endpoint omits its model version; must never be mock for real inference | Before inference | version string | provider/service | inspect cache |

Training job, execution role, model resource and instance settings belong to
the ML deployment tooling, not the FastAPI runtime environment.

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
