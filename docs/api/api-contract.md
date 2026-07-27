# Stable API Contract

This document defines the frontend/backend interface for the movie recommendation system.
It is intentionally stable so the recommendation engine can change from mock data to SageMaker without changing the API shape.

Base URL:
- `http://127.0.0.1:8000/api/v1`

Authentication:
- All protected endpoints require a bearer token in the `Authorization` header.
- Format: `Authorization: Bearer <token>`

Common response envelope:
- Success responses return JSON objects or arrays as defined below.
- Error responses return a JSON object with an `error` field.

## 1. Authentication

### POST /auth/login

- Purpose: Authenticate a user and receive a token.
- Method: `POST`
- Auth: None
- Request body:

```json
{
  "username": "demo",
  "password": "password123"
}
```

- Query parameters: None
- Success response `200 OK`:

```json
{
  "access_token": "dummy-token-for-demo",
  "token_type": "bearer"
}
```

- Error response `401 Unauthorized`:

```json
{
  "error": "Invalid credentials"
}
```

- Status codes:
  - `200 OK`
  - `401 Unauthorized`
  - `422 Unprocessable Entity`
  - `500 Internal Server Error`

### GET /auth/me

- Purpose: Retrieve the authenticated user profile.
- Method: `GET`
- Auth: Required
- Request body: None
- Query parameters: None
- Success response `200 OK`:

```json
{
  "user_id": 1,
  "username": "demo",
  "role": "user"
}
```

- Error response `401 Unauthorized`:

```json
{
  "error": "Invalid token"
}
```

- Status codes:
  - `200 OK`
  - `401 Unauthorized`
  - `500 Internal Server Error`

## 2. Movies

### GET /movies

- Purpose: Retrieve a collection of movies. This endpoint is used by the UI as a movie catalog or recommendation feed.
- Method: `GET`
- Auth: Required
- Request body: None
- Query parameters:
  - `limit` (integer, optional, default: `20`)
  - `offset` (integer, optional, default: `0`)
  - `genre` (string, optional)
  - `sort_by` (string, optional, one of: `rating`, `year`, `title`)

- Success response `200 OK`:

```json
[
  {
    "id": 1,
    "title": "Midnight Horizon",
    "genre": "Sci-Fi Thriller",
    "year": 2025,
    "rating": 8.9,
    "description": "A brilliant pilot and a rogue AI race through a collapsing city.",
    "image_url": "https://example.com/poster.jpg"
  }
]
```

- Error response `401 Unauthorized`:

```json
{
  "error": "Invalid token"
}
```

- Status codes:
  - `200 OK`
  - `401 Unauthorized`
  - `400 Bad Request`
  - `500 Internal Server Error`

### GET /movies/{movie_id}

- Purpose: Retrieve a single movie by identifier.
- Method: `GET`
- Auth: Required
- Request body: None
- Query parameters: None
- Path parameters:
  - `movie_id` (integer, required)

- Success response `200 OK`:

```json
{
  "id": 1,
  "title": "Midnight Horizon",
  "genre": "Sci-Fi Thriller",
  "year": 2025,
  "rating": 8.9,
  "description": "A brilliant pilot and a rogue AI race through a collapsing city.",
  "image_url": "https://example.com/poster.jpg"
}
```

- Error response `404 Not Found`:

```json
{
  "error": "Movie not found"
}
```

- Status codes:
  - `200 OK`
  - `401 Unauthorized`
  - `404 Not Found`
  - `500 Internal Server Error`

## 3. User profile

### GET /users/me/profile

- Purpose: Retrieve the current user profile in a stable, application-facing shape.
- Method: `GET`
- Auth: Required
- Request body: None
- Query parameters: None
- Success response `200 OK`:

```json
{
  "user_id": 1,
  "username": "demo",
  "role": "user"
}
```

- Error response `401 Unauthorized`:

```json
{
  "error": "Invalid token"
}
```

- Status codes:
  - `200 OK`
  - `401 Unauthorized`
  - `500 Internal Server Error`

## 4. User interactions

### POST /users/me/interactions

- Purpose: Record a user interaction event used for future recommendation signals.
- Method: `POST`
- Auth: Required
- Request body:

```json
{
  "event_type": "like",
  "movie_id": 1,
  "rating": 4.5,
  "metadata": {
    "source": "ui"
  }
}
```

- Query parameters: None
- Success response `201 Created`:

```json
{
  "event_id": "evt_001",
  "user_id": 1,
  "event_type": "like",
  "movie_id": 1,
  "rating": 4.5,
  "created_at": "2026-07-27T12:00:00Z"
}
```

- Error response `400 Bad Request`:

```json
{
  "error": "Invalid interaction payload"
}
```

- Status codes:
  - `201 Created`
  - `400 Bad Request`
  - `401 Unauthorized`
  - `422 Unprocessable Entity`
  - `500 Internal Server Error`

## 5. Recommendations

### GET /recommendations

- Purpose: Retrieve personalized recommendations for the current user.
- Method: `GET`
- Auth: Required
- Request body: None
- Query parameters:
  - `user_id` (integer, optional)
  - `limit` (integer, optional, default: `10`)
  - `offset` (integer, optional, default: `0`)
  - `context` (string, optional, example: `home`)

- Success response `200 OK`:

```json
{
  "user_id": 1,
  "recommendations": [
    {
      "movie_id": 1,
      "title": "Midnight Horizon",
      "score": 0.98
    }
  ]
}
```

- Error response `400 Bad Request`:

```json
{
  "error": "Invalid recommendation request"
}
```

- Status codes:
  - `200 OK`
  - `400 Bad Request`
  - `401 Unauthorized`
  - `500 Internal Server Error`

## Stability principles

The contract above remains stable regardless of whether recommendations are served from:
- mock data
- a local ML service
- a SageMaker endpoint
- a future real-time inference system

The API contract is intentionally defined around stable concepts:
- authentication
- movie catalog access
- user profile access
- interaction recording
- recommendation delivery
