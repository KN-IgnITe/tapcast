import pytest
from pydantic import ValidationError
from training.database.database_config import DatabaseConfig


def test_database_config_uses_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "db.internal")
    monkeypatch.setenv("DB_PORT", "6543")
    monkeypatch.setenv("DB_NAME", "tapcast")
    monkeypatch.setenv("POSTGRES_USER", "tapcast_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "secret")

    cfg = DatabaseConfig()

    assert cfg.host == "db.internal"
    assert cfg.port == 6543
    assert cfg.db_name == "tapcast"
    assert cfg.user == "tapcast_user"
    assert cfg.password == "secret"


def test_database_config_raises_error_when_required_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DB_NAME", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    with pytest.raises(ValidationError):
        DatabaseConfig()


def test_database_config_uses_defaults_for_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("DB_HOST", raising=False)
    monkeypatch.delenv("DB_PORT", raising=False)

    monkeypatch.setenv("DB_NAME", "tapcast")
    monkeypatch.setenv("POSTGRES_USER", "user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "pass")

    cfg = DatabaseConfig()

    assert cfg.host == "localhost"
    assert cfg.port == 5432


def test_get_conn_info_returns_expected_format() -> None:
    cfg = DatabaseConfig(
        host="localhost",
        port=5432,
        db_name="tapcast",
        user="postgres",
        password="pwd",
    )

    assert (
        cfg.get_conn_info()
        == "host=localhost port=5432 dbname=tapcast user=postgres password=pwd"
    )
