# AWS resource mapping

Resource names are environment-specific and must never be committed. This
document maps logical resources to configuration and code ownership.

## Runtime resources

| AWS service | Logical resource | Environment variable | Backend repository | Backend service | Purpose | AWS Console location | Current usage |
|---|---|---|---|---|---|---|---|
| DynamoDB | Movies | `AWS_DYNAMODB_MOVIES_TABLE` | `MoviesRepository` | `MovieService`, current mock provider | Source of truth for movie metadata | DynamoDB → Tables → configured name | `GetItem`, paginated `Scan` |
| DynamoDB | PopularMovies | `AWS_DYNAMODB_POPULAR_TABLE` | `PopularMoviesRepository` | Not wired to a runtime service yet | Precomputed global/genre rankings | DynamoDB → Tables → configured name | Configured for future use |
| DynamoDB | Users | `AWS_DYNAMODB_USERS_TABLE` | `UsersRepository` | `AuthService` | Registered users, profile, onboarding and password hash | DynamoDB → Tables → configured name | `GetItem`, `Scan`, `PutItem` |
| DynamoDB | UserInteractions | `AWS_DYNAMODB_INTERACTIONS_TABLE` | `UserInteractionsRepository` | `InteractionService` | Click, watch, rating, reaction and share events | DynamoDB → Tables → configured name | `PutItem`, `GetItem`, paginated `Query` |
| DynamoDB | RecommendationCache | `AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE` | `RecommendationCacheRepository` | `RecommendationService` | Per-user, per-scenario recommendation cache | DynamoDB → Tables → configured name | `GetItem`, `PutItem` |

All DynamoDB resources use `AWS_REGION`. `AWS_ENDPOINT_URL` is used only when an
explicit emulator is configured.

## S3 resources

| AWS service | Logical resource | Environment variable | Repository/service | Purpose | AWS Console location | Current usage |
|---|---|---|---|---|---|---|
| S3 | Project bucket | `AWS_S3_BUCKET` | No backend adapter yet | Parent for data and artifact namespaces | S3 → Buckets → configured name | Startup configuration validation only |
| S3 | Dataset prefix | `AWS_S3_DATASET_PREFIX` | Future data pipeline | Raw/imported datasets | Bucket → configured prefix | Not integrated |
| S3 | Processed prefix | `AWS_S3_PROCESSED_PREFIX` | Future data pipeline | Cleaned/processed datasets | Bucket → configured prefix | Not integrated |
| S3 | Serving prefix | `AWS_S3_SERVING_PREFIX` | Future serving adapter | Serving exports | Bucket → configured prefix | Not integrated |
| S3 | Training prefix | `AWS_S3_TRAINING_PREFIX` | Future training pipeline | Training inputs | Bucket → configured prefix | Not integrated |
| S3 | Model prefix | `AWS_S3_MODEL_PREFIX` | Future model adapter | Model artifacts and manifests | Bucket → configured prefix | Not integrated |
| S3 | Output prefix | `AWS_S3_OUTPUT_PREFIX` | Future job pipeline | Training/evaluation outputs | Bucket → configured prefix | Not integrated |

This task does not add S3 SDK calls or fallback data.

## SageMaker resources

| AWS service | Logical resource | Environment variable | Repository/service | Purpose | AWS Console location | Current usage |
|---|---|---|---|---|---|---|
| SageMaker | Training/processing job | `AWS_SAGEMAKER_TRAINING_JOB_NAME_PREFIX`, `AWS_SAGEMAKER_INSTANCE_TYPE` | ML submodule, external to current backend runtime | Future managed training compute | SageMaker → Training or Processing jobs | Not invoked |
| SageMaker | Model | `AWS_SAGEMAKER_MODEL_NAME` | Future provider | Future deployed model identifier | SageMaker → Inference → Models | Not created or invoked |
| SageMaker | Endpoint | `AWS_SAGEMAKER_ENDPOINT_NAME` | `SageMakerRecommendationProvider` placeholder | Future real-time inference if that architecture is selected | SageMaker → Inference → Endpoints | Not invoked |
| IAM | SageMaker execution role | `AWS_SAGEMAKER_EXECUTION_ROLE` | Future training/deployment integration | Least-privilege service role | IAM → Roles → configured role | Not assumed by backend |

The current runtime remains on `MockRecommendationProvider`. These entries
standardize names only and do not decide the future inference architecture.

## IAM permissions

Grant permissions only to the configured resources.

Current backend runtime generally needs:

- Movies: `dynamodb:GetItem`, `dynamodb:Scan`
- Users: `dynamodb:GetItem`, `dynamodb:Scan`, `dynamodb:PutItem`
- UserInteractions: `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:Query`
- RecommendationCache: `dynamodb:GetItem`, `dynamodb:PutItem`

PopularMovies needs no backend permission until a runtime service consumes it.
S3 and SageMaker permissions are not required by the current business flow.

Do not grant `Action: "*"`, `Resource: "*"`, administrator access, or broad
SageMaker permissions for this configuration-only phase.

## External provisioning checklist

Provisioning is managed outside this repository. Operators must:

1. Create or identify all five DynamoDB tables with the documented key schema.
2. Create or identify the S3 bucket used by future pipeline work.
3. Configure an IAM role/policy with the current runtime actions above.
4. Set environment-specific resource names in the deployment `.env`.
5. Configure GitHub deployment secrets and `EC2_APP_DIR`.
6. Leave SageMaker variables empty until a separately reviewed integration is
   selected and provisioned.
