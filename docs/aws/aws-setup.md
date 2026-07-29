# AWS Setup

This guide provisions a new environment. The current project resources already
exist; do not recreate them during normal deployment. Use the verification
commands first and create only a resource that is confirmed absent.

## 1. Identity and IAM

Prefer IAM Identity Center for developers and IAM roles for EC2, ECS, GitHub
OIDC and SageMaker. Create a long-lived IAM user only when the organization
cannot provide either option.

Console locations:

- IAM Identity Center → Users and permission sets
- IAM → Roles → Create role
- IAM → Users → Create user

The backend role needs:

- `dynamodb:DescribeTable`, `GetItem`, `BatchGetItem`, `PutItem`,
  `DeleteItem`, `Scan`, and `Query` on the five configured tables
- `s3:GetBucketLocation` and `s3:ListBucket` on the configured bucket
- `s3:GetObject` and `s3:PutObject` only for operational dataset tooling
- `sagemaker:DescribeEndpoint` and `sagemaker:InvokeEndpoint` only after
  real-time inference is enabled
- `sts:GetCallerIdentity` for startup identity validation

The SageMaker execution role additionally needs read/write access to the
configured S3 prefixes, CloudWatch Logs permissions, and the actions required
to create the selected training or processing job.

Scope policies to the real table and bucket ARNs. Do not use `Resource: "*"`
in production and never store access keys in git.

## 2. Configure AWS CLI

IAM Identity Center:

```bash
aws configure sso
aws sso login --profile <profile>
aws sts get-caller-identity --profile <profile>
```

Temporary credentials:

```bash
aws configure
aws sts get-caller-identity
```

Set `AWS_PROFILE` for native processes. Docker can receive temporary
credentials through the untracked `.env`; when using SSO, mount the host AWS
configuration directory read-only or run on infrastructure with an IAM role.

## 3. Verify or create DynamoDB tables

Verify first:

```bash
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_MOVIES_TABLE" --region "$AWS_REGION"
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_POPULAR_TABLE" --region "$AWS_REGION"
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_USERS_TABLE" --region "$AWS_REGION"
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_INTERACTIONS_TABLE" --region "$AWS_REGION"
aws dynamodb describe-table --table-name "$AWS_DYNAMODB_RECOMMENDATION_CACHE_TABLE" --region "$AWS_REGION"
```

For a genuinely new environment, create tables with the exact key schema in
[DynamoDB](dynamodb.md), preferably through reviewed infrastructure as code.
Use on-demand billing initially and enable TTL on
`RecommendationCache.expire_at`. Do not add or rename attributes as part of
application deployment.

## 4. Verify or create S3

```bash
aws s3api head-bucket --bucket "$AWS_S3_BUCKET"
aws s3api get-public-access-block --bucket "$AWS_S3_BUCKET"
aws s3api get-bucket-encryption --bucket "$AWS_S3_BUCKET"
```

For a new bucket, enable Block Public Access, server-side encryption,
versioning and a lifecycle policy suitable for model versions and temporary
training output. Configure all prefixes from [Amazon S3](s3.md), then upload
datasets using the project sync command rather than embedding data in the
backend image.

## 5. Prepare SageMaker

1. Create a SageMaker execution role with S3 and CloudWatch permissions.
2. Upload training inputs to `AWS_S3_TRAINING_PREFIX`.
3. Submit a training/processing job from the `ml` submodule.
4. Register the model artifact from `AWS_S3_MODEL_PREFIX`.
5. Create an endpoint configuration and endpoint.
6. Verify the endpoint is `InService`.
7. Run `backend/scripts/test_sagemaker_endpoint.py --describe`.
8. Invoke a contract request, then set `AWS_SAGEMAKER_ENABLED=True`.

See [SageMaker](sagemaker.md) for the request/response contract.

## 6. Configure the application

```bash
cp .env.example .env
```

Fill all required values. Generate `JWT_SECRET_KEY` independently per
environment. Keep `AWS_SAGEMAKER_ENABLED=False` only while the endpoint is
absent, intentionally deleted, or still failing contract tests.
The backend fails startup when identity, table keys, bucket access or enabled
endpoint state is invalid.

## 7. Backend, frontend and Docker

```bash
docker compose config --quiet
docker compose up --build -d
docker compose ps
```

Verify:

```bash
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/api/v1/movies?limit=1"
curl http://127.0.0.1:5173
```

The movie request must resolve `PopularMovies` references through
`BatchGetItem` from `Movies`. It must never return a bundled catalog.

## 8. Service verification

Follow [Project Deployment](project-deployment.md) for the complete new-machine
sequence and [Resource Mapping](resource-mapping.md) for service-specific
verification commands.
