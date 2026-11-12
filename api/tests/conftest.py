import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from psycopg import sql

from app.deps import current_user_id
from app.migrate import main


@pytest.fixture
def db_url() -> Iterator[str]:
    """A fresh empty database for one test, dropped afterwards."""
    admin_url = os.environ.get("TEST_DATABASE_URL")
    if not admin_url:
        pytest.skip("TEST_DATABASE_URL is not set")
    name = f"test_{uuid.uuid4().hex[:12]}"
    with psycopg.connect(admin_url, autocommit=True) as admin:
        admin.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        base, _, _ = admin_url.rpartition("/")
        yield f"{base}/{name}"
        admin.execute(sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.fixture
def migrated_db_url(db_url: str, monkeypatch: pytest.MonkeyPatch) -> str:
    monkeypatch.setenv("DATABASE_URL", db_url)
    main()
    return db_url


@pytest.fixture
def stub_user(migrated_db_url: str) -> None:
    with psycopg.connect(migrated_db_url) as conn:
        conn.execute("INSERT INTO users (id, username) VALUES (%s, 'stub')", (current_user_id(),))


def insert_entry(
    conn: psycopg.Connection,
    *,
    calories: int = 100,
    protein: float = 1.0,
    carbs: float = 10.0,
    fat: float = 1.0,
    servings: float = 1,
    consumed_at: str,
    food_id: uuid.UUID | None = None,
    timezone: str = "Australia/Sydney",
    user_id: uuid.UUID | None = None,
    deleted_at: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO entries (user_id, food_name, serving_unit, serving_size,
                              calories, protein, carbs, fat, servings, consumed_at,
                              food_id, timezone, deleted_at)
        VALUES (%(user_id)s, 'Banana', 'piece', 1,
                %(calories)s, %(protein)s, %(carbs)s, %(fat)s, %(servings)s,
                %(consumed_at)s, %(food_id)s, %(timezone)s, %(deleted_at)s)
        """,
        {
            "user_id": user_id or current_user_id(),
            "calories": calories,
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "servings": servings,
            "consumed_at": consumed_at,
            "food_id": food_id,
            "timezone": timezone,
            "deleted_at": deleted_at,
        },
    )
