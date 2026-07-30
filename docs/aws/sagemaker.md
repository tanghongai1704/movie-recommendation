# SageMaker recommendation integration

## Runtime flow

Guest browsing never calls SageMaker:

```text
Frontend -> GET /api/v1/movies
         -> PopularMovies GetItem
         -> Movies BatchGetItem
         -> Frontend
```

Personalized recommendations keep the existing frontend contract:

```text
Frontend -> GET /api/v1/recommend/{user_id}
         -> validate JWT and completed onboarding
         -> check RecommendationCache
         -> cache miss: read Users and UserInteractions
         -> normalize the RecommendationEngine request
         -> SageMaker Runtime InvokeEndpoint
         -> validate ranked movie IDs
         -> Movies BatchGetItem and restore model order
         -> best-effort RecommendationCache write
         -> existing RecommendationResponse
```

The reusable SageMaker Runtime client is created once by
`backend/app/aws/infrastructure.py`. The provider only invokes/parses model
ranking output. `RecommendationService` owns Movies enrichment and cache
business rules, while repositories own the DynamoDB operations. Routers never
call boto3.

## Verified source contract

The repository contains `ml/src/recommenders/engine.py`, whose
`RecommendationEngine.recommend()` method accepts:

```json
{
  "user_id": 42,
  "scenario_hint": "returning_user",
  "onboarding_completed": true,
  "valid_interaction_count_90d": 5,
  "selected_movie_ids": [],
  "selected_genres": ["Drama"],
  "recent_interactions": [
    {
      "movie_id": 278,
      "event_type": "rating",
      "value": 4.5,
      "timestamp": "2026-07-29T10:00:00.000Z"
    }
  ],
  "exclude_movie_ids": [],
  "limit": 10
}
```

Supported `scenario_hint` values are `guest`, `onboarding_user`, and
`returning_user`. The backend never sends `guest` to SageMaker. Interaction
events are normalized to the engine's `click`, `watch`, `like`, `dislike`,
`rating`, and `share` vocabulary. Clear events remove prior rating/reaction
state rather than becoming model events.

The native engine response is:

```json
{
  "model_name": "hybrid_recommender",
  "model_version": "1.0.0",
  "scenario_applied": "returning_user",
  "recommendation_type": "hybrid",
  "fallback_used": false,
  "fallback_level": "none",
  "generated_at": "2026-07-29T10:00:01+00:00",
  "artifact_versions": {
    "content_based": "local",
    "collaborative": "v1.0.0"
  },
  "recommendations": [
    {
      "movie_id": 278,
      "score": 0.95,
      "reason_code": "similar_users",
      "reason_context": {}
    }
  ]
}
```

The provider also accepts the legacy/operational `items` shape and parallel
`movie_ids`/`scores` arrays. It rejects empty bodies, malformed JSON, missing
IDs, null/non-finite scores, duplicate IDs, mismatched parallel arrays, empty
recommendations, and mock model versions.

Movie metadata is never expected from the model. IDs are batch-read from
Movies and restored to endpoint ranking order. Missing Movies records are
logged and skipped; a response with no resolvable records is rejected.

## Scenario selection

- Fewer than five valid recent interactions: `onboarding_user`, using the
  persisted onboarding genres.
- At least five valid interactions in the last 90 days:
  `returning_user`.
- `watch` counts only at progress `>= 0.5`.
- Click and dislike events still influence/exclude model candidates but do not
  promote an account to returning-user status.

The endpoint may downgrade `scenario_hint`; its `scenario_applied` is logged
and its `model_version` is stored in the cache.

Application user IDs are strings, while the current engine and training frames
use signed 64-bit integer IDs. Positive numeric IDs are preserved. UUIDs and
other strings use a deterministic SHA-256 mapping into the positive `int64`
range. This lets new UUID users use onboarding/content recommendations without
changing DynamoDB. The same mapping must be applied by future interaction
export/retraining jobs before those users can be recognized by collaborative
artifacts.

## Similar movies limitation

The ML source has `RecommendationEngine.because_you_watched()`, but the
repository contains no deployed SageMaker `model_fn`, `input_fn`, `predict_fn`,
`output_fn`, or `transform_fn` exposing that method. Therefore the backend does
not invent a similar-movie payload or add an API that the deployed endpoint may
not support. Before enabling it:

1. inspect the deployed model artifact or add a versioned serving handler;
2. publish the exact operation/request contract;
3. add a provider method and cache key `similar_movies#<movie_id>`;
4. add the non-breaking API route and contract tests;
5. redeploy the endpoint.

## Runtime environment

Required for inference:

```env
AWS_REGION=ap-southeast-1
AWS_SAGEMAKER_ENABLED=True
AWS_SAGEMAKER_ENDPOINT_NAME=movie-rec-endpoint
AWS_SAGEMAKER_CONTENT_TYPE=application/json
AWS_SAGEMAKER_ACCEPT=application/json
AWS_SAGEMAKER_RECOMMENDATION_LIMIT=10
RECOMMENDATION_CACHE_TTL_SECONDS=300
RECOMMENDATION_MODEL_VERSION=<fallback-version>
```

`RECOMMENDATION_MODEL_VERSION` is used only if the endpoint omits
`model_version`. Never set it to `mock-v1` for a real endpoint.

Training/deployment values are configured by the ML tooling. FastAPI needs
only the endpoint name and runtime media-type/limit settings.

## Credentials

The client factory creates one `boto3.Session`:

- non-empty `AWS_PROFILE`: use that profile;
- empty profile: use boto3's default provider chain, including environment
  credentials, shared credentials, container credentials, and IAM roles;
- empty credential values are never passed as SDK credentials;
- `AWS_ENDPOINT_URL` is passed only when non-empty for local/test endpoints.

Check local identity without exposing credentials:

```bash
aws sts get-caller-identity --region "$AWS_REGION"
```

For Docker Desktop on Windows, choose one:

1. use temporary credentials in the untracked `.env`; or
2. create a local Compose override that mounts the host AWS directory
   read-only to `/root/.aws` and set `AWS_PROFILE`.

Do not hardcode a Windows home path in the committed Compose file. AWS-hosted
containers should use an IAM task/instance role.

## Endpoint diagnostics

Install and describe:

```bash
cd backend
python -m pip install -r requirements.txt
python scripts/test_sagemaker_endpoint.py --describe
```

Invoke an onboarding request:

```bash
python scripts/test_sagemaker_endpoint.py \
  --invoke \
  --scenario onboarding_user \
  --genre Drama \
  --genre Action
```

Invoke an exact returning-user request stored in JSON:

```bash
python scripts/test_sagemaker_endpoint.py \
  --invoke \
  --scenario returning_user \
  --request-file request.json
```

The script loads the untracked project `.env`, uses the same AWS session and
provider parser, and prints only endpoint status or normalized recommendation
data. It never prints credentials or JWT configuration.

Control-plane status can also be checked directly:

```bash
aws sagemaker describe-endpoint \
  --endpoint-name "$AWS_SAGEMAKER_ENDPOINT_NAME" \
  --region "$AWS_REGION" \
  --query 'EndpointStatus'
```

## API test

```bash
curl \
  -H "Authorization: Bearer <access-token>" \
  "http://127.0.0.1:8000/api/v1/recommend/<current-user-id>"
```

The frontend-compatible response remains:

```json
{
  "user_id": "<current-user-id>",
  "recommendations": [
    {
      "movie_id": "278",
      "title": "The Shawshank Redemption",
      "genres": ["Drama", "Crime"],
      "poster_path": "/poster.jpg",
      "score": 0.95,
      "reason_code": "similar_users"
    }
  ]
}
```

Server logs contain `cache hit` or `cache miss`. An actual endpoint call also
logs endpoint name, scenario, AWS request ID, latency, and result count.

## Failure behavior

- invalid API input: `400`/`422`;
- missing/disabled endpoint or credentials: `503`;
- inference timeout: `504`;
- invalid/model-error response: `502`;
- DynamoDB user/interaction failure: `503`;
- cache read failure: warning, then invoke the model;
- cache write failure: warning, return the successful model result;
- guest flow: unaffected by endpoint state.

`/health` does not invoke the endpoint. With startup resource validation
enabled, the control plane describes the endpoint once and logs a warning when
it is absent or not `InService`. SageMaker is intentionally an optional runtime
dependency, so guest browsing and core APIs remain available; personalized
cache misses return a controlled `503` until the endpoint is restored.
