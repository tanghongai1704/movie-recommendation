# Amazon SageMaker

The backend has no local recommendation generator. Personalized requests use
`RecommendationCache` first. A valid cache hit is enriched from Movies; a miss
passes through `SageMakerRecommendationProvider`.

The model is not trained/deployed yet, so `AWS_SAGEMAKER_ENABLED` must remain
`False`. In this state a cache miss returns HTTP 503 instead of fabricated
rankings. API request and success-response contracts remain unchanged.

## Provider boundary

Only this file may contain real-time invocation code:

```text
backend/app/services/sagemaker_recommendation_provider.py
```

The provider already owns:

- endpoint configuration
- inference request construction
- response validation
- `movie_id` batch enrichment from DynamoDB
- endpoint status checks
- translation into the existing recommendation API DTO

After a compatible endpoint exists, implement only `invoke_endpoint()`.
Routers, services, repositories, frontend code and API schemas must not change.

## Inference contract

Request:

```json
{
  "user_id": "user-id",
  "scenario": "default",
  "limit": 10
}
```

Expected endpoint response:

```json
{
  "model_version": "model-2026-08-01",
  "items": [
    {
      "movie_id": "278",
      "score": 0.95,
      "reason_code": "personalized"
    }
  ]
}
```

The endpoint must never return movie metadata. The backend resolves every ID
from Movies and rejects a response that references an absent movie.

The future invocation will call the configured SageMaker Runtime client using:

- endpoint: `AWS_SAGEMAKER_ENDPOINT_NAME`
- content type: `AWS_SAGEMAKER_CONTENT_TYPE`
- accept: `AWS_SAGEMAKER_ACCEPT`
- body: serialized `SageMakerRecommendationRequest`

It must parse the response with `SageMakerRecommendationResponse` and translate
SDK/model errors into `RecommendationProviderUnavailableError`.

## Training data and artifacts

```text
UserInteractions
  -> export or DynamoDB export-to-S3
  -> AWS_S3_INTERACTION_EXPORT_PREFIX
  -> feature processing
  -> AWS_S3_TRAINING_PREFIX
  -> SageMaker training/processing job
  -> AWS_S3_MODEL_PREFIX
  -> SageMaker Model
  -> Endpoint Configuration
  -> Endpoint
```

The `ml` submodule syncs raw, processed, feature, serving, split, artifact,
event and report locations exclusively through environment configuration.

## Create SageMaker resources

### Notebook or Studio

Use SageMaker Studio only for exploration. Give its execution role scoped S3
permissions. Commit reusable code to `ml`; do not make notebooks the production
training entrypoint.

### Training or processing job

1. Set `AWS_SAGEMAKER_EXECUTION_ROLE`.
2. Set `AWS_SAGEMAKER_TRAINING_JOB_NAME_PREFIX`.
3. Set `AWS_SAGEMAKER_INSTANCE_TYPE`.
4. Verify the training and output prefixes.
5. Run the ML launcher's dry run.
6. Submit the job and monitor CloudWatch Logs.
7. Store versioned artifacts and evaluation output in S3.

No training job is launched by backend startup.

### Model

Create a SageMaker Model from one immutable artifact version and inference
image. Set `AWS_SAGEMAKER_MODEL_NAME` to that versioned resource name.

### Endpoint configuration and endpoint

Create a versioned endpoint configuration, deploy it, wait for `InService`, and
run contract tests using non-production traffic. Set
`AWS_SAGEMAKER_ENDPOINT_NAME` only after deployment.

Then:

1. implement `invoke_endpoint()`
2. run provider contract and load tests
3. verify IAM `sagemaker:InvokeEndpoint`
4. set `RECOMMENDATION_MODEL_VERSION`
5. set `AWS_SAGEMAKER_ENABLED=True`
6. restart backend and verify startup validation

## Versioning and rollback

- Never overwrite an artifact version.
- Include the model version in endpoint output and cache records.
- Create a new endpoint configuration per release.
- Roll back by switching the endpoint to the previous configuration or changing
  the configured endpoint name.
- Cache TTL bounds exposure to an old version.

## Verification

```bash
aws sagemaker describe-training-job \
  --training-job-name <job-name> \
  --region "$AWS_REGION"

aws sagemaker describe-model \
  --model-name "$AWS_SAGEMAKER_MODEL_NAME" \
  --region "$AWS_REGION"

aws sagemaker describe-endpoint \
  --endpoint-name "$AWS_SAGEMAKER_ENDPOINT_NAME" \
  --region "$AWS_REGION"
```

Do not enable the endpoint integration until the response contract above passes.
