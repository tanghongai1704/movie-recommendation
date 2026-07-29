# Backend

FastAPI service using the five deployed DynamoDB tables and real AWS SDK
clients.

## Architecture

```text
Router -> Service -> Repository
                  -> RecommendationProvider
```

- `app/models/`: DynamoDB persistence models
- `app/schemas/`: request/response and SageMaker DTOs
- `app/repositories/`: DynamoDB operations only
- `app/services/`: business behavior and enrichment
- `app/aws/`: AWS client validation and S3 tooling
- `app/api/`: HTTP transport

No router calls DynamoDB, S3 or SageMaker directly.

## Data flows

Guest movies:

```text
PopularMoviesRepository.GetItem
  -> MoviesRepository.BatchGetItem
  -> MovieResponse[]
```

Personalized recommendations:

```text
RecommendationCacheRepository.GetItem
  -> valid cache: MoviesRepository.BatchGetItem
  -> miss: SageMakerRecommendationProvider
```

The provider does not create local recommendations. Until its endpoint
invocation is implemented and enabled, cache misses return HTTP 503.

Interactions:

```text
InteractionCreate
  -> deterministic event_id
  -> InteractionService
  -> UserInteractionsRepository
  -> DynamoDB
```

## DynamoDB compatibility

Canonical models map to Movies, PopularMovies, Users, UserInteractions and
RecommendationCache. Deployed compatibility is read-only:

- numeric PopularMovies references are converted to string IDs in memory
- historical interaction fields/actions are normalized in memory
- cache records attributed to the retired local provider are not served

No compatibility read rewrites DynamoDB.

See [Domain Model](docs/domain-model.md) and
[Repository Layer](docs/repositories.md).

## Authentication

Registration and profile persistence use UsersRepository. Passwords use
PBKDF2-HMAC-SHA256 with per-user random salts and the configured iteration
count. JWT configuration comes exclusively from environment variables.

Guest, first-login and returning-user behavior is documented in
[Authentication Flow](../docs/architecture/authentication-flow.md).

## Configuration and startup

The composition root creates reusable DynamoDB, S3 and optional SageMaker
clients. With `AWS_VALIDATE_RESOURCES=True`, startup verifies:

- caller identity
- all five tables are `ACTIVE`
- exact partition/sort keys
- S3 bucket and prefix-list access
- enabled SageMaker endpoint is `InService`

See [Environment Variables](../docs/aws/environment.md).

## S3 operations

Backend request handlers do not load datasets. Operational transfers use:

```bash
python scripts/s3_dataset.py list raw
python scripts/s3_dataset.py upload raw /path/to/file
python scripts/s3_dataset.py download serving object.json /tmp/object.json
```

## Development and tests

```bash
cd backend
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
python -m unittest discover -s tests -p "test_*.py" -v
```

Native processes must receive the variables from `.env.example`. Docker is the
recommended path because it propagates the shared project environment.

## API stability

This AWS migration does not change route URLs, request schemas, success
response schemas, authentication states or the DynamoDB key schema. See
[API Contract](../docs/api/api-contract.md).
