# Movie Recommendation System

A Netflix-style movie recommendation prototype built with a React frontend, a FastAPI backend, and an ML-oriented service layer for future model integration.

## Project overview

This repository currently implements a simple end-to-end experience:

- the frontend renders a polished landing page and requests recommendation data from the backend
- the backend exposes REST endpoints for movies, recommendations, and demo authentication
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
- demo authentication flow
- service/repository abstractions for movies and recommendations
- mock recommendation provider for local development
- Docker Compose based local deployment
- initial AWS-related scaffolding for S3, SageMaker, and DynamoDB integration

### Not yet production-ready

- no real persisted movie database
- no deployed ML model
- no production authentication or user management
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

Required variables:

- `VITE_API_URL`
- `LOG_LEVEL`
- `DEBUG`
- `AUTH_TOKEN_PREFIX`
- `AWS_REGION`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `AWS_S3_BUCKET`
- `AWS_DYNAMODB_TABLE`

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
