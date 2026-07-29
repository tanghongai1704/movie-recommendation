# AWS and application configuration

This document is the source of truth for runtime configuration. Copy
`.env.example` to `.env` for local development. Never commit `.env`, AWS
credentials, JWT secrets, account IDs, private endpoints, or authorization
headers.

## Configuration flow

```text
environment variables
  -> app.core.config_validation
  -> app.core.config.Settings
  -> app.main and app.container
  -> configured repositories and services
```

`backend/app/core/config.py` defines immutable logical sections:

- Application
- API and CORS
- Authentication
- AWS SDK
- DynamoDB
- S3
- SageMaker
- Logging
- Recommendation cache

Invalid or conflicting configuration raises `ConfigurationError` during
backend import, before the API starts accepting traffic.

The frontend reads its runtime build values through
`frontend/src/config/environment.ts`. Vite development-server settings are
loaded by `frontend/vite.config.js`.

## Required backend variables

| Variable | Purpose |
|---|---|
| `JWT_SECRET_KEY` | HMAC secret with at least 32 bytes |
| `AWS_REGION` | Region used by the backend AWS clients |
| `AWS_DYNAMODB_MOVIES_TABLE` | Movies table name |
| `AWS_DYNAMODB_POPULAR_TABLE` | PopularMovies table name |
| `AWS_DYNAMODB_USERS_TABLE` | Users table name |
| `AWS_DYNAMODB_INTERACTIONS_TABLE` | UserInteractions table name |
| `AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE` | RecommendationCache table name |
| `AWS_S3_BUCKET` | Validated project bucket identifier reserved for the AWS data pipeline |

S3 is not called by the current backend business flow. Its bucket is validated
now so deployment configuration cannot silently omit the resource expected by
the future data/training integration.

## Application and API

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment label such as development, testing, or production |
| `APP_NAME` | `movie-recommendation` | Application identifier |
| `APP_TITLE` | `Movie Recommendation API` | OpenAPI title |
| `APP_VERSION` | `1.0.0` | OpenAPI application version |
| `APP_DESCRIPTION` | Current API description | OpenAPI description |
| `DEBUG` | `False` | FastAPI debug mode |
| `API_PREFIX` | `/api/v1` | Prefix shared by every API router |
| `API_DOCS_PATH` | `/docs` | OpenAPI UI path |
| `API_HEALTH_PATH` | `/health` | Healthcheck path |
| `CORS_ALLOWED_ORIGINS` | `*` | Comma-separated browser origins |
| `CORS_ALLOW_CREDENTIALS` | `True` | CORS credentials policy |

Changing `API_PREFIX` also requires changing the suffix in `VITE_API_URL`.
Production should replace `CORS_ALLOWED_ORIGINS=*` with explicit HTTPS origins.

## Authentication

| Variable | Default | Validation |
|---|---|---|
| `JWT_SECRET_KEY` | none | Required; at least 32 bytes |
| `JWT_ALGORITHM` | `HS256` | Only HS256 is implemented |
| `JWT_ISSUER` | `movie-recommendation-api` | Must be non-empty |
| `JWT_AUDIENCE` | `movie-recommendation-frontend` | Must be non-empty |
| `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Positive integer |
| `PASSWORD_HASH_ITERATIONS` | `10000` | Integer from 10,000 to 2,000,000 |
| `ALLOW_LEGACY_DEV_LOGIN` | `False` | Development-only compatibility switch |

`ALLOW_LEGACY_DEV_LOGIN` must remain false in production. It does not change the
password hashing algorithm for registered users.

## AWS SDK

| Variable | Default | Description |
|---|---|---|
| `AWS_REGION` | none | Required application region |
| `AWS_DEFAULT_REGION` | none | Optional CLI/SDK compatibility value; when present it must match `AWS_REGION` |
| `AWS_PROFILE` | none | Optional named local profile |
| `AWS_ENDPOINT_URL` | none | Optional HTTP(S) endpoint for an explicitly configured emulator |
| `AWS_VALIDATE_CREDENTIALS` | `True` | Validate that the default credential chain can resolve credentials at startup |
| `AWS_CONNECT_TIMEOUT_SECONDS` | `3` | AWS client connection timeout |
| `AWS_READ_TIMEOUT_SECONDS` | `10` | AWS client read timeout |
| `AWS_MAX_ATTEMPTS` | `3` | AWS SDK retry attempts |
| `AWS_RETRY_MODE` | `standard` | `legacy`, `standard`, or `adaptive` |

The backend creates one reusable DynamoDB resource in `app.container` and
injects table handles into repositories. Repository CRUD behavior is unchanged.

### Credential resolution

Preferred order:

1. IAM role or workload identity in deployed environments.
2. AWS SSO or a named profile for native local development.
3. Temporary environment credentials only when required locally.

The optional variables `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and
`AWS_SESSION_TOKEN` use the normal boto3 credential provider chain. The access
key and secret key must be supplied together. They are intentionally not read
or logged by application code.

For AWS SSO:

```bash
aws configure sso
aws sso login --profile <profile-name>
export AWS_PROFILE=<profile-name>
export AWS_REGION=<region>
export AWS_DEFAULT_REGION=<region>
```

PowerShell:

```powershell
aws configure sso
aws sso login --profile <profile-name>
$env:AWS_PROFILE = "<profile-name>"
$env:AWS_REGION = "<region>"
$env:AWS_DEFAULT_REGION = "<region>"
```

When the backend runs inside Docker, the container must also have access to the
selected profile. Add a local Compose override that mounts the host AWS config
directory read-only to `/root/.aws`, or export temporary credentials through the
untracked `.env`. Do not commit either.

`AWS_VALIDATE_CREDENTIALS=False` is intended only for isolated unit tests or an
explicit emulator setup. It does not create mock AWS data.

## DynamoDB

| Variable | Repository |
|---|---|
| `AWS_DYNAMODB_MOVIES_TABLE` | `MoviesRepository` |
| `AWS_DYNAMODB_POPULAR_TABLE` | `PopularMoviesRepository` |
| `AWS_DYNAMODB_USERS_TABLE` | `UsersRepository` |
| `AWS_DYNAMODB_INTERACTIONS_TABLE` | `UserInteractionsRepository` |
| `AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE` | `RecommendationCacheRepository` |

All five names are required and have no production fallback. The application
never derives a table name from the environment label.

## Amazon S3

| Variable | Required now | Purpose |
|---|---:|---|
| `AWS_S3_BUCKET` | yes | Project data/artifact bucket identifier |
| `AWS_S3_DATASET_PREFIX` | no | Raw dataset namespace |
| `AWS_S3_PROCESSED_PREFIX` | no | Processed dataset namespace |
| `AWS_S3_SERVING_PREFIX` | no | Serving exports namespace |
| `AWS_S3_TRAINING_PREFIX` | no | Training inputs namespace |
| `AWS_S3_MODEL_PREFIX` | no | Model artifact namespace |
| `AWS_S3_OUTPUT_PREFIX` | no | Job output namespace |

Prefixes are normalized without a leading slash and with one trailing slash.
No S3 operation is performed by the current application.

## SageMaker

| Variable | Required now | Purpose |
|---|---:|---|
| `AWS_SAGEMAKER_TRAINING_JOB_NAME_PREFIX` | no | Future training/processing job naming prefix |
| `AWS_SAGEMAKER_ENDPOINT_NAME` | no | Future real-time endpoint identifier |
| `AWS_SAGEMAKER_MODEL_NAME` | no | Future SageMaker model identifier |
| `AWS_SAGEMAKER_EXECUTION_ROLE` | no | Future training/deployment execution role |
| `AWS_SAGEMAKER_INSTANCE_TYPE` | no | Future job or endpoint instance type |

These values are loaded only to centralize future configuration. This
configuration refactor does not invoke SageMaker and does not replace
`MockRecommendationProvider`.

## Recommendation cache

| Variable | Default | Description |
|---|---|---|
| `RECOMMENDATION_CACHE_TTL_SECONDS` | `300` | Positive cache lifetime |
| `RECOMMENDATION_CACHE_SCENARIO` | `default` | RecommendationCache sort-key scenario |
| `RECOMMENDATION_MODEL_VERSION` | `mock-v1` | Version written to cache by the current provider |

## Logging

| Variable | Default |
|---|---|
| `LOG_LEVEL` | `INFO` |
| `LOG_FORMAT` | `%(asctime)s %(levelname)s %(name)s %(message)s` |
| `LOG_DATE_FORMAT` | `%Y-%m-%d %H:%M:%S` |

Logging configuration never emits credentials or full authorization headers.

## Frontend and Vite

| Variable | Required | Description |
|---|---:|---|
| `VITE_API_URL` | yes | Complete backend API base URL including `API_PREFIX` |
| `VITE_TMDB_POSTER_BASE_URL` | yes | TMDB image base URL and size |
| `VITE_HOST` | no | Vite development bind host |
| `VITE_PORT` | no | Vite development port |

Only `VITE_*` variables are exposed to browser code. Do not place secrets in a
`VITE_*` variable.

## Docker Compose

Compose reads `${ENV_FILE:-.env}` and supports:

- `COMPOSE_PROJECT_NAME`
- `BACKEND_CONTAINER_NAME`
- `BACKEND_HOST`
- `BACKEND_HOST_PORT`
- `BACKEND_CONTAINER_PORT`
- `BACKEND_RELOAD`
- `FRONTEND_CONTAINER_NAME`
- `FRONTEND_HOST_PORT`
- `FRONTEND_CONTAINER_PORT`
- `HEALTHCHECK_INTERVAL`
- `HEALTHCHECK_TIMEOUT`
- `HEALTHCHECK_RETRIES`

Local defaults preserve the existing ports: backend 8000 and frontend 5173.
Set `BACKEND_RELOAD=false` for a deployment that should not run the Uvicorn
file watcher.

## Deployment configuration

The GitHub workflow consumes:

- GitHub secret `EC2_HOST`
- GitHub secret `EC2_USER`
- GitHub secret `EC2_SSH_KEY`
- GitHub repository variable `EC2_APP_DIR`

The EC2 `.env` remains the deployment-specific runtime configuration. The
workflow does not contain AWS credentials or resource identifiers.

## Backward-compatible names

The backend temporarily accepts these aliases:

| Legacy | Canonical |
|---|---|
| `JWT_SECRET` | `JWT_SECRET_KEY` |
| `AWS_DYNAMODB_TABLE_MOVIES` | `AWS_DYNAMODB_MOVIES_TABLE` |
| `AWS_DYNAMODB_TABLE_POPULAR` | `AWS_DYNAMODB_POPULAR_TABLE` |
| `AWS_DYNAMODB_TABLE_USERS` | `AWS_DYNAMODB_USERS_TABLE` |
| `AWS_DYNAMODB_TABLE_INTERACTIONS` | `AWS_DYNAMODB_INTERACTIONS_TABLE` |
| `AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE` | `AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE` |

If a legacy and canonical variable are both populated with different values,
startup fails. Migrate deployment environments to canonical names, verify them,
and then remove the legacy entries.
