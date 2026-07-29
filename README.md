# Movie Recommendation System

A Netflix-style movie application with a React/Vite frontend, FastAPI backend,
five DynamoDB tables and an ML submodule prepared for future AWS training and
inference work.

## Current runtime

```text
Browser
  -> centralized frontend API client
  -> FastAPI router
  -> service
  -> DynamoDB repository / recommendation provider
  -> stable API response
```

The current backend uses real DynamoDB repositories for Movies, Users,
UserInteractions and RecommendationCache. Recommendation cache misses still use
`MockRecommendationProvider`; this configuration phase does not integrate
SageMaker or change recommendation behavior.

## Features

- Guest movie browsing and movie detail
- JWT registration, login, profile and onboarding
- First-login and returning-user routing
- Click, watch, rating, reaction and share interaction storage
- Per-user recommendation cache
- Poster-based simulated playback
- Frontend services/hooks with no direct component networking

## Repository structure

```text
frontend/       React, Vite and TypeScript
backend/        FastAPI services, repositories, models and tests
docs/           API, architecture, configuration and setup documentation
ml/             Independent recommendation-system Git submodule
docker-compose.yml
.env.example
```

## Configuration

Configuration is environment-driven and validated before backend startup.

1. Copy `.env.example` to `.env`.
2. Fill the JWT secret, AWS region, five DynamoDB table names and S3 bucket.
3. Provide AWS credentials through an IAM role, workload identity, AWS
   SSO/profile, or temporary untracked local credentials.
4. Keep all real secrets and resource identifiers out of git.

Canonical DynamoDB variables:

- `AWS_DYNAMODB_MOVIES_TABLE`
- `AWS_DYNAMODB_POPULAR_TABLE`
- `AWS_DYNAMODB_USERS_TABLE`
- `AWS_DYNAMODB_INTERACTIONS_TABLE`
- `AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE`

See:

- [Configuration source of truth](docs/aws-configuration.md)
- [AWS resource mapping](docs/aws-resource-mapping.md)
- [AWS and Docker verification](docs/setup/aws-verification.md)
- [Configuration migration report](docs/configuration-migration-report.md)

## Docker

```bash
docker compose config --quiet
docker compose up --build
```

Default local endpoints from `.env.example`:

- Frontend: `http://127.0.0.1:5173`
- Backend health: `http://127.0.0.1:8000/health`
- API documentation: `http://127.0.0.1:8000/docs`

Host ports, container ports, bind hosts, reload behavior and healthcheck
settings are configurable through `.env`.

## Native development

Backend:

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

Native processes must receive the same environment variables documented in
`.env.example`.

## Verification

```bash
docker compose exec -T backend python -m unittest discover -s tests -v
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run build
```

## Documentation

- [API contract](docs/api/api-contract.md)
- [Architecture](docs/architecture/README.md)
- [Authentication flow](docs/architecture/authentication-flow.md)
- [Interaction pipeline](docs/architecture/interaction-pipeline.md)
- [Backend domain model](backend/docs/domain-model.md)
- [Repository layer](backend/docs/repositories.md)

## Deployment

The GitHub workflow builds frontend/backend and deploys to an externally managed
EC2 host. Configure GitHub secrets `EC2_HOST`, `EC2_USER`, `EC2_SSH_KEY` and
repository variable `EC2_APP_DIR`. Runtime AWS resources and IAM policies are
provisioned outside this repository.
