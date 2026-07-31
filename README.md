# Movie Recommendation System

A React/Vite and FastAPI movie application backed by real AWS services.

## Runtime architecture

```text
Browser
  -> centralized frontend services
  -> FastAPI Router
  -> Service
  -> DynamoDB Repository / RecommendationProvider
  -> AWS
```

The five configured DynamoDB tables are Movies, PopularMovies, Users,
UserInteractions and RecommendationCache. S3 is the durable dataset/artifact
store. The backend never serves bundled movie data or locally generated
rankings.

Recommendation behavior:

- guest home: PopularMovies → BatchGet Movies
- returning-user cache hit: RecommendationCache → BatchGet Movies
- cache miss: Users/UserInteractions → SageMaker Runtime → BatchGet Movies
- endpoint unavailable: controlled error, never fabricated recommendations

## Features

- guest movie browsing and movie detail
- JWT registration, login, profile and onboarding
- first-login and returning-user routing
- click, watch, rating, reaction and share interactions
- DynamoDB recommendation cache
- poster-based simulated playback
- centralized frontend API services and hooks

## Repository structure

```text
frontend/       React, Vite and TypeScript
backend/        FastAPI, AWS composition, repositories, services and tests
docs/           API, architecture and AWS deployment documentation
ml/             Independent ML Git submodule with S3/SageMaker tooling
docker-compose.yml
.env.example
```

## Create and configure `.env`

The repository contains a safe configuration template at `.env.example`.
Create a local `.env` from that template before starting the application.

PowerShell:

```powershell
Copy-Item .env.example .env
```

Command Prompt:

```bat
copy .env.example .env
```

macOS, Linux, or Git Bash:

```bash
cp .env.example .env
```

Open `.env` and review the following required settings:

1. Generate a JWT secret containing at least 32 random bytes:

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```

   Paste the generated value into `JWT_SECRET_KEY`. Generate a different secret
   for every environment.

2. Set `AWS_REGION` and `AWS_DEFAULT_REGION` to the same AWS Region.

3. Choose exactly one AWS credential method:

   - local Docker: fill `AWS_ACCESS_KEY_ID`,
     `AWS_SECRET_ACCESS_KEY`, and `AWS_SESSION_TOKEN` when required;
   - EC2/ECS IAM role: leave all access-key fields blank so boto3 uses the
     workload role.

4. Verify the five DynamoDB table names and the existing PopularMovies
   `list_id`:

   - `AWS_DYNAMODB_MOVIES_TABLE`
   - `AWS_DYNAMODB_POPULAR_TABLE`
   - `AWS_DYNAMODB_USERS_TABLE`
   - `AWS_DYNAMODB_INTERACTIONS_TABLE`
   - `AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE`
   - `AWS_DYNAMODB_POPULAR_LIST_ID`

5. Verify `AWS_S3_BUCKET` and every configured S3 prefix.

6. Configure SageMaker:

   - when a compatible endpoint exists, set `AWS_SAGEMAKER_ENABLED=True` and
     provide `AWS_SAGEMAKER_ENDPOINT_NAME`;
   - when it is unavailable, set `AWS_SAGEMAKER_ENABLED=False` and leave the
     endpoint name blank. Guest browsing remains available, while personalized
     cache misses return a controlled service-unavailable response.

7. Verify `VITE_API_URL`, `VITE_TMDB_POSTER_BASE_URL`, CORS origins, and the
   frontend/backend ports.

Check the selected AWS identity without printing credentials:

```bash
aws sts get-caller-identity --region "<AWS_REGION>"
```

Validate the Compose configuration before building:

```bash
docker compose config --quiet
```

The command should exit without output. The backend then validates the AWS
identity, all five DynamoDB table states and key schemas, S3 access, and the
optional SageMaker endpoint health during startup.

Never commit `.env`. It may contain JWT secrets, temporary AWS credentials,
account-specific resource names, and private endpoints. `.gitignore` already
excludes it; verify with:

```bash
git status --short
```

Docker does not mount operating-system-specific AWS configuration directories.
Local credentials come only from the untracked `.env`. On EC2/ECS, leave those
values blank and use an IAM role.

The backend validates:

- AWS credential chain and caller identity
- all five table states and exact key schemas
- S3 bucket and prefix-list access
- enabled SageMaker endpoint state as a non-blocking health warning
- API, JWT, URL, timeout, retry and logging settings

See [Environment Variables](docs/aws/environment.md).

## Docker

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Default local URLs:

- frontend: `http://127.0.0.1:5173`
- backend health: `http://127.0.0.1:8000/health`
- OpenAPI: `http://127.0.0.1:8000/docs`

## Verification

```bash
docker compose exec -T backend \
  python -m unittest discover -s tests -p "test_*.py" -v
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run build
```

## Documentation

- [AWS Setup](docs/aws/aws-setup.md)
- [DynamoDB](docs/aws/dynamodb.md)
- [Amazon S3](docs/aws/s3.md)
- [SageMaker](docs/aws/sagemaker.md)
- [Environment Variables](docs/aws/environment.md)
- [Project Deployment](docs/aws/project-deployment.md)
- [AWS Resource Mapping](docs/aws/resource-mapping.md)
- [AWS Migration Report](docs/aws-migration-report.md)
- [API Contract](docs/api/api-contract.md)
- [Architecture](docs/architecture/README.md)
- [Authentication](docs/architecture/authentication-flow.md)
- [Interaction Pipeline](docs/architecture/interaction-pipeline.md)

SageMaker Runtime integration is implemented in the provider and keeps the
existing frontend API contract. See the SageMaker guide for the verified model
request/response contract, endpoint diagnostics, cache behavior, and the
documented similar-movies serving limitation.
