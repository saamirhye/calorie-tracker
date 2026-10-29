from pathlib import Path

import psycopg
import pytest

from app.migrate import (
    MigrationChangedError,
    applied,
    apply_file,
    checksum,
    ensure_table,
    main,
    pending,
)


def test_checksum_matches_known_value(tmp_path: Path) -> None:
    f = tmp_path / "x.sql"  # arrange a temporary file
    f.write_bytes(b"abc")
    result = checksum(f)  # act
    expected_result = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert result == expected_result  # assert


def test_checksum_matches_with_two_different_files_with_the_same_content(tmp_path: Path) -> None:
    f = tmp_path / "w.sql"
    f.write_bytes(b"abc")
    k = tmp_path / "x.sql"
    k.write_bytes(b"abc")
    assert checksum(f) == checksum(k)


def test_changed_content_changes_checksum(tmp_path: Path) -> None:
    f = tmp_path / "w.sql"
    f.write_bytes(b"abc")
    first_result = checksum(f)
    f.write_bytes(b"abd")
    second_result = checksum(f)
    assert first_result != second_result


def test_checksum_called_twice_on_one_file(tmp_path: Path) -> None:
    f = tmp_path / "a.sql"
    f.write_bytes(b"abc")
    first = checksum(f)
    second = checksum(f)
    assert first == second


def test_empty_file_does_not_crash(tmp_path: Path) -> None:
    f = tmp_path / "empty.sql"
    f.touch()
    result = checksum(f)
    expected_result = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert result == expected_result


def test_ensure_table_creates_the_table(db_url: str) -> None:
    with psycopg.connect(db_url) as conn:
        ensure_table(conn)
        row = conn.execute("select to_regclass('schema_migrations')").fetchone()
        assert row is not None
        exists: object = row[0]
    assert exists is not None


def test_calling_create_table_twice_does_not_raise(db_url: str) -> None:
    with psycopg.connect(db_url) as conn:
        ensure_table(conn)
        ensure_table(conn)
        row = conn.execute(
            """
      select count(*) from information_schema.tables
      where table_name = 'schema_migrations'
      """
        ).fetchone()
        assert row is not None
        count: object = row[0]
    assert count == 1


def test_table_persists_across_connections(db_url: str) -> None:
    with psycopg.connect(db_url) as conn:
        ensure_table(conn)
    with psycopg.connect(db_url) as other:
        ensure_table(other)  # must not raise
        row = other.execute("select to_regclass('schema_migrations')").fetchone()
        assert row is not None
        exists: object = row[0]
    assert exists is not None


def test_check_for_three_columns(db_url: str) -> None:
    with psycopg.connect(db_url) as conn:
        ensure_table(conn)
        rows = conn.execute(
            "select column_name from information_schema.columns where table_name = %s",
            ("schema_migrations",),
        ).fetchall()
    assert {row[0] for row in rows} == {"filename", "checksum", "applied_at"}


def test_applied_returns_empty_dict_on_a_fresh_database(db_url: str) -> None:
    with psycopg.connect(db_url) as conn:
        ensure_table(conn)
        result = applied(conn)
    assert result == {}


def test_applied_returns_recorded_file_and_checksum(db_url: str) -> None:
    with psycopg.connect(db_url) as conn:
        ensure_table(conn)
        filename = "0001_test.sql"
        checksum_var = "0123abcd"
        conn.execute(
            "insert into schema_migrations (filename, checksum) values (%s, %s)",
            (filename, checksum_var),
        )
        result = applied(conn)
    assert result == {filename: checksum_var}


def test_apply_file_runs_the_sql_and_records_the_file(db_url: str, tmp_path: Path) -> None:
    with psycopg.connect(db_url) as conn:
        # arrange - the table and the file exist
        ensure_table(conn)
        f = tmp_path / "a.sql"
        f.write_text("create table t (id int);")

        # act - what we are testing
        apply_file(conn, f)

        # assert - what should be true after the test succeeds
        row = conn.execute("select to_regclass('t')").fetchone()
        assert row is not None
        assert row[0] is not None  # check first row is not none
        result = applied(conn)  # result needs to be within the connect block otherwise it fails
    assert result == {f.name: checksum(f)}


def test_apply_file_with_bad_sql_raises_and_records_nothing(db_url: str, tmp_path: Path) -> None:
    with psycopg.connect(db_url) as conn:
        ensure_table(conn)
        f = tmp_path / "bad.sql"
        f.write_text("create table t (id int); this is not sql")

        with pytest.raises(psycopg.Error):
            apply_file(conn, f)

        result = applied(conn)
    assert result == {}  # error should be raised and result should be empty


def test_apply_file_rolls_back_its_sql_when_the_record_cannot_be_saved(
    db_url: str, tmp_path: Path
) -> None:
    with psycopg.connect(db_url) as conn:
        ensure_table(conn)
        conn.execute(
            "insert into schema_migrations (filename, checksum) values (%s, %s)", ("a.sql", "old")
        )
        f = tmp_path / "a.sql"
        f.write_text("create table t (id int);")

        with pytest.raises(psycopg.errors.UniqueViolation):
            apply_file(conn, f)

        row = conn.execute("select to_regclass('t')").fetchone()
        assert row is not None
    assert row[0] is None  # after rollback nothing should have changed so row[0] should be None


def test_pending_returns_every_file_when_nothing_is_applied(tmp_path: Path) -> None:
    a = tmp_path / "0001_a.sql"
    a.touch()
    b = tmp_path / "0002_b.sql"
    b.touch()

    result = pending({}, [a, b])
    assert result == [a, b]


def test_pending_skips_file_already_applied(tmp_path: Path) -> None:
    a = tmp_path / "0001_a.sql"
    a.touch()
    b = tmp_path / "0002_b.sql"
    b.touch()

    result = pending({a.name: checksum(a)}, [a, b])
    assert result == [b]


def test_pending_raises_error_on_stale_checksum(tmp_path: Path) -> None:
    a = tmp_path / "0001_a.sql"
    a.write_text("select 1;")

    with pytest.raises(MigrationChangedError):
        pending({a.name: "stale"}, [a])


def test_pending_returns_empty_when_no_files_sent() -> None:
    result = pending({}, [])
    assert result == []


def test_main_happy_path(tmp_path: Path, db_url: str, monkeypatch: pytest.MonkeyPatch) -> None:
    a = tmp_path / "0001_a.sql"
    a.write_text("create table one (id int);")
    b = tmp_path / "0002_b.sql"
    b.write_text("create table two (id int);")

    monkeypatch.setenv("MIGRATIONS_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", db_url)

    assert main() == 0

    with psycopg.connect(db_url) as conn:
        result = applied(conn)
    assert result == {a.name: checksum(a), b.name: checksum(b)}


def test_main_second_run_applies_nothing(
    tmp_path: Path, db_url: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    a = tmp_path / "0001_a.sql"
    a.write_text("create table one (id int);")
    b = tmp_path / "0002_b.sql"
    b.write_text("create table two (id int);")

    monkeypatch.setenv("MIGRATIONS_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", db_url)

    main()
    first = capsys.readouterr().out
    assert a.name in first
    assert b.name in first

    main()
    second = capsys.readouterr().out
    assert second == ""

    with psycopg.connect(db_url) as conn:
        result = applied(conn)
    assert result == {a.name: checksum(a), b.name: checksum(b)}


def test_main_rolls_back_every_file_when_a_later_one_fails(
    tmp_path: Path, db_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "0001_a.sql").write_text("create table one (id int);")
    (tmp_path / "0002_b.sql").write_text("this is not sql;")
    monkeypatch.setenv("MIGRATIONS_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", db_url)

    with pytest.raises(psycopg.Error):
        main()

    with psycopg.connect(db_url) as conn:
        assert applied(conn) == {}
        row = conn.execute("select to_regclass('one')").fetchone()
        assert row is not None
    assert row[0] is None


def test_main_raises_when_the_migrations_folder_is_missing(
    tmp_path: Path, db_url: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("MIGRATIONS_DIR", str(tmp_path / "nope"))
    monkeypatch.setenv("DATABASE_URL", db_url)

    with pytest.raises(FileNotFoundError):
        main()
