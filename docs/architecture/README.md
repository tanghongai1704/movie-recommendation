# Architecture

## Runtime

```text
React component
  -> feature hook
  -> centralized frontend service
  -> apiClient
  -> FastAPI router
  -> service
  -> repository/provider
  -> AWS
```

Components render state and dispatch actions. They do not call `fetch`, Axios
or backend URLs directly.

## Movie flow

```text
Guest / home
  -> MovieService
  -> PopularMovieService
  -> PopularMoviesRepository.GetItem
  -> MoviesRepository.BatchGetItem
  -> MovieResponse[]
```

Movie detail uses `MoviesRepository.GetItem`. Movies remains the only metadata
source.

## Personalized recommendation flow

```text
Authenticated returning user
  -> RecommendationService
  -> RecommendationCacheRepository.GetItem
     -> valid: MoviesRepository.BatchGetItem -> response
     -> missing/expired/invalid: RecommendationProvider
        -> SageMakerRecommendationProvider
```

There is no local ranking fallback. Until a compatible endpoint is deployed,
cache misses return HTTP 503. A future endpoint change is isolated to
`SageMakerRecommendationProvider.invoke_endpoint()`.

## Authentication flow

Guest users are not persisted. Registration/login/profile/onboarding use
UsersRepository and the existing JWT middleware. See
[Authentication Flow](authentication-flow.md).

## Interaction flow

Every canonical click, watch, rating, reaction and share is conditionally
written to UserInteractions. Recommendation computation is not executed in
InteractionService. See [Interaction Pipeline](interaction-pipeline.md).

## AWS boundaries

- DynamoDB repositories contain only persistence mechanics.
- services contain business behavior and enrichment.
- S3 tooling moves datasets/artifacts; HTTP handlers never load them.
- the ML submodule consumes S3 and exports UserInteractions for training.
- SageMaker control/runtime clients are owned by the provider/composition layer.

Startup validates the AWS identity, exact table keys, S3 access, and the
endpoint state when inference is enabled.

See [AWS Resource Mapping](../aws/resource-mapping.md) and
[Project Deployment](../aws/project-deployment.md).
