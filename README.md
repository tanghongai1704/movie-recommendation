# Movie Recommendation System

A Netflix-style movie recommendation prototype built with a React frontend, a FastAPI backend, and an ML-oriented service layer for future model integration.

## Project overview

This repository currently implements a simple end-to-end experience:

- the frontend renders a polished landing page and requests recommendation data from the backend
- the backend exposes REST endpoints for movies, recommendations, JWT authentication, profiles, and onboarding
- the ML layer is currently represented by a service abstraction and a mock recommendation path, with future support planned for SageMaker-based inference

## Current architecture

```text
User
  |
Frontend (React + Vite)
  |
Backend API (FastAPI)
  |
Service layer / repositories
  |
Recommendation provider (mock today, ML-ready)
  |
AWS / storage integration (planned and partially scaffolded)
```

## Current implementation status

### Implemented

- React landing page and movie section UI
- FastAPI backend with API routes
- registered-user authentication with salted password hashes and JWT access tokens
- service/repository abstractions for movies and recommendations
- mock recommendation provider for local development
- Docker Compose based local deployment
- initial AWS-related scaffolding for S3, SageMaker, and DynamoDB integration

### Not yet production-ready

- no real persisted movie database
- no deployed ML model
- no external identity provider or distributed JWT revocation store
- no real AWS credentials or deployment wiring beyond scaffolding

## Repository structure

```text
project-root/
├── frontend/            # React/Vite UI
├── backend/             # FastAPI application
│   ├── app/
│   │   ├── api/          # routes
│   │   ├── services/     # business logic
│   │   ├── repositories/ # data access abstraction
│   │   ├── schemas/      # response models
│   │   └── core/         # config and shared utilities
│   └── README.md
├── ml/                  # ML scaffolding and future training assets
├── docker-compose.yml   # local container orchestration
├── .env.example         # environment variable template
└── README.md            # project overview
```

## API contract

A stable API contract for the current frontend/backend boundary is documented in [docs/api/api-contract.md](docs/api/api-contract.md).
The guest, first-login, returning-user, JWT, and redirect behavior is documented
in [docs/architecture/authentication-flow.md](docs/architecture/authentication-flow.md).

## Development flow

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Backend

```bash
cd backend
python -m pip install -r requirements.txt
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Environment variables

Copy `.env.example` to `.env` and adjust values as needed.

Required backend variables:

- `JWT_SECRET`
- `AWS_REGION`
- `AWS_DYNAMODB_TABLE_MOVIES`
- `AWS_DYNAMODB_TABLE_POPULAR`
- `AWS_DYNAMODB_TABLE_USERS`
- `AWS_DYNAMODB_TABLE_INTERACTIONS`
- `AWS_DYNAMODB_TABLE_RECOMMENDATION_CACHE`

Optional authentication settings include `JWT_ISSUER`, `JWT_AUDIENCE`,
`JWT_ACCESS_TOKEN_EXPIRE_MINUTES`, and `PASSWORD_HASH_ITERATIONS`. The frontend
uses `VITE_API_URL`, defaulting to the local backend URL. AWS credentials follow
the standard AWS SDK credential chain and must not be committed.

## AWS integration roadmap

### Phase 1 — Local development
- run frontend and backend locally
- use mock recommendations

### Phase 2 — S3 dataset storage
- store training and sample datasets in S3

### Phase 3 — SageMaker training
- train and package models in SageMaker

### Phase 4 — SageMaker endpoint
- deploy a recommendation endpoint

### Phase 5 — Backend integration
- switch the backend from mock recommendations to live model inference
