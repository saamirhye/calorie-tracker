# Calorie tracker

A calorie and macro tracker built to learn PostgreSQL, Python and React, and to be used day to day. Stage 1 is a web app on a versioned HTTP API. Native iOS and Android apps come later and use the same API.

## Layout

| Path | Contents |
|---|---|
| `api/` | FastAPI service, tests, type checking (uv, pytest, pyright) |
| `db/migrations/` | Numbered plain SQL files. Postgres runs them on first start |
| `docker-compose.yml` | Postgres 16 and the API |

## Run

1. Copy `.env.example` to `.env` and change the password.
2. Start the stack: `docker compose up --build`
3. Check it: `curl localhost:8000/v1/health`

## Develop the API without Docker

```bash
cd api
uv sync
uv run pytest
uv run pyright
uv run uvicorn app.main:app --reload
```

## Status

Scaffold only. The schema, queries, endpoints and front end are written by hand as part of the learning plan.
