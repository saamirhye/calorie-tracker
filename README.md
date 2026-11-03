# Calorie tracker

A calorie and macro tracker built to learn PostgreSQL, Python and React, and to be used day to day. Stage 1 is a web app on a versioned HTTP API. Native iOS and Android apps come later and use the same API.

## Layout

| Path                 | Contents                                                    |
| -------------------- | ----------------------------------------------------------- |
| `api/`               | FastAPI service, tests, type checking (uv, pytest, pyright) |
| `db/migrations/`     | Numbered plain SQL files, applied by the `migrate` service  |
| `docker-compose.yml` | Postgres 16, the migrate step and the API                   |

## Run

1. Copy `.env.example` to `.env` and change the password.
2. Start the stack: `docker compose up --build`
3. Check it: `curl localhost:8000/v1/health`
4. List foods: `curl localhost:8000/v1/foods`. Returns the public foods and the current user's own, sorted by name. Until auth exists, every request acts as the seed user (`00000000-0000-0000-0000-000000000001`), so with `db/seed.sql` loaded their private foods appear too.

## Develop the API without Docker

```bash
docker compose up -d db
cd api
uv sync
export DATABASE_URL=postgresql://tracker:change-me@localhost:5432/tracker
export TEST_DATABASE_URL=$DATABASE_URL
uv run python -m app.migrate
uv run pytest
uv run pyright
uv run uvicorn app.main:app --reload
```

## Data

`db/seed_foods_afcd.sql` loads 30 generic foods from the Australian Food Composition Database, Release 3, published by Food Standards Australia New Zealand (FSANZ). Values are per 100 g. Check FSANZ's copyright and licence terms before redistributing the data. `db/seed.sql` adds a test user and entries for development. `db/queries.sql` holds the SQL for the app's reports.

`docker compose down -v` deletes the database, so reload the seed data afterwards.

Load the seed data:

```bash
docker exec -i calorie-tracker-db-1 psql -U tracker -d tracker < db/seed_foods_afcd.sql
docker exec -i calorie-tracker-db-1 psql -U tracker -d tracker < db/seed.sql
```

## Status

Scaffold only. The schema, queries, endpoints and front end are written by hand as part of the learning plan.
