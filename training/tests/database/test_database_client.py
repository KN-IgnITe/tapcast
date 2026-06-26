from unittest.mock import MagicMock

import psycopg
import pytest
from training.database.database_client import DatabaseClient
from training.database.database_config import DatabaseConfig


@pytest.fixture
def db_config() -> DatabaseConfig:
    return DatabaseConfig(
        host="localhost",
        port="5432",
        db_name="tapcast",
        user="postgres",
        password="pwd",
    )


def test_connect_opens_connection_when_missing(
    monkeypatch: pytest.MonkeyPatch, db_config: DatabaseConfig
) -> None:
    connection = MagicMock()
    connection.closed = False

    connect_mock = MagicMock(return_value=connection)
    monkeypatch.setattr(psycopg, "connect", connect_mock)

    client = DatabaseClient(db_config)
    result = client.connect()

    assert result is True
    connect_mock.assert_called_once_with(db_config.get_conn_info())


def test_connect_reuses_existing_open_connection(
    monkeypatch: pytest.MonkeyPatch, db_config: DatabaseConfig
) -> None:
    connect_mock = MagicMock()
    monkeypatch.setattr(psycopg, "connect", connect_mock)

    client = DatabaseClient(db_config)
    existing_connection = MagicMock()
    existing_connection.closed = False
    client._connection = existing_connection

    result = client.connect()

    assert result is True
    connect_mock.assert_not_called()


def test_connect_reconnects_when_existing_connection_is_closed(
    monkeypatch: pytest.MonkeyPatch, db_config: DatabaseConfig
) -> None:
    old_connection = MagicMock()
    old_connection.closed = True

    new_connection = MagicMock()
    new_connection.closed = False

    connect_mock = MagicMock(return_value=new_connection)
    monkeypatch.setattr(psycopg, "connect", connect_mock)

    client = DatabaseClient(db_config)
    client._connection = old_connection

    result = client.connect()

    assert result is True
    connect_mock.assert_called_once_with(db_config.get_conn_info())
    assert client._connection is new_connection


def test_connect_reraises_psycopg_errors(
    monkeypatch: pytest.MonkeyPatch, db_config: DatabaseConfig
) -> None:
    connect_mock = MagicMock(side_effect=psycopg.Error("boom"))
    monkeypatch.setattr(psycopg, "connect", connect_mock)

    client = DatabaseClient(db_config)

    with pytest.raises(psycopg.Error, match="boom"):
        client.connect()


def test_close_closes_and_clears_open_connection(db_config: DatabaseConfig) -> None:
    client = DatabaseClient(db_config)

    connection = MagicMock()
    connection.closed = False
    client._connection = connection

    client.close()

    connection.close.assert_called_once()
    assert client._connection is None


def test_enter_connects_and_returns_client(
    monkeypatch: pytest.MonkeyPatch, db_config: DatabaseConfig
) -> None:
    client = DatabaseClient(db_config)

    connect_mock = MagicMock(return_value=True)
    monkeypatch.setattr(client, "connect", connect_mock)

    returned = client.__enter__()

    connect_mock.assert_called_once_with()
    assert returned is client


def test_exit_closes_connection(
    monkeypatch: pytest.MonkeyPatch, db_config: DatabaseConfig
) -> None:
    client = DatabaseClient(db_config)

    close_mock = MagicMock()
    monkeypatch.setattr(client, "close", close_mock)

    client.__exit__(None, None, None)

    close_mock.assert_called_once_with()


def test_fetch_raises_when_connection_missing(db_config: DatabaseConfig) -> None:
    client = DatabaseClient(db_config)

    with pytest.raises(ConnectionError, match="No connection available"):
        client.fetch("SELECT 1")


def test_fetch_executes_query_and_returns_rows(db_config: DatabaseConfig) -> None:
    client = DatabaseClient(db_config)

    connection = MagicMock()
    connection.closed = False

    cursor_cm = MagicMock()
    cursor = MagicMock()
    cursor_cm.__enter__.return_value = cursor
    connection.cursor.return_value = cursor_cm

    rows = [{"id": 1}, {"id": 2}]
    cursor.fetchall.return_value = rows

    client._connection = connection

    result = client.fetch("SELECT * FROM test WHERE id = %s", (1,))

    assert result == rows
    connection.cursor.assert_called_once()
    cursor.execute.assert_called_once_with("SELECT * FROM test WHERE id = %s", (1,))
    cursor.fetchall.assert_called_once_with()


def test_fetch_converts_backend_placeholders(db_config: DatabaseConfig) -> None:
    client = DatabaseClient(db_config)

    connection = MagicMock()
    connection.closed = False

    cursor_cm = MagicMock()
    cursor = MagicMock()
    cursor_cm.__enter__.return_value = cursor
    connection.cursor.return_value = cursor_cm

    cursor.fetchall.return_value = []
    client._connection = connection

    client.fetch("SELECT * FROM sale WHERE bar_id = $1 AND plu = $2", (1, 539))

    cursor.execute.assert_called_once_with(
        "SELECT * FROM sale WHERE bar_id = %s AND plu = %s", (1, 539)
    )


def test_fetch_orders_backend_placeholder_params(db_config: DatabaseConfig) -> None:
    client = DatabaseClient(db_config)

    connection = MagicMock()
    connection.closed = False

    cursor_cm = MagicMock()
    cursor = MagicMock()
    cursor_cm.__enter__.return_value = cursor
    connection.cursor.return_value = cursor_cm

    cursor.fetchall.return_value = []
    client._connection = connection

    client.fetch("SELECT * FROM sale WHERE plu = $2 OR bar_id = $1", (1, 539))

    cursor.execute.assert_called_once_with(
        "SELECT * FROM sale WHERE plu = %s OR bar_id = %s", (539, 1)
    )
