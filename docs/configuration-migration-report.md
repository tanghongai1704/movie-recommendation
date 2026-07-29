# Configuration migration report

## Scope

This migration centralizes configuration only. It does not change:

- API URLs or request/response schemas under the default configuration
- authentication states or authorization policy
- recommendation logic or provider selection
- DynamoDB repository CRUD behavior
- frontend features
- SageMaker integration status

## Audit findings

### Duplicated configuration

- `/api/v1` existed in backend settings, router registration, frontend URL and
  documentation.
- Backend/frontend ports and bind hosts were repeated across Vite, Dockerfiles
  and Compose.
- Logging read the environment directly instead of using backend settings.
- DynamoDB resource creation was repeated by each repository constructor.

### Missing configuration

- CORS origins and credentials policy.
- JWT algorithm.
- AWS client endpoint, timeout and retry behavior.
- Recommendation cache scenario and model version.
- S3 prefixes and SageMaker future identifiers.
- Docker host/container ports, reload behavior and healthcheck settings.
- Deployment application directory as a GitHub repository variable.

### Inconsistent configuration

- Existing DynamoDB variables used `AWS_DYNAMODB_TABLE_*`; the standardized
  template uses `AWS_DYNAMODB_*_TABLE`.
- Authentication used `JWT_SECRET`; the standardized name is
  `JWT_SECRET_KEY`.
- Frontend services embedded fallback URLs while Vite had separate host/port
  constants.
- Root documentation described AWS as planned even though the backend already
  uses real DynamoDB repositories.

### Obsolete or misleading configuration

- `AWS_S3_BUCKET` existed without backend validation or usage documentation.
- SageMaker placeholder settings were not mapped and could be mistaken for an
  active integration.
- EC2 deployment path was hardcoded in the workflow.

## Files added

- `backend/app/core/config_validation.py`
- `backend/tests/test_config.py`
- `frontend/src/config/environment.ts`
- `docs/aws-configuration.md`
- `docs/aws-resource-mapping.md`
- `docs/setup/aws-verification.md`
- `docs/configuration-migration-report.md`

## Files modified

- `.env.example`
- `.github/workflows/deploy.yml`
- `docker-compose.yml`
- `backend/Dockerfile`
- `backend/app/core/config.py`
- `backend/app/core/security.py`
- `backend/app/main.py`
- `backend/app/container.py`
- `backend/app/services/recommendation_service.py`
- backend configuration-related tests and documentation
- `frontend/Dockerfile`
- `frontend/vite.config.js`
- `frontend/src/vite-env.d.ts`
- `frontend/src/api/apiClient.ts`
- `frontend/src/services/movieService.ts`
- root, architecture, API, authentication and frontend documentation

## Files removed

None. No business implementation, mock provider, fixture, repository, schema or
API file was deleted.

## Configuration improvements

- Immutable logical settings sections.
- Reusable descriptive validators.
- Required-value, alias-conflict, URL, region, S3 bucket/prefix, JWT, integer,
  boolean, logging and AWS credential validation.
- One configured DynamoDB resource injected into all runtime repositories.
- Default AWS credential provider chain preserved.
- Configurable AWS endpoint, timeouts and retry mode.
- Central frontend URL validation.
- Parameterized Docker host/container ports and healthcheck.
- Deployment directory moved to GitHub repository variable `EC2_APP_DIR`.

## Canonical variables added

- `JWT_SECRET_KEY`
- `JWT_ALGORITHM`
- `AWS_DYNAMODB_MOVIES_TABLE`
- `AWS_DYNAMODB_POPULAR_TABLE`
- `AWS_DYNAMODB_USERS_TABLE`
- `AWS_DYNAMODB_INTERACTIONS_TABLE`
- `AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE`
- S3 prefix variables
- SageMaker future-resource and training-job variables
- API, CORS, logging, AWS SDK, cache, Vite and Docker variables documented in
  `.env.example`

Legacy JWT and DynamoDB names remain accepted temporarily. They are not listed
in the new template.

## Hardcoded values removed from runtime composition

- API router prefix
- CORS origins and credentials flag
- OpenAPI metadata
- JWT algorithm
- backend logging format/level
- cache scenario/model version
- frontend API/TMDB URL fallbacks
- Vite host/port
- Docker host/port/container names and health path
- EC2 deployment directory

Safe local defaults remain centralized for developer ports, paths and current
behavior. No AWS resource name has a runtime fallback.

## Documentation synchronized

- Root setup and architecture status.
- Backend configuration and repository injection.
- Frontend environment requirements.
- API base URL.
- Authentication secret/algorithm names.
- AWS configuration architecture.
- AWS resource ownership and IAM expectations.
- Local/Docker/AWS verification and troubleshooting.

## Outstanding TODO items

- The `ml` directory is an independent Git submodule with its own configuration
  history. Its tracked AWS YAML/docs must be migrated in the submodule
  repository and then referenced by a new parent gitlink commit; changing it
  silently in the parent working tree would not publish those changes.
- S3 and SageMaker settings are configuration placeholders only. No SDK calls,
  provider replacement or recommendation changes were authorized.
- Production CORS origins, IAM policies, resource names, S3 prefixes and
  deployment values must be supplied externally.
- Remove legacy environment aliases only after every deployed environment has
  migrated and passed the verification guide.

## Verification checklist

- [x] Backend configuration syntax compiles.
- [x] Backend unit/API tests pass.
- [x] Frontend TypeScript check passes.
- [x] Frontend production build passes.
- [x] Docker Compose configuration validates.
- [x] Current backend container starts and reports healthy.
- [x] Canonical and legacy environment-name tests pass.
- [x] Missing/invalid configuration tests fail descriptively.
- [ ] Production AWS account resources and IAM verified by an operator.
- [ ] Production CORS origins configured.
- [ ] GitHub repository variable `EC2_APP_DIR` configured.
