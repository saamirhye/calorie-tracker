import os
import uuid
from collections.abc import Iterator

import psycopg


def get_conn() -> Iterator[psycopg.Connection]:
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        yield conn


# Stub: matches the seed user in db/seed.sql until real auth exists
def current_user_id() -> uuid.UUID:
    return uuid.UUID("00000000-0000-0000-0000-000000000001")
