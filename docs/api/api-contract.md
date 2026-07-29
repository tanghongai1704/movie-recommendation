# Stable API Contract

Base URL: the configured `VITE_API_URL`. With `.env.example`, this is
`http://127.0.0.1:8000/api/v1`. The backend router prefix is configured by
`API_PREFIX`; both values must remain aligned.

Protected endpoints require:

```http
Authorization: Bearer <access_token>
```

Interaction writes additionally require:

```http
Idempotency-Key: <unique-request-key>
```

Validation and application errors use FastAPI's canonical `detail` field:

```json
{
  "detail": "Human-readable error"
}
```

## Access policy

| Capability | Guest | First Login | Returning User |
|---|---:|---:|---:|
| Browse movie list/detail | Yes | Yes | Yes |
| Register/login | Yes | N/A | N/A |
| View/update own profile | No | Yes | Yes |
| Record interactions | No | Yes | Yes |
| Rate, like, share, watchlist actions | No | Yes | Yes |
| Personalized recommendations | No | No | Yes |

Reaction and share events use the protected interaction endpoint. Watchlist is
not currently a product endpoint and must use the same registered-user
dependency when introduced.

## Authentication

### POST `/auth/register`

Creates a Users record, hashes the password, and returns a JWT session.

Auth: public

Request:

```json
{
  "email": "viewer@example.com",
  "username": "viewer",
  "password": "password123"
}
```

Response: `201 Created`

```json
{
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_in": 3600,
  "user": {
    "user_id": "a9a24f96-a3eb-449f-87f5-a4f43e79de19",
    "email": "viewer@example.com",
    "username": "viewer",
    "created_at": "2026-07-28T08:00:00Z",
    "onboarding_genres": [],
    "onboarding_completed": false,
    "last_active_at": "2026-07-28T08:00:00Z",
    "user_state": "first_login"
  }
}
```

Status codes:

- `201` account created
- `409` email or username already registered
- `422` invalid input
- `503` persistence unavailable

### POST `/auth/login`

Accepts either username or email in the `username` field.

Auth: public

Request:

```json
{
  "username": "viewer",
  "password": "password123"
}
```

Response: `200 OK`, using the same session shape as register.

Status codes:

- `200` authenticated
- `401` invalid credentials
- `422` invalid input
- `503` persistence unavailable

### POST `/auth/logout`

Auth: registered user

Response: `204 No Content`

The backend uses stateless, short-lived JWT access tokens. Logout confirms the
session is authenticated; the frontend then deletes its local token. The token
is not server-revoked and expires according to `exp`.

### GET `/auth/me`

Auth: registered user

Returns the current `UserProfileResponse`. `password_hash` is never exposed.

### GET `/users/me/profile`

Auth: registered user

Alias for the current profile response.

### PATCH `/users/me/profile`

Auth: registered user

Request may contain one or both editable fields:

```json
{
  "email": "new-email@example.com",
  "username": "new-username"
}
```

Response: updated `UserProfileResponse`.

Status codes:

- `200` updated
- `401` unauthenticated/invalid JWT
- `409` email or username already registered
- `422` invalid input
- `503` persistence unavailable

### PUT `/users/me/onboarding`

Auth: registered user

Request:

```json
{
  "onboarding_genres": ["Drama", "Science Fiction"]
}
```

Response: profile with:

```json
{
  "onboarding_completed": true,
  "user_state": "returning_user"
}
```

Between one and three unique, non-empty genres are required.

## Movies

### GET `/movies`

Auth: public

Returns canonical Movies records. Guests use this endpoint without a fabricated
identity or token. The optional `limit` query parameter defaults to `24` and
accepts values from `1` through `100`.

### GET `/movie/{movie_id}`

Auth: public

Returns one canonical Movies record or `404`.

Movie response fields:

```json
{
  "movie_id": "265330",
  "title": "Example title",
  "release_year": 2024,
  "genres": ["Drama", "Thriller"],
  "overview": "Canonical overview from the Movies table.",
  "poster_path": "/3LdEtd3IMJtw4zitgWZpIc60UFX.jpg",
  "vote_average": 7.8,
  "vote_count": 1234,
  "popularity": 42.5,
  "runtime": 100,
  "original_language": "en",
  "companies": ["Example Pictures"],
  "countries": ["United States"],
  "actors": ["Actor One"],
  "directors": ["Director One"]
}
```

`poster_path` is persisted and returned unchanged from Movies. The frontend
service resolves a relative TMDB path against its configured TMDB image base;
the backend does not call TMDB or duplicate poster assets.

## Interactions

### POST `/users/me/interactions`

Auth: registered user

Guest requests receive `401`. Both First Login and Returning User accounts may
record interactions.

Request:

```json
{
  "interaction_type": "rating",
  "interaction_action": "set",
  "movie_id": "1",
  "interaction_value": 4.5,
  "timestamp": "2026-07-28T08:10:00Z",
  "session_id": "web-session-id"
}
```

Supported type/action combinations:

| User action | `interaction_type` | `interaction_action` | `interaction_value` |
|---|---|---|---:|
| Open movie | `click` | `record` | `1` |
| Reach 60% watched | `watch` | `record` | `0.6` |
| Share movie | `share` | `record` | `1` |
| Like movie | `reaction` | `set` | `1` |
| Dislike movie | `reaction` | `set` | `-1` |
| Remove reaction | `reaction` | `clear` | `0` |
| Rate 4.5 stars | `rating` | `set` | `4.5` |
| Remove rating | `rating` | `clear` | `0` |

All canonical interaction requests require `interaction_value`. Watch values
are normalized progress ratios from `0` through `1`. Rating `set` values are
from `0.5` through `5.0` in `0.5` increments.

Response: `201 Created`

```json
{
  "user_id": "a9a24f96-a3eb-449f-87f5-a4f43e79de19",
  "interaction_key": "2026-07-28T08:10:00.000Z#1#f54f347c-d55f-57f8-a46f-61832bd53484",
  "event_id": "f54f347c-d55f-57f8-a46f-61832bd53484",
  "movie_id": "1",
  "interaction_type": "rating",
  "interaction_action": "set",
  "interaction_value": 4.5,
  "timestamp": "2026-07-28T08:10:00Z",
  "session_id": "web-session-id"
}
```

The API generates `event_id` from the authenticated user, idempotency key, and
canonical request payload. Repeating the same request with the same
`Idempotency-Key` returns the same `event_id` and `interaction_key` and leaves
only one DynamoDB item. Clients must reuse both the header and request
timestamp during retries.

Status codes:

- `201` interaction stored or identical retry resolved
- `401` unauthenticated/invalid JWT
- `422` missing idempotency key or invalid interaction fields
- `503` persistence unavailable

### GET `/users/me/ratings/{movie_id}`

Auth: registered user

Returns the authenticated user's most recent `rating` interaction for
the requested movie. This is a read-only projection of UserInteractions and
does not create or update any DynamoDB item.

Rated response:

```json
{
  "movie_id": "1",
  "rating": 4.0
}
```

When the user has not rated the movie, `rating` is `null`.

Status codes:

- `200` rating or explicit unrated state returned
- `401` unauthenticated/invalid JWT
- `503` persistence unavailable

### GET `/users/me/reactions/{movie_id}`

Auth: registered user

Returns the latest effective reaction after applying `set` and `clear` events.
The `reaction` value is `"like"`, `"dislike"`, or `null`.

```json
{
  "movie_id": "1",
  "reaction": "like"
}
```

## Personalized recommendations

### GET `/recommend/{user_id}`

Auth: Returning User

Rules:

- JWT must be valid.
- Token subject must resolve to a registered user.
- `onboarding_completed` must be `true`.
- Path `user_id` must equal the authenticated user ID.

Responses:

- `200` recommendation response
- `401` guest, invalid, or expired token
- `403` onboarding incomplete or user ID mismatch
- `502` endpoint returned an invalid/model-error response
- `503` DynamoDB, credentials, or SageMaker endpoint unavailable
- `504` SageMaker inference timed out

```json
{
  "user_id": "a9a24f96-a3eb-449f-87f5-a4f43e79de19",
  "recommendations": [
    {
      "movie_id": "278",
      "title": "The Shawshank Redemption",
      "score": 0.95,
      "reason_code": "similar_users"
    }
  ]
}
```

The response contract is independent of the active RecommendationProvider.
Guest movie browsing uses `/movies` and never calls SageMaker.
