import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.deps import current_user_id
from app.main import app

client = TestClient(app)

VALID_ENTRY = {
    "servings": 2,
    "consumed_at": "2026-11-05T12:00:00+11:00",
    "timezone": "Australia/Sydney",
}


def insert_food(
    conn: psycopg.Connection,
    visibility: str = "public",
    created_by: uuid.UUID | None = None,
) -> uuid.UUID:
    row = conn.execute(
        """
        INSERT INTO foods (name, serving_unit, serving_size, calories,
                           protein, carbs, fat, visibility, created_by_user_id)
        VALUES ('Banana', 'piece', 1, 105, 1.3, 27.0, 0.4, %s, %s)
        RETURNING id
        """,
        (visibility, created_by),
    ).fetchone()
    assert row is not None
    return row[0]


def count_entries(db_url: str) -> int:
    with psycopg.connect(db_url) as conn:
        row = conn.execute("SELECT count(*) FROM entries").fetchone()
        assert row is not None
        return row[0]


def test_post_entry_copies_nutrition_from_public_food(
    migrated_db_url: str, stub_user: None
) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        food_id = insert_food(conn)
    response = client.post("/v1/entries", json={**VALID_ENTRY, "food_id": str(food_id)})

    assert response.status_code == 201
    body = response.json()
    assert body["food_name"] == "Banana"
    assert body["calories"] == 105
    assert body["servings"] == 2
    assert body["protein"] == 1.3
    assert body["carbs"] == 27.0
    assert body["fat"] == 0.4
    assert body["serving_unit"] == "piece"
    assert body["serving_size"] == 1
    assert body["timezone"] == "Australia/Sydney"
    assert body["consumed_at"] == "2026-11-05T01:00:00Z"

    with psycopg.connect(migrated_db_url) as conn:
        row = conn.execute(
            "SELECT user_id, food_id, food_name, calories, servings FROM entries"
        ).fetchone()
        assert row is not None
        assert str(row[0]) == str(current_user_id())
        assert row[1] == food_id
        assert row[2] == "Banana"
        assert row[3] == 105
        assert row[4] == VALID_ENTRY["servings"]


def test_post_entry_unknown_food_returns_404(migrated_db_url: str, stub_user: None) -> None:
    response = client.post("/v1/entries", json={**VALID_ENTRY, "food_id": str(uuid.uuid4())})

    assert response.status_code == 404
    assert response.json() == {"detail": "food_not_found"}
    assert count_entries(migrated_db_url) == 0


def test_post_entry_other_users_private_food_returns_404(
    migrated_db_url: str, stub_user: None
) -> None:
    other_user_id = uuid.uuid4()
    with psycopg.connect(migrated_db_url) as conn:
        conn.execute("INSERT INTO users (id, username) VALUES (%s, 'other')", (other_user_id,))
        food_id = insert_food(conn, visibility="private", created_by=other_user_id)

    response = client.post("/v1/entries", json={**VALID_ENTRY, "food_id": str(food_id)})

    assert response.status_code == 404
    assert response.json() == {"detail": "food_not_found"}
    assert count_entries(migrated_db_url) == 0


def test_post_entry_own_private_food_creates_entry(migrated_db_url: str, stub_user: None) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        food_id = insert_food(conn, visibility="private", created_by=current_user_id())
    response = client.post("/v1/entries", json={**VALID_ENTRY, "food_id": str(food_id)})

    assert response.status_code == 201
    assert response.json()["food_id"] == str(food_id)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("servings", 0),
        ("servings", -1),
        ("servings", 10_000),
        ("servings", 1.005),
        ("consumed_at", "2026-11-05T12:00:00"),
        ("food_id", "not-a-uuid"),
        ("timezone", "Mars/Olympus"),
    ],
)
def test_post_entry_rejects_invalid_input(
    migrated_db_url: str,
    stub_user: None,
    field: str,
    value: object,
) -> None:
    body = {**VALID_ENTRY, "food_id": str(uuid.uuid4()), field: value}
    response = client.post("/v1/entries", json=body)

    assert response.status_code == 422
    assert count_entries(migrated_db_url) == 0
