CREATE EXTENSION IF NOT EXISTS citext;

CREATE TABLE users (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    username CITEXT UNIQUE NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    timezone VARCHAR(255) DEFAULT 'UTC' NOT NULL
);

CREATE TABLE serving_units (
    code TEXT PRIMARY KEY
);

INSERT INTO serving_units (code) VALUES
    ('g'),
    ('ml'),
    ('oz'),
    ('cup'),
    ('tbsp'),
    ('tsp'),
    ('slice'),
    ('piece'),
    ('other');

CREATE TABLE foods (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    serving_unit TEXT NOT NULL REFERENCES serving_units(code),
    serving_size NUMERIC(6, 2) NOT NULL CHECK (serving_size > 0),
    calories INT NOT NULL CHECK (calories >= 0),
    protein NUMERIC(6, 1) NOT NULL CHECK (protein >= 0),
    carbs NUMERIC(6, 1) NOT NULL CHECK (carbs >= 0),
    fat NUMERIC(6, 1) NOT NULL CHECK (fat >= 0),
    barcode VARCHAR(255),
    source VARCHAR(255),
    external_id VARCHAR(255),
    created_by_user_id uuid REFERENCES users(id) ON DELETE CASCADE,
    visibility VARCHAR(50) DEFAULT 'private' NOT NULL CHECK (visibility IN ('private', 'public')),
    CHECK (
        (visibility = 'private' AND created_by_user_id IS NOT NULL) OR
        (visibility = 'public' AND created_by_user_id IS NULL)
    ),
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    deleted_at timestamptz
);

CREATE UNIQUE INDEX food_source_external_id_active
    ON foods (source, external_id)
    WHERE deleted_at IS NULL;

CREATE TABLE entries (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    food_id uuid REFERENCES foods(id) ON DELETE SET NULL,
    food_name TEXT NOT NULL,
    serving_unit TEXT NOT NULL REFERENCES serving_units(code),
    serving_size NUMERIC(6, 2) NOT NULL CHECK (serving_size > 0),
    calories INT NOT NULL CHECK (calories >= 0),
    protein NUMERIC(6, 1) NOT NULL CHECK (protein >= 0),
    carbs NUMERIC(6, 1) NOT NULL CHECK (carbs >= 0),
    fat NUMERIC(6, 1) NOT NULL CHECK (fat >= 0),
    servings NUMERIC(6, 2) NOT NULL CHECK (servings > 0),
    consumed_at timestamptz NOT NULL,
    timezone VARCHAR(255) DEFAULT 'UTC' NOT NULL,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    deleted_at timestamptz
);

CREATE TABLE targets (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    target_type VARCHAR(50) NOT NULL CHECK (target_type IN ('calories', 'protein', 'carbs', 'fat')),
    target_value NUMERIC(6, 2) NOT NULL CHECK (target_value >= 0),
    start_date DATE NOT NULL,
    end_date DATE,
    created_at timestamptz DEFAULT now() NOT NULL,
    updated_at timestamptz DEFAULT now() NOT NULL,
    deleted_at timestamptz,
    CHECK (end_date IS NULL OR end_date >= start_date)
);

CREATE UNIQUE INDEX targets_user_type_start_active
    ON targets (user_id, target_type, start_date)
    WHERE deleted_at IS NULL;

CREATE FUNCTION set_updated_at() RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER users_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER foods_set_updated_at
BEFORE UPDATE ON foods
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER entries_set_updated_at
BEFORE UPDATE ON entries
FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER targets_set_updated_at
BEFORE UPDATE ON targets
FOR EACH ROW EXECUTE FUNCTION set_updated_at();