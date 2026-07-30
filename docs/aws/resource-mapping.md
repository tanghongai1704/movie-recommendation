# AWS Resource Mapping

Resource names are always resolved from environment variables.

| AWS service | Console location | Resource name variable | Backend repository | Backend service/tool | Purpose | Verification command |
|---|---|---|---|---|---|---|
| STS/IAM | IAM → Roles / Identity Center | credential provider chain | — | startup validator | Runtime identity | `aws sts get-caller-identity` |
| DynamoDB | DynamoDB → Tables | `AWS_DYNAMODB_MOVIES_TABLE` | `MoviesRepository` | `MovieService` | Movie metadata source | `aws dynamodb describe-table --table-name "$AWS_DYNAMODB_MOVIES_TABLE"` |
| DynamoDB | DynamoDB → Tables | `AWS_DYNAMODB_POPULAR_TABLE` | `PopularMoviesRepository` | `PopularMovieService` | Guest rankings | `aws dynamodb get-item --table-name "$AWS_DYNAMODB_POPULAR_TABLE" --key ...` |
| DynamoDB | DynamoDB → Tables | `AWS_DYNAMODB_USERS_TABLE` | `UsersRepository` | `AuthService` | Registered identity/profile | `aws dynamodb describe-table --table-name "$AWS_DYNAMODB_USERS_TABLE"` |
| DynamoDB | DynamoDB → Tables | `AWS_DYNAMODB_INTERACTIONS_TABLE` | `UserInteractionsRepository` | `InteractionService`, ML exporter | Behavior events | `aws dynamodb describe-table --table-name "$AWS_DYNAMODB_INTERACTIONS_TABLE"` |
| DynamoDB | DynamoDB → Tables | `AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE` | `RecommendationCacheRepository` | `RecommendationService` | Personalized cache | `aws dynamodb describe-table --table-name "$AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE"` |
| S3 | S3 → Buckets | `AWS_S3_BUCKET` | — | startup validator, S3 tooling, ML sync | Durable data/artifact store | `aws s3api head-bucket --bucket "$AWS_S3_BUCKET"` |
| S3 | S3 → bucket → Objects | `AWS_S3_RAW_PREFIX` | — | S3/ML sync | Raw datasets | `aws s3api list-objects-v2 --bucket "$AWS_S3_BUCKET" --prefix "$AWS_S3_RAW_PREFIX" --max-items 1` |
| S3 | S3 → bucket → Objects | `AWS_S3_PROCESSED_PREFIX` | — | S3/ML sync | Cleaned data and feature tables | same command with prefix |
| S3 | S3 → bucket → Objects | `AWS_S3_SERVING_PREFIX` | — | ML sync | Endpoint inference lookups | same command with prefix |
| S3 | S3 → bucket → Objects | `AWS_S3_TRAINING_PREFIX` | — | SageMaker job | Training input | same command with prefix |
| S3 | S3 → bucket → Objects | `AWS_S3_MODEL_PREFIX` | — | SageMaker job/deployment | Model artifacts | same command with prefix |
| S3 | S3 → bucket → Objects | `AWS_S3_OUTPUT_PREFIX` | — | SageMaker job | Reports/outputs | same command with prefix |
| S3 | S3 → bucket → Objects | `AWS_S3_INTERACTION_EXPORT_PREFIX` | — | ML exporter | Retraining events | same command with prefix |
| SageMaker | SageMaker → Inference → Endpoints | `AWS_SAGEMAKER_ENDPOINT_NAME` | — | `SageMakerRecommendationProvider` | Real-time personalized inference | `aws sagemaker describe-endpoint --endpoint-name "$AWS_SAGEMAKER_ENDPOINT_NAME"` |

## Runtime ownership

```text
FastAPI composition
  -> one configured AWS SDK client set
  -> five DynamoDB repositories
  -> S3 operational storage boundary
  -> SageMaker provider boundary
```

The backend does not own resource creation. Infrastructure deployment supplies
names and IAM permissions; startup validation confirms they match the immutable
application key contract.
