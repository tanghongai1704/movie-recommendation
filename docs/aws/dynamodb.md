# DynamoDB

The deployed DynamoDB schema is immutable. Repositories perform persistence
only; routers and UI code never call DynamoDB.

## Tables and keys

| Table | Partition key | Sort key | Repository |
|---|---|---|---|
| Movies | `movie_id` | — | `MoviesRepository` |
| PopularMovies | `list_id` | — | `PopularMoviesRepository` |
| Users | `user_id` | — | `UsersRepository` |
| UserInteractions | `user_id` | `interaction_key` | `UserInteractionsRepository` |
| RecommendationCache | `user_id` | `scenario` | `RecommendationCacheRepository` |

The deployed tables currently have no GSIs. The application does not assume
that the previously recommended interaction indexes exist.

## Attribute mapping

### Movies

`movie_id`, `title`, `release_year`, `genres`, `overview`, `poster_path`,
`vote_average`, `vote_count`, `popularity`, `runtime`, `original_language`,
`companies`, `countries`, `actors`, and `directors`.

Movies is the metadata source of truth. No other table duplicates these fields.

### PopularMovies

`list_id`, `ranking_type`, `genre`, `movie_ids`, `scores`, and `generated_at`.
The selected list is configured with `AWS_DYNAMODB_POPULAR_LIST_ID`.

Some deployed genre lists contain numeric `movie_ids`, while Movies uses string
keys. `PopularMovie` normalizes those references to strings only in memory.
The repository never rewrites the source item.

### Users

The deployed schema stores `user_id`, `recent_movie_ids`, `schema_version`,
`onboarding_genres`, and the embedded `user_settings` map containing `email`,
`username`, `password_hash`, and `created_at`. Authentication keeps this shape
and does not create guest records.

### UserInteractions

Canonical writes contain:

- `user_id`
- `interaction_key = timestamp#movie_id#event_id`
- `event_id`
- `movie_id`
- `interaction_type`
- `interaction_action`
- `interaction_value`
- `timestamp`
- `session_id`

The read model accepts historical records without updating them.

### RecommendationCache

Canonical records contain `user_id`, `scenario`, ordered `items`,
`model_version`, `generated_at`, and TTL field `expire_at`. Each item contains
only `movie_id`, `score`, and `reason_code`.

Legacy cache records attributed to a removed local provider are never served.
They remain untouched until an explicitly approved data-cleanup operation.

## Access patterns

| Use case | DynamoDB operation |
|---|---|
| Guest home ranking | `GetItem` PopularMovies, then `BatchGetItem` Movies |
| Movie detail | `GetItem` Movies |
| General repository listing | Paginated `Scan` Movies |
| Register/update user | Conditional `PutItem` Users |
| Token profile | `GetItem` Users |
| Login/identity uniqueness | `GetItem` for deterministic legacy ID, otherwise paginated Users `Scan` because no identity GSI exists |
| Record interaction | Conditional `PutItem` UserInteractions |
| User rating/reaction history | `Query` UserInteractions by `user_id` |
| Personalized cache | `GetItem` RecommendationCache |
| Cache enrichment | `BatchGetItem` Movies |
| Offline full interaction export | Paginated `Scan`; switch to DynamoDB export-to-S3 at scale |

`Query` is used whenever the deployed key schema supports it. A table scan is
unavoidable for case-insensitive username/email lookup because Users has only
`user_id`; adding an identity GSI would be an infrastructure/schema decision
outside this migration.

## Serialization and nulls

- Python floats are converted to DynamoDB `Decimal`.
- Datetimes are serialized as ISO-8601 UTC strings.
- Optional domain fields accept `null` only where the deployed data allows it.
- API DTOs are never persisted directly.
- `BatchGetItem` is chunked at 100 keys, retries unprocessed keys, restores the
  ranking order, and omits references that do not exist.

## Write semantics

- `create` uses `attribute_not_exists`.
- `update` requires the key to exist.
- cache `upsert` replaces one `(user_id, scenario)` record.
- interaction retries reuse the same deterministic event ID and conditional key.
- repository errors are translated to HTTP only by routers.

## Verification

```bash
aws dynamodb describe-table \
  --table-name "$AWS_DYNAMODB_INTERACTIONS_TABLE" \
  --region "$AWS_REGION" \
  --query "Table.{Status:TableStatus,Keys:KeySchema,Indexes:GlobalSecondaryIndexes[].IndexName}"

aws dynamodb get-item \
  --table-name "$AWS_DYNAMODB_POPULAR_TABLE" \
  --key "{\"list_id\":{\"S\":\"$AWS_DYNAMODB_POPULAR_LIST_ID\"}}" \
  --region "$AWS_REGION"

aws dynamodb scan \
  --table-name "$AWS_DYNAMODB_MOVIES_TABLE" \
  --select COUNT \
  --region "$AWS_REGION"
```

The backend performs a read-only startup check of all table states and key
schemas when `AWS_VALIDATE_RESOURCES=True`.
