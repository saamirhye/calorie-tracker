import psycopg
import pytest
from fastapi.testclient import TestClient

from app.deps import current_user_id
from app.main import app

client = TestClient(app)

VALID_FOOD = {
    "name": "Banana",
    "serving_unit": "piece",
    "serving_size": 1,
    "calories": 105,
    "protein": 1.3,
    "carbs": 27.0,
    "fat": 0.4,
}


@pytest.fixture
def stub_user(migrated_db_url: str) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        conn.execute("INSERT INTO users (id, username) VALUES (%s, 'stub')", (current_user_id(),))


def test_get_foods_returns_public_foods(migrated_db_url: str) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        conn.execute(
            """
            INSERT INTO foods (name, serving_unit, serving_size, calories,
            protein, carbs, fat, visibility)
            VALUES ('Banana', 'piece', 1, 105, 1.3, 27.0, 0.4, 'public')
            """
        )

    response = client.get("/v1/foods")

    assert response.status_code == 200
    assert [f["name"] for f in response.json()] == ["Banana"]


def test_post_foods_creates_a_private_food(migrated_db_url: str, stub_user: None) -> None:
    response = client.post(
        "/v1/foods",
        json=VALID_FOOD,
    )

    assert response.status_code == 201
    body = response.json()
    assert body == {**VALID_FOOD, "id": body["id"], "description": None, "barcode": None}

    with psycopg.connect(migrated_db_url) as conn:
        row = conn.execute(
            "SELECT visibility, created_by_user_id FROM foods WHERE id = %s",
            (body["id"],),
        ).fetchone()

    assert row is not None
    assert row[0] == "private"
    assert row[1] == current_user_id()


def test_post_foods_stores_description_and_barcode(stub_user: None) -> None:
    payload = {**VALID_FOOD, "description": "Cavendish", "barcode": "9300000000001"}

    response = client.post("/v1/foods", json=payload)

    assert response.status_code == 201
    assert response.json()["description"] == "Cavendish"
    assert response.json()["barcode"] == "9300000000001"


def test_post_food_accepts_zero_macros(stub_user: None) -> None:
    response = client.post(
        "/v1/foods",
        json={**VALID_FOOD, "protein": 0, "carbs": 0, "fat": 0},
    )

    assert response.status_code == 201


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("calories", -5),
        ("serving_size", 0),
        ("name", ""),
        ("serving_size", 10_000),  # NUMERIC(6,2) holds up to 9999.99
        ("protein", 100_000),  # NUMERIC(6,1) holds up to 99999.9
        ("calories", 2_147_483_648),  # INT maximum is 2,147,483,647
        ("protein", 99999.95),  # more than one decimal place
        ("serving_size", 0.004),  # rounds to 0.00 and would violate CHECK (serving_size > 0)
        ("barcode", "9" * 256),  # VARCHAR(255)
        ("name", "   "),  # blank after trimming
    ],
)
def test_post_foods_rejects_invalid_values(migrated_db_url: str, field: str, value: object) -> None:
    response = client.post("/v1/foods", json={**VALID_FOOD, field: value})
    assert response.status_code == 422


def test_post_foods_accepts_the_largest_stored_values(stub_user: None) -> None:
    response = client.post(
        "/v1/foods",
        json={
            **VALID_FOOD,
            "serving_size": 9999.99,
            "calories": 2_147_483_647,
            "protein": 99999.9,
            "carbs": 99999.9,
            "fat": 99999.9,
        },
    )
    assert response.status_code == 201


def test_post_foods_rejects_an_unknown_serving_unit(stub_user: None) -> None:
    response = client.post("/v1/foods", json={**VALID_FOOD, "serving_unit": "bucket"})
    assert response.json()["detail"] == "unknown_serving_unit"
    assert response.status_code == 422


def test_post_foods_does_not_hide_a_missing_user_as_a_unit_error(migrated_db_url: str) -> None:
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        client.post("/v1/foods", json=VALID_FOOD)
