-- Development data. Run on a fresh database after the migration and seed_foods.sql.
-- One test user and ten entries across four local days in Sydney time (AEDT, +11).
-- Entries at 23:59 on the 21st and 00:01 on the 22nd test the day boundary.
-- One entry is soft deleted. Food values are copied from foods at log time.

INSERT INTO users (id, username, timezone) VALUES
    ('00000000-0000-0000-0000-000000000001', 'Greg', 'Australia/Sydney');

INSERT INTO targets (user_id, target_type, target_value, start_date, end_date)
SELECT u.id, 'calories', 2200, '2026-10-18'::date, NULL
FROM users u
WHERE u.username = 'Greg'
ON CONFLICT (user_id, target_type, start_date) WHERE deleted_at IS NULL DO NOTHING;

INSERT INTO entries (user_id, food_id, food_name, serving_unit, serving_size,
                     calories, protein, carbs, fat, servings, consumed_at, timezone)
SELECT u.id, f.id, f.name, f.serving_unit, f.serving_size,
       f.calories, f.protein, f.carbs, f.fat, v.servings, v.consumed_at, u.timezone
FROM (VALUES
    ('S001', 1.00, '2026-10-19 23:30:00+11'::timestamptz),
    ('S002', 1.00, '2026-10-20 12:00:00+11'::timestamptz),
    ('S003', 1.00, '2026-10-21 08:00:00+11'::timestamptz),
    ('S004', 1.50, '2026-10-21 12:30:00+11'::timestamptz),
    ('S005', 1.50, '2026-10-21 18:00:00+11'::timestamptz),
    ('S006', 2.00, '2026-10-21 23:59:00+11'::timestamptz),
    ('S007', 1.50, '2026-10-22 00:01:00+11'::timestamptz),
    ('S008', 1.00, '2026-10-22 08:00:00+11'::timestamptz),
    ('S009', 1.50, '2026-10-22 12:00:00+11'::timestamptz),
    ('S010', 0.30, '2026-10-22 18:00:00+11'::timestamptz)
) AS v(external_id, servings, consumed_at)
JOIN foods f ON f.source = 'sample' AND f.external_id = v.external_id
JOIN users u ON u.username = 'Greg';

-- The cheddar entry was logged by mistake and removed.
UPDATE entries
SET deleted_at = '2026-10-22 18:05:00+11'
WHERE food_name = 'Cheddar cheese';
