# Architecture notes

## Current runtime flow

1. The frontend loads in the browser and calls the backend API from the React
   service layer. Public movie cards navigate to `/movies/{movie_id}`, where a
   movie-detail hook loads all canonical Movies fields and drives a poster-only
   simulated player. Relative TMDB poster paths are resolved to the configured
   `image.tmdb.org` URL by `movieService`.
2. FastAPI routes receive those requests and delegate to `MovieService`, which
   reads canonical metadata through `MoviesRepository` from DynamoDB.
3. `RecommendationService` checks DynamoDB for a valid per-user, per-scenario cache entry.
4. Cache hits resolve stored ordered movie IDs, scores and reason codes against
   the Movies table without invoking the provider.
5. Cache misses or expired/invalid entries invoke `MockRecommendationProvider` and write the result back to DynamoDB.
6. Protected interaction actions pass through the idempotent interaction
   pipeline and are stored in UserInteractions for future ML consumption.
7. The ML package is currently a service-oriented scaffold and is not yet connected to a production model.

## Request path example

```text
Browser -> React UI -> API client -> FastAPI route -> service -> repository/provider
```

## Current implementation boundaries

- Frontend: UI and API consumption
- Backend: REST API, JWT authentication, service layer, repository abstraction
- ML: future training/inference scaffolding
- Infrastructure: Docker Compose and deployment workflow

See [Interaction Pipeline](interaction-pipeline.md) for the write and retry
sequence diagrams.

## Configuration boundary

```text
.env / deployment environment
  -> backend validation and typed Settings
  -> app.main / app.container
  -> configured AWS repositories and services

VITE_* environment
  -> frontend config module
  -> centralized API and poster URL consumers
```

See [AWS configuration](../aws-configuration.md),
[AWS resource mapping](../aws-resource-mapping.md), and
[setup verification](../setup/aws-verification.md). S3 and SageMaker values are
future configuration only; neither service is invoked by the current backend.
