-- Sample foods for development, per 100 g. Rounded approximate values, not reference data.
-- Safe to run more than once.

INSERT INTO foods (name, serving_unit, serving_size, calories, protein, carbs, fat, source, external_id, visibility)
VALUES
    ('Banana, raw', 'g', 100.00, 89, 1.1, 22.8, 0.3, 'sample', 'S001', 'public'),
    ('Apple, raw', 'g', 100.00, 52, 0.3, 13.8, 0.2, 'sample', 'S002', 'public'),
    ('Egg, whole, raw', 'g', 100.00, 143, 12.6, 0.7, 9.5, 'sample', 'S003', 'public'),
    ('Chicken breast, grilled', 'g', 100.00, 165, 31.0, 0.0, 3.6, 'sample', 'S004', 'public'),
    ('Salmon, raw', 'g', 100.00, 208, 20.0, 0.0, 13.0, 'sample', 'S005', 'public'),
    ('Rice, white, boiled', 'g', 100.00, 130, 2.7, 28.0, 0.3, 'sample', 'S006', 'public'),
    ('Pasta, boiled', 'g', 100.00, 158, 5.8, 31.0, 0.9, 'sample', 'S007', 'public'),
    ('Broccoli, raw', 'g', 100.00, 34, 2.8, 6.6, 0.4, 'sample', 'S008', 'public'),
    ('Sweet potato, raw', 'g', 100.00, 86, 1.6, 20.0, 0.1, 'sample', 'S009', 'public'),
    ('Cheddar cheese', 'g', 100.00, 403, 25.0, 1.3, 33.0, 'sample', 'S010', 'public'),
    ('Milk, full cream', 'g', 100.00, 61, 3.2, 4.8, 3.3, 'sample', 'S011', 'public'),
    ('Olive oil', 'g', 100.00, 884, 0.0, 0.0, 100.0, 'sample', 'S012', 'public')
ON CONFLICT (source, external_id) WHERE deleted_at IS NULL DO NOTHING;
