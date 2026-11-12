import uuid

import psycopg

from app.foods import list_foods


def insert_user(conn: psycopg.Connection, username: str) -> uuid.UUID:
    row = conn.execute(
        "INSERT INTO users (username) VALUES (%s) RETURNING id", (username,)
    ).fetchone()
    assert row is not None
    return row[0]


def test_list_foods_returns_empty_list_on_a_fresh_database(migrated_db_url: str) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        result = list_foods(conn, uuid.uuid4())
    assert result == []


def test_list_foods_returns_a_public_food(migrated_db_url: str) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        conn.execute(
            """
            INSERT INTO foods (name, serving_unit, serving_size, calories, protein,
            carbs, fat, visibility)
            VALUES ('Banana', 'piece', 1, 105, 1.3, 27.0, 0.4, 'public')
            """
        )
        result = list_foods(conn, uuid.uuid4())
    assert [f.name for f in result] == ["Banana"]


def test_list_foods_excludes_soft_deleted_food(migrated_db_url: str) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        conn.execute(
            """
            INSERT INTO foods (name, serving_unit, serving_size, calories, protein,
            carbs, fat, visibility, deleted_at)
            VALUES ('Banana', 'piece', 1, 105, 1.3, 27.0, 0.4, 'public', now())
            """
        )
        result = list_foods(conn, uuid.uuid4())
    assert result == []


def test_list_foods_excludes_another_users_private_food(migrated_db_url: str) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        me = insert_user(conn, "me")
        theirs = insert_user(conn, "theirs")

        # my private food
        conn.execute(
            """
            INSERT INTO foods (name, serving_unit, serving_size, calories, protein,
            carbs, fat, visibility, created_by_user_id)
            VALUES ('Mine', 'piece', 1, 100, 1, 1, 1, 'private', %s)
            """,
            (me,),
        )
        # their private food
        conn.execute(
            """
            INSERT INTO foods (name, serving_unit, serving_size, calories, protein,
            carbs, fat, visibility, created_by_user_id)
            VALUES ('Theirs', 'piece', 1, 100, 1, 1, 1, 'private', %s)
            """,
            (theirs,),
        )

        result = list_foods(conn, me)
    assert [f.name for f in result] == ["Mine"]


def test_list_foods_orders_by_name(migrated_db_url: str) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        conn.execute(
            """
            INSERT INTO foods (name, serving_unit, serving_size, calories, protein,
            carbs, fat, visibility)
            VALUES ('Cherry', 'piece', 1, 100, 1.2, 10, 0.1, 'public'),
                    ('Apple', 'piece', 1, 100, 1.2, 10, 0.1, 'public'),
                    ('Banana', 'piece', 1, 100, 1.2, 10, 0.1, 'public')
            """
        )
        result = list_foods(conn, uuid.uuid4())
    assert [f.name for f in result] == ["Apple", "Banana", "Cherry"]
