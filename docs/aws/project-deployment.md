# Project Deployment

This is the complete deployment path from a new machine.

## 1. Prerequisites

- Git with submodule support
- Docker Engine and Docker Compose v2
- AWS CLI v2
- an IAM identity or workload role with the permissions in
  [AWS Setup](aws-setup.md)
- existing five DynamoDB tables and S3 bucket

## 2. Clone

```bash
git clone --recurse-submodules <repository-url>
cd movie-recommendation
git submodule update --init --recursive
```

## 3. Configure AWS identity

Developer workstation:

```bash
aws sso login --profile <profile>
aws sts get-caller-identity --profile <profile>
```

EC2/ECS should use an instance/task role:

```bash
aws sts get-caller-identity
```

Do not copy permanent access keys to a server. For Docker on a workstation,
either use temporary values in untracked `.env` or mount the AWS profile
directory read-only through a local Compose override.

## 4. Configure environment

```bash
cp .env.example .env
```

Fill:

- JWT secret
- Region
- five DynamoDB table names
- selected PopularMovies `list_id`
- S3 bucket and every prefix
- production CORS origin
- frontend API URL

Keep:

```dotenv
AWS_VALIDATE_CREDENTIALS=True
AWS_VALIDATE_RESOURCES=True
AWS_SAGEMAKER_ENABLED=False
BACKEND_RELOAD=False
```

Enable SageMaker only after completing the endpoint procedure.

## 5. Verify AWS before starting

```bash
aws sts get-caller-identity
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_MOVIES_TABLE" --region "$AWS_REGION"
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_POPULAR_TABLE" --region "$AWS_REGION"
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_USERS_TABLE" --region "$AWS_REGION"
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_INTERACTIONS_TABLE" --region "$AWS_REGION"
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE" --region "$AWS_REGION"
aws s3api head-bucket --bucket "$AWS_S3_BUCKET"
```

The backend repeats identity, key-schema, table-state and S3 permission checks
at startup.

## 6. Build and run

```bash
docker compose config --quiet
docker compose build --pull
docker compose up -d
docker compose ps
docker compose logs backend --tail 100
```

Both services use `restart: unless-stopped`. Uvicorn reload is disabled by
default.

## 7. Verify backend

```bash
curl -f "http://127.0.0.1:${BACKEND_HOST_PORT:-8000}${API_HEALTH_PATH:-/health}"
curl -f "http://127.0.0.1:${BACKEND_HOST_PORT:-8000}${API_PREFIX:-/api/v1}/movies?limit=1"
```

Verify OpenAPI at the configured docs path. Register, complete onboarding,
record an interaction, and read it back through rating/reaction endpoints.

Guest movie loading must use the configured PopularMovies list and Movies
BatchGet. If the list is absent, the API returns 503 rather than scanning or
using bundled content.

## 8. Verify frontend

```bash
curl -f "http://127.0.0.1:${FRONTEND_HOST_PORT:-5173}"
docker compose logs frontend --tail 100
```

In the browser network panel, every backend request must start with
`VITE_API_URL`. Relative poster paths must use
`VITE_TMDB_POSTER_BASE_URL`.

## 9. Verify S3

```bash
docker compose exec -T backend python scripts/s3_dataset.py list raw
docker compose exec -T backend python scripts/s3_dataset.py list serving
```

The backend does not download these objects while serving HTTP requests.

## 10. Verify recommendations

- Guest: PopularMovies → BatchGet Movies.
- Returning user with valid canonical cache: RecommendationCache → BatchGet
  Movies.
- Missing/expired cache while SageMaker is disabled: HTTP 503.
- No response may contain a locally generated ranking.

## 11. Tests before release

```bash
docker compose exec -T backend \
  python -m unittest discover -s tests -p "test_*.py" -v
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run build
```

## 12. GitHub/EC2 deployment

Configure GitHub:

- secrets: `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY`
- repository variable: `EC2_APP_DIR`

Store `.env` securely on the target host. The deployment workflow does not
commit or generate production credentials.

## 13. Rollback

Deploy the previous git revision while preserving `.env`. Database schema and
table names must not be rolled back or recreated. For SageMaker, switch to the
previous endpoint configuration before re-enabling inference.
