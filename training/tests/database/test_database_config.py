import pytest

from training.database.database_config import DatabaseConfig


def test_get_conn_info_uses_defaults_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Config should fall back to defaults when env vars are absent."""
    for name in [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    ]:
        monkeypatch.delenv(name, raising=False)

    config = DatabaseConfig()

    assert config.get_conn_info() == (
        "host=localhost port=5432 dbname=postgres user=postgres password=password"
    )


def test_get_conn_info_falls_back_to_db_prefixed_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """DB_* vars should be used when matching POSTGRES_* vars are missing."""
    monkeypatch.setenv("DB_HOST", "127.0.0.1")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "tapcast")
    monkeypatch.setenv("DB_USER", "trainer")
    monkeypatch.setenv("DB_PASSWORD", "secret")
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    config = DatabaseConfig()

    assert config.get_conn_info() == (
        "host=127.0.0.1 port=6543 dbname=tapcast user=trainer password=secret"
    )


def test_get_conn_info_prefers_postgres_values_over_db_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POSTGRES_* vars should have priority when both sets are provided."""
    monkeypatch.setenv("DB_HOST", "db-from-db")
    monkeypatch.setenv("DB_PORT", "1111")
    monkeypatch.setenv("DB_NAME", "db_name")
    monkeypatch.setenv("DB_USER", "db_user")
    monkeypatch.setenv("DB_PASSWORD", "db_password")
    monkeypatch.setenv("POSTGRES_DB", "postgres_name")
    monkeypatch.setenv("POSTGRES_USER", "postgres_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "postgres_password")

    config = DatabaseConfig()

    assert config.get_conn_info() == (
        "host=db-from-db port=1111 "
        "dbname=postgres_name user=postgres_user password=postgres_password"
    )
