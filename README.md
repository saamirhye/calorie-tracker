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
5. Load `db/seed.sql` once (`docker exec -i calorie-tracker-db-1 psql -U tracker -d tracker < db/seed.sql`), because the request acts as the seed user and the insert fails with a 500 if that user row doesn't exist.
6. Create a food: `curl -X POST localhost:8000/v1/foods -H 'content-type: application/json' -d '{"name":"Banana","serving_unit":"piece","serving_size":1,"calories":105,"protein":1.3,"carbs":27,"fat":0.4}'`. Returns `201` and the new food, saved as a private food for the current user.
7. Log an entry: `curl -X POST localhost:8000/v1/entries -H 'content-type: application/json' -d '{"food_id":"<id from GET /v1/foods>","servings":2,"consumed_at":"2026-11-05T12:00:00+11:00","timezone":"Australia/Sydney"}'`. Returns `201` and the entry, with the food's nutrition copied at that moment. Returns `404` if the food doesn't exist or is another user's private food.
8. Daily totals: `curl 'localhost:8000/v1/summary?date=2026-11-05'`. Returns the calories and macros for that day for the current user, as `calories`, `protein`, `carbs` and `fat`, plus the number of `entries`. A day with nothing logged returns zeros. A missing or invalid date returns `422`.

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

Built and tested: the schema, foods, entries and the daily summary. Next: the React front end.
