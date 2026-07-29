# Frontend

The frontend is a React + Vite application for guest browsing, authenticated
interactions, onboarding, profiles, and Netflix-style movie discovery.

## Current responsibilities

- render public movie catalog and movie-detail routes
- render authentication, registration, onboarding, and profile experiences
- enforce guest and onboarding redirects before protected actions
- call the backend only through the centralized API client and feature services
- show loading and error states for API responses

The public catalog requests at most 100 Movies records. `MovieSection` renders
the first 20 as a responsive grid (four columns on desktop, approximately five
rows) and reveals the next 20 whenever the user selects `More film`. The whole
movie card is the navigation target; cards do not expose separate Watch or Rate
buttons.

## Movie detail

The public route `/movies/{movie_id}` loads canonical movie data through:

```text
MovieDetailPage
  -> useMovieDetail
  -> movieService
  -> apiClient
  -> GET /api/v1/movie/{movie_id}
```

The viewing page keeps the global header and presents these user-facing Movies
fields:

- `title`
- `release_year`
- `genres`
- `overview`
- `poster_path`
- `vote_average`
- `vote_count`
- `runtime`
- `original_language`
- `companies`
- `countries`
- `actors`
- `directors`

`movie_id` remains an internal routing and interaction identifier, and
`popularity` remains available in the API contract; neither is rendered in the
Movie Detail UI. Vote average, vote count, the five-star rating action, Like,
Dislike, and Sharing use a streaming-player-style layout. The aggregate vote
average and vote count sit directly below the movie title and outside the
action panel. The TMDB-style ten-point `vote_average` is converted to a
five-star display (`vote_average / 2`) while the API value remains unchanged.
The action panel contains a separate interactive five-star control. It loads
the authenticated user's latest rating through
`GET /users/me/ratings/{movie_id}`; unrated movies show empty stars, and a new
selection is shown only after the rating interaction is stored successfully.

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
the required `VITE_TMDB_POSTER_BASE_URL` value.

## Simulated player

Movies currently have no trailer field or video asset. Movie Detail therefore
uses the poster as the player artwork and never requests a video file.

`useSimulatedPlayback` owns the playback timer and exposes:

- play and pause state
- elapsed and total runtime in seconds
- seek/progress state
- automatic stop when the runtime is reached

The player is intentionally visual-only. Playback records one `watch/record`
interaction with value `0.6` when an authenticated user reaches 60%. A guest
is redirected to `/login` without starting playback.

## Interaction pipeline

`useMovieActions` supports click, watch, rating, reaction, and share. It maps
each UI action to the canonical `interaction_type`, `interaction_action`, and
required `interaction_value` fields. `interactionService` adds the session,
timestamp, and a request-scoped `Idempotency-Key`.

`useMovieRating` loads and owns the current user's selected star value. It
keeps aggregate movie votes separate from the personal rating interaction.
`useMovieReaction` owns the current Like/Dislike selection. The selected button
turns red only after persistence succeeds; selecting it again submits
`reaction/clear/0` and removes the highlight. Rating exposes an explicit Clear
action that submits `rating/clear/0`. The rating control exposes ten selectable
half-star steps, so values such as `3.5` fill exactly three and a half stars.
Both hooks reload the latest effective state from UserInteractions so the UI
remains consistent after refresh.

Network retries reuse the same request body and idempotency key. The backend
therefore returns the same `event_id` and DynamoDB `interaction_key` instead of
creating another interaction record.

## Frontend boundaries

- Components render state and forward user events.
- Hooks own navigation, asynchronous state, and playback behavior.
- Services own API operations.
- `apiClient` is the only frontend module that calls `fetch`.
- Movie Detail is public; rating, reaction, share, and simulated playback
  actions remain protected.

## Local development

```bash
cd frontend
npm install
npm run dev
```

## Environment variables

- `VITE_API_URL` — required backend API base URL, including `API_PREFIX`
- `VITE_TMDB_POSTER_BASE_URL` — required TMDB image base and size
- `VITE_HOST` — optional Vite development bind host
- `VITE_PORT` — optional Vite development port

`src/config/environment.ts` is the only frontend runtime URL configuration
module. It fails fast on missing or invalid URLs. Only `VITE_*` variables are
available to browser code; never place credentials or secrets in them.

See [project configuration](../docs/aws-configuration.md) for the full template
and Docker mapping.
