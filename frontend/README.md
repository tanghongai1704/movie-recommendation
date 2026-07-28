# Frontend

The frontend is a React + Vite application for guest browsing, authenticated
interactions, onboarding, profiles, and Netflix-style movie discovery.

## Current responsibilities

- render public movie catalog and movie-detail routes
- render authentication, registration, onboarding, and profile experiences
- enforce guest and onboarding redirects before protected actions
- call the backend only through the centralized API client and feature services
- show loading and error states for API responses

The initial public catalog uses the backend's bounded default of 24 Movies
records instead of requesting the full DynamoDB table.

## Movie detail

The public route `/movies/{movie_id}` loads canonical movie data through:

```text
MovieDetailPage
  -> useMovieDetail
  -> movieService
  -> apiClient
  -> GET /api/v1/movie/{movie_id}
```

The page displays every Movies field:

- `movie_id`
- `title`
- `release_year`
- `genres`
- `overview`
- `poster_path`
- `vote_average`
- `vote_count`
- `popularity`
- `runtime`
- `original_language`
- `companies`
- `countries`
- `actors`
- `directors`

Missing scalar or collection values receive an explicit unavailable state. A
missing poster uses a local SVG placeholder.

TMDB stores `poster_path` as a relative file path such as
`/3LdEtd3IMJtw4zitgWZpIc60UFX.jpg`. `movieService` converts that value to a
browser-ready URL before returning movie data to hooks:

```text
https://image.tmdb.org/t/p/w500/3LdEtd3IMJtw4zitgWZpIc60UFX.jpg
```

Absolute poster URLs remain unchanged. Broken or missing images fall back to
the local placeholder. Override the image base and size with
`VITE_TMDB_POSTER_BASE_URL`; the default is
`https://image.tmdb.org/t/p/w500`.

## Simulated player

Movies currently have no trailer field or video asset. Movie Detail therefore
uses the poster as the player artwork and never requests a video file.

`useSimulatedPlayback` owns the playback timer and exposes:

- play and pause state
- elapsed and total runtime in seconds
- seek/progress state
- automatic stop when the runtime is reached

The player is intentionally visual-only. Starting playback records a `watch`
interaction for an authenticated user. A guest is redirected to `/login`
without starting playback.

## Frontend boundaries

- Components render state and forward user events.
- Hooks own navigation, asynchronous state, and playback behavior.
- Services own API operations.
- `apiClient` is the only frontend module that calls `fetch`.
- Movie Detail is public; rating and simulated playback remain protected.

## Local development

```bash
cd frontend
npm install
npm run dev
```

## Environment variables

- `VITE_API_URL` — backend API base URL, default
  `http://127.0.0.1:8000/api/v1`
- `VITE_TMDB_POSTER_BASE_URL` — TMDB image base and size, default
  `https://image.tmdb.org/t/p/w500`
