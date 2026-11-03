import psycopg
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_get_foods_returns_public_foods(migrated_db_url: str) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        conn.execute(
            """
            INSERT INTO foods (name, serving_unit, serving_size, calories,
            protein, carbs, fat, visibility)
            VALUES ('Banana', 'piece', 1, 105, 1.3, 27.0, 0.4, 'public')
            """
        )
        conn.commit()

    response = client.get("/v1/foods")

    assert response.status_code == 200
    assert [f["name"] for f in response.json()] == ["Banana"]
