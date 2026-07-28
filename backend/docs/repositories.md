# DynamoDB Repository Layer

## Purpose

The repository layer is the only backend layer that performs DynamoDB
operations. It maps canonical domain models to DynamoDB records and maps
DynamoDB records back to canonical domain models.

Repositories do not:

- make business decisions
- create API response objects
- call recommendation providers
- rank or filter recommendations
- control authentication or authorization
- own environment-specific table names

## Module layout

```text
app/repositories/
  dynamodb_base.py
  movies_repository.py
  popular_movies_repository.py
  users_repository.py
  user_interactions_repository.py
  recommendation_cache_repository.py
  movie_repository.py
```

`dynamodb_base.py` contains serialization, connection, pagination, conditional
write, get, query, scan, and delete mechanics shared across repositories.

`movie_repository.py` contains the read abstraction and in-memory implementation
used by the current mock provider. It is not a DynamoDB table implementation.

## Repository contracts

### MoviesRepository

| Method | Persistence operation |
|---|---|
| `create(movie)` | Conditionally create a Movies item |
| `get(movie_id)` | Read one Movies item |
| `list_all()` | Scan all Movies pages |
| `update(movie)` | Conditionally replace an existing Movies item |
| `delete(movie_id)` | Delete one Movies item |

### PopularMoviesRepository

| Method | Persistence operation |
|---|---|
| `create(popular_movies)` | Conditionally create a ranking list |
| `get(list_id)` | Read one ranking list |
| `list_all()` | Scan all ranking-list pages |
| `update(popular_movies)` | Conditionally replace an existing list |
| `delete(list_id)` | Delete one list |

### UsersRepository

| Method | Persistence operation |
|---|---|
| `create(user)` | Conditionally create a registered user |
| `get(user_id)` | Read one registered user |
| `list_all()` | Scan all user pages |
| `update(user)` | Conditionally replace an existing user |
| `delete(user_id)` | Delete one registered user |

### UserInteractionsRepository

| Method | Persistence operation |
|---|---|
| `create(interaction)` | Conditionally create one interaction |
| `get(user_id, interaction_key)` | Read one interaction |
| `list_by_user(user_id)` | Query all interaction pages for one user |
| `update(interaction)` | Conditionally replace an existing interaction |
| `delete(user_id, interaction_key)` | Delete one interaction |

### RecommendationCacheRepository

| Method | Persistence operation |
|---|---|
| `create(cache_entry)` | Conditionally create one cache entry |
| `get(user_id, scenario)` | Read one cache entry |
| `update(cache_entry)` | Conditionally replace an existing entry |
| `upsert(cache_entry)` | Create or replace an entry |
| `delete(user_id, scenario)` | Delete one cache entry |

`upsert` is a persistence operation. Cache validity, ranking, model selection,
metadata enrichment, and scenario selection remain service responsibilities.

## Configuration

Repository constructors require both `table_name` and `region_name`. They do not
contain fallback resource names.

The application composition layer supplies values from:

- `AWS_REGION`
- `AWS_DYNAMODB_TABLE_MOVIES`
- `AWS_DYNAMODB_TABLE_POPULAR`
- `AWS_DYNAMODB_TABLE_USERS`
- `AWS_DYNAMODB_TABLE_INTERACTIONS`
- `AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE`

Startup fails with a clear configuration error when a required variable is
missing or empty.

## Domain mapping

Repositories accept and return models from `app.models`. They never import from
`app.schemas`, so API response shape changes cannot affect DynamoDB records.

| Repository | Domain model |
|---|---|
| MoviesRepository | `Movie` |
| PopularMoviesRepository | `PopularMovie` |
| UsersRepository | `User` |
| UserInteractionsRepository | `UserInteraction` |
| RecommendationCacheRepository | `RecommendationCache` |

Full-item `update` operations intentionally replace the stored canonical item.
Partial update semantics belong in a separately reviewed repository contract
and are not inferred from API patch requests.

## Error behavior

AWS SDK, credential, DynamoDB client, and domain-validation failures are exposed
to services as `DynamoDBRepositoryError`. Repositories do not translate these
errors into HTTP status codes or API error payloads.

## Import boundary

Repository classes are imported directly from their table-specific modules.
The former `app.services.dynamodb` repository location has been removed so
persistence code cannot drift back into the service layer.
