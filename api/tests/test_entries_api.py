import uuid

import psycopg
import pytest
from conftest import insert_entry
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


def test_list_entries_returns_newest_first(migrated_db_url: str, stub_user: None) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        first_food_id = insert_food(conn, visibility="private", created_by=current_user_id())
        second_food_id = insert_food(conn, visibility="private", created_by=current_user_id())

        insert_entry(conn, food_id=first_food_id, consumed_at="2026-11-05T08:00:00+11:00")
        insert_entry(conn, food_id=second_food_id, consumed_at="2026-11-05T09:00:00+11:00")

    response = client.get("/v1/entries", params={"date": "2026-11-05"})
    assert response.status_code == 200

    items = response.json()
    assert items[0]["food_id"] == str(second_food_id)
    assert items[1]["food_id"] == str(first_food_id)


def test_list_entries_empty_day_returns_empty_list(stub_user: None) -> None:
    response = client.get("/v1/entries", params={"date": "2026-11-01"})
    assert response.status_code == 200
    items = response.json()
    assert items == []


def test_list_entries_uses_each_entrys_timezone(migrated_db_url: str, stub_user: None) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        nassau_food_id = insert_food(conn, visibility="private", created_by=current_user_id())
        sydney_food_id = insert_food(conn, visibility="private", created_by=current_user_id())

        insert_entry(
            conn,
            food_id=nassau_food_id,
            consumed_at="2026-11-05T08:00:00+11:00",
            timezone="America/Nassau",
        )
        insert_entry(
            conn,
            food_id=sydney_food_id,
            consumed_at="2026-11-05T09:00:00+11:00",
        )

    response = client.get("/v1/entries", params={"date": "2026-11-05"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["food_id"] == str(sydney_food_id)

    response = client.get("/v1/entries", params={"date": "2026-11-04"})
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["food_id"] == str(nassau_food_id)


def test_list_entries_ignores_other_days_and_other_users(
    migrated_db_url: str, stub_user: None
) -> None:
    other_user_id = uuid.uuid4()
    with psycopg.connect(migrated_db_url) as conn:
        my_first_food_id = insert_food(conn, visibility="private", created_by=current_user_id())
        my_second_food_id = insert_food(conn, visibility="private", created_by=current_user_id())
        insert_entry(conn, food_id=my_first_food_id, consumed_at="2026-11-05T09:00:00+11:00")
        insert_entry(conn, food_id=my_second_food_id, consumed_at="2026-11-06T09:00:00+11:00")

        conn.execute("INSERT INTO users (id, username) VALUES (%s, 'other')", (other_user_id,))
        other_users_food_id = insert_food(conn, visibility="private", created_by=other_user_id)
        insert_entry(
            conn,
            food_id=other_users_food_id,
            consumed_at="2026-11-06T09:00:00+11:00",
            user_id=other_user_id,
        )

    response = client.get("/v1/entries", params={"date": "2026-11-06"})
    assert response.status_code == 200

    items = response.json()
    assert len(items) == 1
    assert items[0]["food_id"] == str(my_second_food_id)


def test_list_entries_ignores_deleted_entries(migrated_db_url: str, stub_user: None) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        my_first_food_id = insert_food(conn, visibility="private", created_by=current_user_id())
        my_second_food_id = insert_food(conn, visibility="private", created_by=current_user_id())
        insert_entry(conn, food_id=my_first_food_id, consumed_at="2026-11-05T09:00:00+11:00")
        insert_entry(
            conn,
            food_id=my_second_food_id,
            consumed_at="2026-11-05T09:00:00+11:00",
            deleted_at="2026-11-05T10:00:00+11:00",
        )

    response = client.get("/v1/entries", params={"date": "2026-11-05"})
    assert response.status_code == 200

    items = response.json()
    assert len(items) == 1
    assert items[0]["food_id"] == str(my_first_food_id)


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({}, id="missing"),
        pytest.param({"date": "not-a-date"}, id="not-a-date"),
        pytest.param({"date": "2026-13-01"}, id="month-13"),
    ],
)
def test_list_entries_rejects_bad_date(migrated_db_url: str, params: dict[str, str]) -> None:
    response = client.get("/v1/entries", params=params)

    assert response.status_code == 422
