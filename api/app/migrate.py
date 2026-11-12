import hashlib
import os
import sys
from pathlib import Path
from typing import LiteralString, cast

import psycopg

DEFAULT_MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "db" / "migrations"


def checksum(path: Path) -> str:
    """SHA-256 of the file contents."""
    with path.open("rb") as f:
        sha256_hash = hashlib.file_digest(f, "sha256").hexdigest()
    return sha256_hash


def ensure_table(conn: psycopg.Connection) -> None:
    """Create schema_migrations if it does not exist."""
    with conn.transaction():
        conn.execute(
            """
      CREATE TABLE IF NOT EXISTS schema_migrations (
        filename TEXT PRIMARY KEY,
        checksum TEXT NOT NULL,
        applied_at timestamptz NOT NULL DEFAULT now()
      );
      """
        )


def applied(conn: psycopg.Connection) -> dict[str, str]:
    """Return {filename: checksum} for every file already applied."""
    rows = conn.execute("select filename, checksum from schema_migrations").fetchall()
    return {filename: checksum for filename, checksum in rows}


def apply_file(conn: psycopg.Connection, path: Path) -> None:
    """Run one file and record it, inside a single transaction."""
    with conn.transaction():
        sql_text = path.read_text()
        conn.execute(cast(LiteralString, sql_text))  # migration files are trusted repository code
        conn.execute(
            "insert into schema_migrations (filename, checksum) values (%s, %s)",
            (path.name, checksum(path)),
        )


class MigrationChangedError(Exception):
    pass


def pending(done: dict[str, str], files: list[Path]) -> list[Path]:
    """Files not yet applied, in order. Raise if an applied file has changed."""
    result: list[Path] = []

    for file in files:
        if file.name in done:
            if done[file.name] != checksum(file):
                raise MigrationChangedError(f"{file.name} was edited after it was applied")
            continue
        result.append(file)
    return result


def main() -> int:
    migrations_dir = Path(os.environ.get("MIGRATIONS_DIR", DEFAULT_MIGRATIONS_DIR))
    if not migrations_dir.is_dir():
        raise FileNotFoundError(f"migrations folder not found: {migrations_dir}")

    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        ensure_table(conn)

        files = sorted(migrations_dir.glob("*.sql"))

        to_apply = pending(applied(conn), files)
        for path in to_apply:
            apply_file(conn, path)
            print(f"applied {path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
