# Backend Domain Model and Entity Mapping

## Purpose

This document defines the backend's canonical field names and types. The five
DynamoDB table schemas are the persistence source of truth. Transport DTOs may
expose derived fields, but they must not redefine persisted entity fields.

## Entity mapping

| DynamoDB table | Domain model | Repository |
|---|---|---|
| Movies | `app.models.movie.Movie` | `MoviesRepository` |
| PopularMovies | `app.models.popular_movie.PopularMovie` | `PopularMoviesRepository` |
| Users | `app.models.user.User` | `UsersRepository` |
| UserInteractions | `app.models.user_interaction.UserInteraction` | `UserInteractionsRepository` |
| RecommendationCache | `app.models.recommendation_cache.RecommendationCache` | `RecommendationCacheRepository` |

Repositories accept and return typed domain models. Raw DynamoDB dictionaries
are confined to repository serialization and deserialization.

## Domain model

### Movie

| Field | Type | Meaning |
|---|---|---|
| `movie_id` | `str` | Movies partition key and cross-table movie reference |
| `title` | `str` | Display title |
| `release_year` | `int \| None` | Release year when known |
| `genres` | `list[str]` | Normalized genres |
| `overview` | `str` | Movie synopsis |
| `poster_path` | `str \| None` | Poster path or URL |
| `vote_average` | `float` | Aggregate vote average |
| `vote_count` | `int` | Aggregate vote count |
| `popularity` | `float` | Source popularity value |
| `runtime` | `int \| None` | Runtime in minutes |
| `original_language` | `str` | Original language code |
| `companies` | `list[str]` | Embedded production companies |
| `countries` | `list[str]` | Embedded production countries |
| `actors` | `list[str]` | Embedded actor names |
| `directors` | `list[str]` | Embedded director names |

### PopularMovie

| Field | Type | Meaning |
|---|---|---|
| `list_id` | `str` | PopularMovies partition key |
| `ranking_type` | `str` | Ranking strategy |
| `genre` | `str \| None` | Optional genre scope |
| `movie_ids` | `list[str]` | Ordered Movies references |
| `scores` | `list[float]` | Scores aligned with `movie_ids` |
| `generated_at` | `datetime` | UTC generation time |

PopularMovies never duplicates movie titles, posters, or other metadata.

### User

| Field | Type | Meaning |
|---|---|---|
| `user_id` | `str` | Users partition key |
| `recent_movie_ids` | `list[str]` | Snapshot of up to 100 recently interacted movie IDs |
| `schema_version` | `int` | Deployed Users item schema version |
| `onboarding_genres` | `list[str] \| None` | Null before onboarding; selected genres afterwards |
| `user_settings` | `UserSettings` | Embedded account and audit settings |

`UserSettings` contains:

| Field | Type | Meaning |
|---|---|---|
| `email` | `str` | Account email |
| `username` | `str` | Public username |
| `password_hash` | `str` | PBKDF2 credential or restricted legacy dev seed value |
| `created_at` | `datetime` | UTC account creation time |

`onboarding_completed` is derived from whether `onboarding_genres` contains at
least one value. `last_active_at` is not persisted by the deployed schema; the
stable API response uses `user_settings.created_at` as its audit fallback.
Login is read-only and never rewrites a Users item. `password_hash` remains
persistence-only and is excluded from API profile responses. Guest users have
no User record.

### UserInteraction

| Field | Type | Meaning |
|---|---|---|
| `user_id` | `str` | UserInteractions partition key |
| `interaction_key` | `str` | Sort key formatted as `timestamp#movie_id#event_id` |
| `event_id` | `UUID` | API-generated idempotent event identifier |
| `movie_id` | `str` | Movies reference |
| `interaction_type` | `click \| watch \| rating \| reaction \| share` | Behavior category |
| `interaction_action` | `InteractionAction` | Concrete action within the category |
| `interaction_value` | `float \| None` | Canonical numeric signal; null remains readable only for legacy events |
| `timestamp` | `datetime` | UTC event time |
| `session_id` | `str` | Client session grouping key |

Canonical writes use `record`, `set`, and `clear`. Click and share use
`record/1`; watch uses `record` with a `0..1` progress ratio; rating uses
`set/0.5..5` in half-star increments or `clear/0`; and reaction uses `set/1`,
`set/-1`, or `clear/0`.
Legacy action values remain deserializable so existing DynamoDB events can
still be read, but new API requests cannot write them.

### RecommendationCache

| Field | Type | Meaning |
|---|---|---|
| `user_id` | `str` | RecommendationCache partition key |
| `scenario` | `str` | RecommendationCache sort key |
| `items` | `list[RecommendationCacheItem]` | Ordered ranking output |
| `model_version` | `str` | Provider/model version |
| `generated_at` | `datetime` | UTC generation time |
| `expire_at` | `int` | Unix epoch expiration time |

Each cache item contains only:

| Field | Type | Meaning |
|---|---|---|
| `movie_id` | `str` | Movies reference |
| `score` | `float` | Ranking score |
| `reason_code` | `str` | Stable explanation code |

Movie metadata is enriched from Movies after a cache read.

## API DTO mapping

| DTO | Domain relationship |
|---|---|
| `MovieResponse` | Canonical public representation of `Movie` |
| `PopularMovieResponse` | Canonical representation of `PopularMovie` |
| `UserProfileResponse` | Safe `User` representation without `password_hash` |
| `InteractionCreate` | Client-writable subset of `UserInteraction` |
| `InteractionResponse` | Canonical persisted interaction |
| `RecommendationItem` | `MovieResponse` enriched with score and reason code |
| `RecommendationResponse` | User-scoped ordered recommendation envelope |

User responses contain a derived `user_state` field. It is `first_login` when
onboarding is incomplete and `returning_user` after completion. The value is not
stored separately in Users.

## Field mapping

| Legacy field | Canonical field | Migration behavior |
|---|---|---|
| `id` | `movie_id` | Removed from backend models and output |
| `year` | `release_year` | Removed |
| `genre` on a movie | `genres` | Replaced with a string list |
| `description` | `overview` | Removed |
| `image_url` | `poster_path` | Removed |
| `rating` on a movie | `vote_average` | Removed |
| `event_type` | `interaction_type` | Accepted temporarily as request-only alias |
| `rating` on an interaction | `interaction_value` | Accepted temporarily as request-only alias |
| `created_at` on an interaction | `timestamp` | Removed from new records |
| `metadata` | none | Rejected from canonical interaction requests |
| `movie_ids` in cache | `items[].movie_id` | Replaced |
| `movies` in cache | none | Removed; metadata comes from Movies |
| `cached_at` | `generated_at` | Replaced |
| `expires_at` | `expire_at` | Replaced |
| `provider` | `model_version` | Replaced with an explicit version |
| Flat user account fields | `user_settings.*` | Users account fields remain embedded |

## Field naming convention

1. Persisted and public entity fields use `snake_case`.
2. Identifiers always include their entity name.
3. All cross-table movie references use `movie_id: str`.
4. All user ownership references use `user_id: str`.
5. UTC date-time fields use semantic `*_at` names or `timestamp`.
6. DynamoDB TTL uses `expire_at` as Unix epoch seconds.
7. Collection names are plural.
8. Persistence models reject undeclared fields.
9. API-only derived fields must be explicitly documented.
10. Repositories never rename fields.

## Data flow

### Write path

```text
HTTP request
  -> request DTO validation
  -> service creates canonical domain model
  -> repository serializes canonical names
  -> DynamoDB
```

### Read path

```text
DynamoDB
  -> repository deserializes canonical domain model
  -> service applies business logic
  -> response DTO
  -> JSON response
```

### Recommendation cache path

```text
RecommendationCache.items
  -> ordered movie_id lookup in Movies
  -> Movie metadata enrichment
  -> score/reason attachment
  -> RecommendationResponse
```

## Detailed DynamoDB table documentation placeholders

The following sections are intentionally reserved for a later infrastructure
milestone.

### Movies table details

TODO: Document capacity, indexes, import ownership, backup, and operational
access patterns.

### PopularMovies table details

TODO: Document list generation jobs, refresh cadence, and consistency rules.

### Users table details

TODO: Document identity indexes, uniqueness enforcement, encryption, and access
patterns.

### UserInteractions table details

TODO: Document both GSIs, retention, export, and ML consumption patterns.

### RecommendationCache table details

TODO: Document TTL configuration, scenarios, invalidation, and model-version
rollout rules.
