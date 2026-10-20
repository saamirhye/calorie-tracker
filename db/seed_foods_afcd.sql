-- Public foods from the Australian Food Composition Database, Release 3.
-- Source: Food Standards Australia New Zealand (FSANZ), nutrient profiles per 100 g.
-- calories = energy with dietary fibre, equated (kJ) / 4.184, rounded.
-- carbs = available carbohydrate, without sugar alcohols.
-- Safe to run more than once.

INSERT INTO foods (name, serving_unit, serving_size, calories, protein, carbs, fat, source, external_id, visibility)
VALUES
    ('Banana, cavendish, peeled, raw', 'g', 100.00, 95, 1.4, 19.9, 0.2, 'afcd', 'F000262', 'public'),
    ('Apple, red delicious, unpeeled, raw', 'g', 100.00, 59, 0.3, 13.5, 0.0, 'afcd', 'F000107', 'public'),
    ('Orange, navel, peeled, raw', 'g', 100.00, 41, 1.0, 8.2, 0.0, 'afcd', 'F006276', 'public'),
    ('Avocado, hass, raw', 'g', 100.00, 156, 1.6, 2.2, 14.6, 'afcd', 'F000162', 'public'),
    ('Egg, chicken, whole, raw', 'g', 100.00, 127, 12.6, 0.3, 8.5, 'afcd', 'F003729', 'public'),
    ('Chicken, breast, lean flesh, raw', 'g', 100.00, 98, 22.5, 0.0, 0.8, 'afcd', 'F002594', 'public'),
    ('Chicken, breast, lean flesh, grilled, no added fat', 'g', 100.00, 143, 29.8, 0.0, 2.5, 'afcd', 'F002593', 'public'),
    ('Beef, mince, lower fat, raw', 'g', 100.00, 129, 22.9, 0.0, 4.1, 'afcd', 'F000666', 'public'),
    ('Salmon, Atlantic, fillet, raw', 'g', 100.00, 231, 20.5, 0.0, 16.7, 'afcd', 'F007827', 'public'),
    ('Tuna, unflavoured, canned in water, drained', 'g', 100.00, 129, 26.1, 0.0, 2.6, 'afcd', 'F009300', 'public'),
    ('Rice, white, boiled or rice cooker, no added salt', 'g', 100.00, 158, 3.1, 34.7, 0.2, 'afcd', 'F007661', 'public'),
    ('Pasta, white wheat flour, boiled from dry, no added salt', 'g', 100.00, 137, 5.3, 26.2, 0.4, 'afcd', 'F006456', 'public'),
    ('Broccoli, fresh, raw', 'g', 100.00, 32, 4.0, 1.2, 0.4, 'afcd', 'F001905', 'public'),
    ('Sweet potato, orange flesh, peeled, fresh, raw', 'g', 100.00, 65, 1.4, 13.2, 0.2, 'afcd', 'F009035', 'public'),
    ('Cheese, cheddar, natural, regular fat', 'g', 100.00, 403, 24.6, 0.3, 33.4, 'afcd', 'F002414', 'public'),
    ('Peanut butter, smooth & crunchy, added sugar & salt', 'g', 100.00, 596, 22.2, 14.3, 49.6, 'afcd', 'F006577', 'public'),
    ('Porridge, rolled oats, prepared with water', 'g', 100.00, 89, 3.0, 11.4, 2.9, 'afcd', 'F007164', 'public'),
    ('Milk, cow, fluid, regular fat (~3.5%)', 'g', 100.00, 65, 3.3, 5.4, 3.4, 'afcd', 'F005634', 'public'),
    ('Milk, cow, fluid, reduced fat (~1%)', 'g', 100.00, 43, 3.3, 4.8, 1.2, 'afcd', 'F005614', 'public'),
    ('Milk, cow, fluid, skim (~0.15% fat)', 'g', 100.00, 35, 3.6, 5.3, 0.0, 'afcd', 'F005637', 'public'),
    ('Yoghurt, natural, regular fat (~3%)', 'g', 100.00, 73, 5.1, 5.0, 3.2, 'afcd', 'F009694', 'public'),
    ('Bread, from white flour', 'g', 100.00, 251, 9.5, 46.2, 2.0, 'afcd', 'F001463', 'public'),
    ('Bread, from wholemeal flour', 'g', 100.00, 237, 10.4, 39.2, 2.5, 'afcd', 'F001553', 'public'),
    ('Bread, mixed grain', 'g', 100.00, 258, 10.7, 39.8, 4.5, 'afcd', 'F001621', 'public'),
    ('Oil, olive', 'g', 100.00, 883, 0.0, 0.0, 99.9, 'afcd', 'F006177', 'public'),
    ('Potato, coliban, peeled, raw', 'g', 100.00, 58, 2.0, 11.5, 0.0, 'afcd', 'F007247', 'public'),
    ('Potato, coliban, peeled, boiled, drained', 'g', 100.00, 56, 1.0, 11.6, 0.0, 'afcd', 'F007245', 'public'),
    ('Tomato, common, raw', 'g', 100.00, 17, 0.6, 3.0, 0.0, 'afcd', 'F009193', 'public'),
    ('Tomato, cherry, raw', 'g', 100.00, 22, 0.9, 3.5, 0.0, 'afcd', 'F009190', 'public'),
    ('Carrot, mature, peeled, fresh, raw', 'g', 100.00, 35, 0.6, 6.6, 0.0, 'afcd', 'F002276', 'public')
ON CONFLICT (source, external_id) WHERE deleted_at IS NULL DO NOTHING;
