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
        -> UsersRepository.GetItem
        -> UserInteractionsRepository.Query
        -> SageMakerRecommendationProvider.InvokeEndpoint
        -> MoviesRepository.BatchGetItem
        -> best-effort RecommendationCacheRepository.Upsert
```

There is no local ranking fallback. Endpoint failures are translated to
controlled API errors, while guest browsing remains independent of SageMaker.

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

Startup strictly validates the AWS identity, exact table keys, and S3 access.
When inference is enabled it checks endpoint state as non-blocking health, so
an intentionally stopped endpoint cannot take guest browsing down.

See [AWS Resource Mapping](../aws/resource-mapping.md) and
[Project Deployment](../aws/project-deployment.md).
