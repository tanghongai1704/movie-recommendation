# Stable API Contract

Base URL: `http://127.0.0.1:8000/api/v1`

Protected endpoints require:

```http
Authorization: Bearer <access_token>
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

Like, share, and watchlist APIs are not currently product endpoints. When
introduced, they must use the same registered-user dependency as interactions.

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

At least one unique, non-empty genre is required.

## Movies

### GET `/movies`

Auth: public

Returns canonical Movies records. Guests use this endpoint without a fabricated
identity or token.

### GET `/movie/{movie_id}`

Auth: public

Returns one canonical Movies record or `404`.

Movie response fields:

```json
{
  "movie_id": "1",
  "title": "Midnight Horizon",
  "release_year": 2025,
  "genres": ["Science Fiction", "Thriller"],
  "overview": "A brilliant pilot and a rogue AI race through a collapsing city.",
  "poster_path": "https://example.com/poster.jpg",
  "vote_average": 8.9,
  "vote_count": 12400,
  "popularity": 94.1,
  "runtime": 132,
  "original_language": "en",
  "companies": ["Northstar Pictures"],
  "countries": ["United States"],
  "actors": ["Avery Chen"],
  "directors": ["Jordan Vale"]
}
```

## Interactions

### POST `/users/me/interactions`

Auth: registered user

Guest requests receive `401`. Both First Login and Returning User accounts may
record interactions.

Request:

```json
{
  "interaction_type": "rating",
  "movie_id": "1",
  "interaction_value": 4.5,
  "session_id": "web-session-id"
}
```

Supported interaction types: `click`, `watch`, `rating`.

Response: `201 Created`

```json
{
  "user_id": "a9a24f96-a3eb-449f-87f5-a4f43e79de19",
  "interaction_key": "2026-07-28T08:10:00Z#1",
  "movie_id": "1",
  "interaction_type": "rating",
  "interaction_value": 4.5,
  "timestamp": "2026-07-28T08:10:00Z",
  "session_id": "web-session-id"
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

The response contract is independent of the active RecommendationProvider.
