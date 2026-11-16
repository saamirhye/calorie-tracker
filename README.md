# Calorie tracker

![ci](https://github.com/saamirhye/calorie-tracker/actions/workflows/ci.yml/badge.svg) ![python](https://img.shields.io/badge/python-3.12%2B-blue) ![postgres](https://img.shields.io/badge/postgres-16-blue)

A calorie and macro tracker on a versioned HTTP API. I am building it to learn PostgreSQL, Python and React, and to use it every day. The back end comes first. Native iOS and Android apps will use the same API later.

## Status

Built and tested: the database schema, foods, entries (create and list by day), the daily summary and the weekly report query. Not built yet: the React front end, authentication, and editing or deleting entries.

## Stack

- API: Python 3.12, FastAPI, Pydantic, psycopg 3
- Database: PostgreSQL 16, with plain SQL migrations
- Tooling: Docker Compose, uv, pytest, pyright, ruff, pre-commit (with gitleaks)
- CI: GitHub Actions. Dependabot keeps dependencies current.

## Quick start

```bash
cp .env.example .env            # then change the password
docker compose up --build
docker exec -i calorie-tracker-db-1 psql -U tracker -d tracker < db/seed_foods.sql
docker exec -i calorie-tracker-db-1 psql -U tracker -d tracker < db/seed.sql
curl localhost:8000/v1/health
curl localhost:8000/v1/foods
```

Load the seed data before creating foods or entries. Until authentication exists, every request acts as one seed user, and the insert fails with a 500 if that user row is missing. `docker compose down -v` deletes the database, so reload the seed data afterwards.

## API

All routes are under `/v1`.

| Method and path | What it does |
| --- | --- |
| `GET /health` | Service check. |
| `GET /foods` | Public foods plus the current user's own, sorted by name. |
| `POST /foods` | Creates a private food for the current user. Returns `201`. |
| `POST /entries` | Logs a food. Copies the food's nutrition at that moment. Returns `201`, or `404` if the food does not exist or is another user's private food. |
| `GET /entries?date=` | The current user's entries for a day, newest first. Returns `[]` for an empty day and `422` for a missing or invalid date. |
| `GET /summary?date=` | Calories, protein, carbs, fat and the number of entries for a day. Returns zeros for an empty day and `422` for a missing or invalid date. |

<details>
<summary>curl examples</summary>

```bash
# Create a food
curl -X POST localhost:8000/v1/foods -H 'content-type: application/json' \
  -d '{"name":"Banana","serving_unit":"piece","serving_size":1,"calories":105,"protein":1.3,"carbs":27,"fat":0.4}'

# Log an entry (use an id from GET /v1/foods)
curl -X POST localhost:8000/v1/entries -H 'content-type: application/json' \
  -d '{"food_id":"<id>","servings":2,"consumed_at":"2026-11-05T12:00:00+11:00","timezone":"Australia/Sydney"}'

# Entries and totals for a day
curl 'localhost:8000/v1/entries?date=2026-11-05'
curl 'localhost:8000/v1/summary?date=2026-11-05'
```

</details>

## Design decisions

- An entry copies the food's nutrition when it is logged. Editing a food later does not rewrite past days.
- A day is the entry's own local date. Each entry stores the timezone it was logged in, so a trip across timezones does not move meals between days.
- Foods are private or public. A private food is visible only to its owner, and logging another user's private food returns `404`.
- Migrations are numbered plain SQL files. A `migrate` service applies them and records a checksum for each, so an edited migration is caught.
- Deletes are soft. Foods and entries carry a `deleted_at` column, and the queries skip deleted rows.
- The API is versioned from the start (`/v1`), so the mobile apps can rely on it.

## A performance experiment

The weekly report (seven days of calories against a target) is the heaviest query. I measured it before changing anything, on 52,730 generated entries for 21 users.

| Version | Median | Rows read |
| --- | --- | --- |
| No index, no week window | 9.9 ms | 51,740 |
| Index on `user_id` | 2.9 ms | 2,595 |
| Index on `(user_id, consumed_at)`, no week window | 2.8 ms | 2,595 |
| Index on `(user_id, consumed_at)`, with the week window | 0.4 ms | 37 |

The second column of the index helped only once the query asked for just the week. Filtering on the calculated local date could not use the index at all, so the query compares the raw `consumed_at` column. Method: six runs per version with `explain (analyze, buffers)`, the first dropped, the median of the other five. The limits: one machine, one user, one week, a warm cache, and not yet measured at ten times the data. The full write-up and the scripts are in [`db/perf/`](db/perf/results.md).

## Tests and CI

53 tests run with pytest against a PostgreSQL database. CI runs on every push to `main` and every pull request: ruff (lint and format check), pyright, the migrations, the seed data with the daily totals query, then the tests. Pre-commit hooks run ruff and gitleaks before each commit.

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

`db/seed_foods.sql` loads 12 sample foods with rounded, approximate values per 100 g. They are placeholders, not reference data. `db/seed.sql` adds a test user and entries for development. `db/queries.sql` holds the SQL for the reports.

## Roadmap

1. The React front end: a Today page with the day's entries and totals.
2. Editing and deleting entries.
3. Daily targets.
4. Authentication, replacing the seed user.
5. Native mobile apps on the same API.
