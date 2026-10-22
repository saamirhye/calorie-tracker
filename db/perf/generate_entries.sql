-- Large, repeatable data set for measuring query performance.
-- Adds 20 users and about 52,000 entries (4 per user per day, 1 Jan 2025 to 21 Oct 2026).
-- About 2% of entries are soft deleted. Every fifth user is in New York time.
-- Run on a performance database only, after the migration and seed_foods_afcd.sql.

SELECT setseed(0.42);

INSERT INTO users (username, timezone)
SELECT 'perf_user_' || i,
       CASE WHEN i % 5 = 0 THEN 'America/New_York' ELSE 'Australia/Sydney' END
FROM generate_series(1, 20) AS i;

WITH numbered_foods AS (
    SELECT id, name, serving_unit, serving_size, calories, protein, carbs, fat,
           row_number() OVER (ORDER BY external_id) AS n
    FROM foods
    WHERE source = 'afcd'
)
, slots AS (
    SELECT u.id AS user_id, u.timezone, d::date AS day, k
    FROM users u
    CROSS JOIN generate_series(DATE '2025-01-01', DATE '2026-10-21', INTERVAL '1 day') AS d
    CROSS JOIN generate_series(1, 4) AS k
    WHERE u.username LIKE 'perf_user_%'
)
, picks AS (
    SELECT s.*,
           1 + floor(random() * 30)::int AS food_n,
           round((0.5 + random() * 2.5)::numeric * 4) / 4 AS servings,
           random() AS jitter,
           random() < 0.02 AS is_deleted
    FROM slots s
)
INSERT INTO entries (user_id, food_id, food_name, serving_unit, serving_size,
                     calories, protein, carbs, fat, servings, consumed_at, timezone, deleted_at)
SELECT p.user_id, f.id, f.name, f.serving_unit, f.serving_size,
       f.calories, f.protein, f.carbs, f.fat, p.servings,
       (p.day + TIME '06:00' + p.k * INTERVAL '4 hours' + p.jitter * INTERVAL '3 hours') AT TIME ZONE p.timezone,
       p.timezone,
       CASE WHEN p.is_deleted THEN now() END
FROM picks p
JOIN numbered_foods f ON f.n = p.food_n;

ANALYZE;
