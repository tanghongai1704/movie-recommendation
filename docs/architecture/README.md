# Architecture notes

## Current runtime flow

1. The frontend loads in the browser and calls the backend API from the React service layer.
2. FastAPI routes receive those requests and delegate to application services.
3. Services use repository abstractions for movie data and a recommendation provider for recommendation responses.
4. The ML package is currently a service-oriented scaffold and is not yet connected to a production model.
5. AWS-related modules are present as scaffolding for future S3, DynamoDB, and SageMaker integration.

## Request path example

```text
Browser -> React UI -> API client -> FastAPI route -> service -> repository/provider
```

## Current implementation boundaries

- Frontend: UI and API consumption
- Backend: REST API, auth placeholder, service layer, repository abstraction
- ML: future training/inference scaffolding
- Infrastructure: Docker Compose and deployment workflow
