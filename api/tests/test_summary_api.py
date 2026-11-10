import uuid

import psycopg
import pytest
from fastapi.testclient import TestClient

from app.deps import current_user_id
from app.main import app

client = TestClient(app)


def insert_entry(
    conn: psycopg.Connection,
    *,
    calories: int,
    protein: float,
    carbs: float,
    fat: float,
    servings: float,
    consumed_at: str,
    timezone: str = "Australia/Sydney",
    user_id: uuid.UUID | None = None,
    deleted_at: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO entries (user_id, food_name, serving_unit, serving_size,
                              calories, protein, carbs, fat, servings, consumed_at,
                              timezone, deleted_at)
        VALUES (%(user_id)s, 'Banana', 'piece', 1,
                %(calories)s, %(protein)s, %(carbs)s, %(fat)s, %(servings)s,
                %(consumed_at)s, %(timezone)s, %(deleted_at)s)
        """,
        {
            "user_id": user_id or current_user_id(),
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "servings": servings,
            "consumed_at": consumed_at,
            "timezone": timezone,
            "deleted_at": deleted_at,
        },
    )


def test_get_summary_totals_the_days_entries(migrated_db_url: str, stub_user: None) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        insert_entry(
            conn,
            calories=105,
            protein=1.3,
            carbs=27.0,
            fat=0.4,
            servings=2,
            consumed_at="2026-11-05T12:00:00+11:00",
        )
        insert_entry(
            conn,
            calories=105,
            protein=1.3,
            carbs=27.0,
            fat=0.4,
            servings=1,
            consumed_at="2026-11-05T18:00:00+11:00",
        )
    response = client.get("/v1/summary", params={"date": "2026-11-05"})
    assert response.status_code == 200
    assert response.json() == {
        "date": "2026-11-05",
        "entries": 2,
        "calories": 315.0,
        "protein": 3.9,
        "carbs": 81.0,
        "fat": 1.2,
    }


def test_get_summary_empty_day_returns_zeros(stub_user: None) -> None:
    response = client.get("/v1/summary", params={"date": "2026-11-05"})
    assert response.status_code == 200
    assert response.json() == {
        "date": "2026-11-05",
        "entries": 0,
        "calories": 0,
        "protein": 0,
        "carbs": 0,
        "fat": 0,
    }


def test_get_summary_uses_each_entries_timezone(migrated_db_url: str, stub_user: None) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        insert_entry(
            conn,
            calories=105,
            protein=1.3,
            carbs=27.0,
            fat=0.4,
            servings=1,
            consumed_at="2026-11-06T08:00:00+11:00",
        )

    response = client.get("/v1/summary", params={"date": "2026-11-06"})
    assert response.status_code == 200
    assert response.json().get("entries") == 1

    response = client.get("/v1/summary", params={"date": "2026-11-05"})
    assert response.status_code == 200
    assert response.json().get("entries") == 0


def test_get_summary_ignores_other_days_and_other_users(
    migrated_db_url: str, stub_user: None
) -> None:
    other_user_id = uuid.uuid4()
    with psycopg.connect(migrated_db_url) as conn:
        conn.execute("INSERT INTO users (id, username) VALUES (%s, 'other')", (other_user_id,))

        # counts: stub user, 5 Nov
        insert_entry(
            conn,
            calories=105,
            protein=1.3,
            carbs=27.0,
            fat=0.4,
            servings=1,
            consumed_at="2026-11-05T12:00:00+11:00",
        )
        # excluded: stub user, a different day
        insert_entry(
            conn,
            calories=105,
            protein=1.3,
            carbs=27.0,
            fat=0.4,
            servings=1,
            consumed_at="2026-11-06T12:00:00+11:00",
        )
        # excluded: another user, same day
        insert_entry(
            conn,
            calories=500,
            protein=10.0,
            carbs=50.0,
            fat=20.0,
            servings=1,
            consumed_at="2026-11-05T12:00:00+11:00",
            user_id=other_user_id,
        )

    response = client.get("/v1/summary", params={"date": "2026-11-05"})

    assert response.status_code == 200
    assert response.json() == {
        "date": "2026-11-05",
        "entries": 1,
        "calories": 105.0,
        "protein": 1.3,
        "carbs": 27.0,
        "fat": 0.4,
    }


def test_get_summary_ignores_deleted_entries(migrated_db_url: str, stub_user: None) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        insert_entry(
            conn,
            calories=105,
            protein=1.3,
            carbs=27.0,
            fat=0.4,
            servings=1,
            consumed_at="2026-11-06T08:00:00+11:00",
        )
        insert_entry(
            conn,
            calories=105,
            protein=1.3,
            carbs=27.0,
            fat=0.4,
            servings=1,
            consumed_at="2026-11-06T09:00:00+11:00",
            deleted_at="2026-11-06T10:00:00+11:00",
        )

    response = client.get("/v1/summary", params={"date": "2026-11-06"})
    assert response.status_code == 200
    assert response.json().get("entries") == 1


@pytest.mark.parametrize(
    "params",
    [
        pytest.param({}, id="missing"),
        pytest.param({"date": "not-a-date"}, id="not-a-date"),
        pytest.param({"date": "2026-13-01"}, id="month-13"),
    ],
)
def test_get_summary_rejects_bad_date(migrated_db_url: str, params: dict[str, str]) -> None:
    response = client.get("/v1/summary", params=params)

    assert response.status_code == 422
