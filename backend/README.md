# Backend

The backend is a FastAPI service whose canonical domain model is aligned with
the five DynamoDB tables used by the movie recommendation system.

## Current responsibilities

- serve the existing API routes under `/api/v1`
- handle the current authentication placeholder routes
- expose canonical movie and recommendation response fields
- serve valid recommendation-cache entries before invoking the provider
- enrich cached movie references from the Movies repository
- record click, watch, and rating behavior in canonical DynamoDB records

## Architecture

```text
Router -> Service -> Repository
                  -> RecommendationProvider
```

- `app/models/` defines strict DynamoDB persistence models.
- `app/schemas/` defines request and response DTOs.
- `app/repositories/` contains persistence operations only.
- `app/services/` contains application behavior and mapping.
- `app/api/` contains HTTP transport concerns.

No API URL was changed during the domain-model migration.

## Domain model

The backend recognizes exactly five persisted aggregates:

1. `Movie` maps to Movies.
2. `PopularMovie` maps to PopularMovies.
3. `User` maps to Users.
4. `UserInteraction` maps to UserInteractions.
5. `RecommendationCache` maps to RecommendationCache.

Movie and user identifiers are strings throughout the backend. Cross-table
references use `movie_id` and `user_id`; generic `id` fields are not used.

See [Domain Model and Entity Mapping](docs/domain-model.md) for the complete
field inventory, data flow, field mapping, and naming rules.

## Data flow

### Movie metadata

```text
Movies table -> MoviesRepository -> MovieService -> MovieResponse
```

### Recommendations

```text
RecommendationCacheRepository
  -> cache hit: movie IDs/scores/reasons -> MoviesRepository enrichment
  -> cache miss: RecommendationProvider -> normalized cache entry
  -> RecommendationResponse
```

RecommendationCache stores references and ranking data only. Movie metadata
remains owned by Movies.

### Interactions

```text
InteractionCreate
  -> InteractionService
  -> UserInteraction
  -> UserInteractionsRepository
```

InteractionService records behavior only and does not invoke recommendation
logic.

## Field naming convention

- Use `snake_case` in Python, JSON, and DynamoDB.
- Use explicit identifiers: `movie_id`, `user_id`, and `list_id`.
- Use `timestamp`, `generated_at`, `created_at`, and `last_active_at` for UTC
  date-time values.
- Use `expire_at` for the integer Unix timestamp consumed by DynamoDB TTL.
- Use plural names only for collections: `genres`, `movie_ids`, `items`.
- Persistence models reject undeclared fields.
- API-only fields must be documented and must not silently become DynamoDB
  attributes.

## Migration

See [Phase 1 Migration Summary](docs/migration-summary.md) for renamed fields,
compatibility behavior, data-migration requirements, and deferred work.

## Main entrypoint

- `app/main.py` - FastAPI application
- `app/api/v1/routes/` - existing API routes
- `app/services/` - business logic
- `app/repositories/` - DynamoDB and in-memory data access
- `app/models/` - canonical persistence models
- `app/schemas/` - request and response DTOs
- `app/core/config.py` - application configuration

## Local development

```bash
cd backend
python -m pip install -r requirements.txt
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Environment variables

- `LOG_LEVEL` - logging level, default `INFO`
- `DEBUG` - enables debug mode when set to `True`
- `AUTH_TOKEN_PREFIX` - token prefix used by the demo auth flow
- `AWS_REGION` - DynamoDB region
- `AWS_DYNAMODB_TABLE_INTERACTIONS` - UserInteractions table name
- `AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE` - RecommendationCache table name
- `RECOMMENDATION_CACHE_TTL_SECONDS` - application cache validity window
