import pytest
from training.database.database_config import DatabaseConfig


def test_database_config_uses_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "db.internal")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "tapcast")
    monkeypatch.setenv("POSTGRES_USER", "tapcast_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")

    cfg = DatabaseConfig()

    assert cfg.host == "db.internal"
    assert cfg.port == "6543"
    assert cfg.db_name == "tapcast"
    assert cfg.user == "tapcast_user"
    assert cfg.password == "secret"


def test_database_config_falls_back_to_legacy_env_names(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.setenv("POSTGRES_DB", "legacy_db")
    monkeypatch.setenv("DB_PASSWORD", "legacy_secret")

    cfg = DatabaseConfig()

    assert cfg.db_name == "legacy_db"
    assert cfg.password == "legacy_secret"


def test_database_config_uses_defaults_when_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("POSTGRES_DB", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)
    monkeypatch.delenv("DB_PASSWORD", raising=False)

    cfg = DatabaseConfig()

    assert cfg.host == "localhost"
    assert cfg.port == "5432"
    assert cfg.db_name == "postgres"
    assert cfg.user == "postgres"
    assert cfg.password == "password"


def test_get_conn_info_returns_expected_format() -> None:
    cfg = DatabaseConfig(
        host="localhost",
        port="5432",
        db_name="tapcast",
        user="postgres",
        password="pwd",
    )

    assert (
        cfg.get_conn_info()
        == "host=localhost port=5432 dbname=tapcast user=postgres password=pwd"
    )
