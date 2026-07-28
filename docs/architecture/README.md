# Architecture notes

## Current runtime flow

1. The frontend loads in the browser and calls the backend API from the React service layer.
2. FastAPI routes receive those requests and delegate to application services.
3. `RecommendationService` checks DynamoDB for a valid per-user, per-scenario cache entry.
4. Cache hits return the stored ordered movie IDs and snapshots without invoking the provider.
5. Cache misses or expired/invalid entries invoke `MockRecommendationProvider` and write the result back to DynamoDB.
6. The ML package is currently a service-oriented scaffold and is not yet connected to a production model.

## Request path example

```text
Browser -> React UI -> API client -> FastAPI route -> service -> repository/provider
```

## Current implementation boundaries

- Frontend: UI and API consumption
- Backend: REST API, JWT authentication, service layer, repository abstraction
- ML: future training/inference scaffolding
- Infrastructure: Docker Compose and deployment workflow
