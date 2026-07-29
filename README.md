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
- cache miss: SageMakerRecommendationProvider
- before a compatible SageMaker endpoint exists: HTTP 503, never fabricated
  recommendations

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

## Configuration

```bash
cp .env.example .env
```

Fill the JWT secret, AWS identity/Region, five table names, popular list ID, S3
bucket/prefixes and frontend URL. Keep `.env` untracked.

The backend validates:

- AWS credential chain and caller identity
- all five table states and exact key schemas
- S3 bucket and prefix-list access
- enabled SageMaker endpoint state
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

SageMaker inference remains disabled until a compatible model is trained and
deployed. Enabling it later requires implementing only the provider's
`invoke_endpoint()` method; frontend, API, services and repositories stay
unchanged.
