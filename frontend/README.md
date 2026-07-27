# Frontend

The frontend is a React + Vite application that renders a Netflix-style landing page and fetches recommendations from the backend API.

## Current responsibilities

- display the main experience and featured movie content
- call the backend API for recommended movies
- show loading and error states for API responses

## Local development

```bash
cd frontend
npm install
npm run dev
```

## Environment variables

- `VITE_API_URL` — backend API base URL, default `http://127.0.0.1:8000/api/v1`
