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
