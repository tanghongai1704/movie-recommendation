# Backend

The backend is a FastAPI service whose canonical domain model is aligned with
the five DynamoDB tables used by the movie recommendation system.

## Current responsibilities

- serve the existing API routes under `/api/v1`
- register and authenticate users with password hashing and JWT access tokens
- expose protected profile, onboarding, interaction, and recommendation flows
- expose canonical movie and recommendation response fields
- serve valid recommendation-cache entries before invoking the provider
- enrich cached movie references from the Movies repository
- record click, watch, rating, reaction, and share behavior in canonical
  idempotent DynamoDB records

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

See [DynamoDB Repository Layer](docs/repositories.md) for the one-repository-per-
table layout, CRUD contracts, configuration, and boundary rules.

See [Authentication Flow](../docs/architecture/authentication-flow.md) for user
states, JWT middleware, protected routes, and frontend redirects.

See [Interaction Pipeline](../docs/architecture/interaction-pipeline.md) for
the event contract, retry guarantees, and sequence diagrams.

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
  -> API generates deterministic event_id
  -> InteractionService
  -> UserInteraction
  -> UserInteractionsRepository
```

InteractionService owns interaction behavior only and does not invoke
recommendation logic. The repository uses a conditional create so an identical
retry resolves to the existing item instead of creating a duplicate.
Canonical writes use only `record`, `set`, and `clear`. Click and share store
`record/1`; the 60% watch milestone stores `record/0.6`; reactions store
`set/1`, `set/-1`, or `clear/0`; and ratings store `set/<rating>` or `clear/0`.
Set ratings range from `0.5` to `5.0` in `0.5` increments.

`GET /api/v1/users/me/ratings/{movie_id}` reads the authenticated user's
UserInteractions partition and returns the latest rating event for that movie,
or `null` when no rating exists. This read path does not change the DynamoDB
schema or write a derived rating record. The equivalent reaction projection is
available at `GET /api/v1/users/me/reactions/{movie_id}`.

Historical UserInteractions records are mapped through a read-only compatibility
model. It accepts the deployed legacy field shapes, infers missing actions, and
normalizes numeric movie IDs without writing the normalized representation back
to DynamoDB. Canonical writes remain strict and unchanged.

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
- `app/core/config.py` - typed application configuration sections
- `app/core/config_validation.py` - reusable environment/startup validators

## Local development

```bash
cd backend
python -m pip install -r requirements.txt
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Environment variables

The complete source of truth is
[AWS and application configuration](../docs/aws-configuration.md). Required
backend values include `JWT_SECRET_KEY`, `AWS_REGION`, the five canonical
`AWS_DYNAMODB_*_TABLE` variables and `AWS_S3_BUCKET`.

Startup validates credentials, URLs, AWS region, table names, S3 bucket, JWT,
logging, timeouts, retry settings and cache configuration. Legacy
`JWT_SECRET`/`AWS_DYNAMODB_TABLE_*` names remain temporary read aliases so
existing deployments can migrate without changing API behavior.

The composition root creates one configured DynamoDB resource and injects its
table handles into repositories. Repository CRUD operations do not contain
fallback resource names.

`ALLOW_LEGACY_DEV_LOGIN` does not rewrite Users records. When enabled, it
accepts only the exact `<user_id>#username`, `<user_id>@email.com`, and
`<user_id>#pass` combination on a schema-version-2 seed record. New
registrations always store PBKDF2 in the existing
`user_settings.password_hash` field. Seed identities are resolved by their
embedded `user_id` with `GetItem`, avoiding a full Users table scan without
adding an index or changing the table schema.
