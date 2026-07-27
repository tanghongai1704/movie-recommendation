# Backend

The backend is a FastAPI service that exposes movie and recommendation endpoints for the frontend.

## Current responsibilities

- serve the main API routes under `/api/v1`
- handle authentication placeholder routes
- provide movie and recommendation responses
- provide a light service/repository abstraction for future persistence

## Main entrypoint

- `app/main.py` — app factory and middleware setup
- `app/api/v1/routes/` — API routes
- `app/services/` — service layer
- `app/repositories/` — repository abstractions
- `app/schemas/` — response models
- `app/core/config.py` — configuration settings

## Local development

```bash
cd backend
python -m pip install -r requirements.txt
PYTHONPATH=. python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Environment variables

- `LOG_LEVEL` — logging level, default `INFO`
- `DEBUG` — enables debug mode when set to `True`
- `AUTH_TOKEN_PREFIX` — token prefix used by the demo auth flow
