import os
import uuid
from collections.abc import Iterator

import psycopg
import pytest
from psycopg import sql


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
