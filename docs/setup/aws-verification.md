# AWS and local setup verification

Use this checklist after creating `.env` and whenever deployment configuration
changes. Commands use placeholders and do not print secret values.

## 1. Prepare the environment

```bash
cp .env.example .env
```

Fill every required value documented in
[AWS configuration](../aws-configuration.md). Keep `.env` untracked.

Confirm Git ignores it:

```bash
git check-ignore .env
```

## 2. Verify AWS credentials

For AWS SSO:

```bash
aws configure sso
aws sso login --profile <profile-name>
aws sts get-caller-identity --profile <profile-name>
```

PowerShell:

```powershell
aws configure sso
aws sso login --profile <profile-name>
aws sts get-caller-identity --profile <profile-name>
```

The command should return the intended account and principal. Do not paste that
output into source files or logs.

If the backend runs natively, export `AWS_PROFILE`. If it runs in Docker, mount
the host AWS profile directory read-only using a local Compose override, or use
temporary credentials in the untracked `.env`.

## 3. Verify region

```bash
aws configure get region --profile <profile-name>
aws sts get-caller-identity --profile <profile-name>
```

Ensure the configured profile, `AWS_REGION`, and `AWS_DEFAULT_REGION` refer to
the same intended region.

PowerShell can inspect variable presence without printing credentials:

```powershell
@("AWS_REGION", "AWS_DEFAULT_REGION", "AWS_PROFILE") |
  ForEach-Object { "$_ configured: $(-not [string]::IsNullOrWhiteSpace([Environment]::GetEnvironmentVariable($_)))" }
```

## 4. Verify DynamoDB tables

Run once per configured logical table:

```bash
aws dynamodb describe-table \
  --region <region> \
  --table-name <configured-table-name> \
  --query "Table.{Name:TableName,Status:TableStatus,Keys:KeySchema}"
```

Expected keys:

| Table | Partition key | Sort key |
|---|---|---|
| Movies | `movie_id` | none |
| PopularMovies | `list_id` | none |
| Users | `user_id` | none |
| UserInteractions | `user_id` | `interaction_key` |
| RecommendationCache | `user_id` | `scenario` |

Confirm each status is `ACTIVE`. A table in another region is not equivalent.

## 5. Verify S3

```bash
aws s3api head-bucket --bucket <configured-bucket>
aws s3api get-bucket-location --bucket <configured-bucket>
```

The backend currently validates the bucket name but does not call S3. These
commands verify external provisioning and permissions.

## 6. Validate Docker configuration

This command checks Compose syntax without rendering secret values:

```bash
docker compose config --quiet
```

Build and start:

```bash
docker compose up --build -d
docker compose ps
```

Both services should be running and the backend should become healthy.

Inspect startup errors:

```bash
docker compose logs --tail 100 backend
docker compose logs --tail 100 frontend
```

Configuration failures name the missing or invalid variable. Logs must not
contain AWS secret keys or JWT secrets.

## 7. Verify backend

Default local URLs from `.env.example`:

```bash
curl http://127.0.0.1:8000/health
curl "http://127.0.0.1:8000/api/v1/movies?limit=1"
```

Expected health response:

```json
{"status":"ok"}
```

The movie request should return DynamoDB data or an explicit service error. It
must not silently return local mock catalog data.

Run tests:

```bash
docker compose exec -T backend python -m unittest discover -s tests -v
```

## 8. Verify frontend

```bash
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm run build
```

Open the configured frontend host port. Browser requests should target the
exact `VITE_API_URL`.

## 9. Verify environment migration

Search for legacy names:

```bash
rg "JWT_SECRET|AWS_DYNAMODB_TABLE_" .env
```

Replace them with canonical names from `.env.example`. During migration, the
backend accepts legacy aliases. If both names exist with different values,
startup intentionally fails.

## 10. Common failures

### AWS credentials are unavailable

- Refresh an expired SSO session.
- Confirm `AWS_PROFILE` exists inside the backend process/container.
- Confirm the deployed runtime has an IAM role.
- Do not disable credential validation in production.

### Region mismatch

- Compare `AWS_REGION`, `AWS_DEFAULT_REGION`, profile region and resource
  region.
- Do not create duplicate tables to work around a wrong region.

### Access denied

- Read the AWS action and resource ARN from the error.
- Add only the missing least-privilege action to the runtime role.
- Do not grant administrator access.

### Resource not found

- Confirm the canonical environment-variable name.
- Confirm exact table/bucket spelling.
- Confirm region and AWS account.

### Frontend cannot fetch

- Confirm `VITE_API_URL` includes `API_PREFIX`.
- Confirm backend health and host-port mapping.
- Confirm the browser origin is included in `CORS_ALLOWED_ORIGINS`.

### Docker backend fails immediately

- Run `docker compose config --quiet`.
- Check required variables in `.env`.
- Confirm Docker can resolve the selected AWS credentials.
- Review the first configuration error in backend logs.
