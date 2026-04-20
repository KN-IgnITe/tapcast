from unittest.mock import Mock

import pytest

from training.database.connector import Connector


def test_init_reads_connection_info_from_config() -> None:
    """Connector should cache connection info from config at init time."""
    config = Mock()
    config.get_conn_info.return_value = "host=localhost"

    connector = Connector(config)

    config.get_conn_info.assert_called_once_with()
    assert connector._conn_info == "host=localhost"


def test_connect_calls_psycopg_connect_with_cached_conn_info(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """connect should delegate to psycopg.connect using cached conn string."""
    config = Mock()
    config.get_conn_info.return_value = "host=db port=5432"
    connector = Connector(config)

    mock_connection = object()
    mock_connect = Mock(return_value=mock_connection)
    monkeypatch.setattr("training.database.connector.psycopg.connect", mock_connect)

    result = connector.connect()

    mock_connect.assert_called_once_with("host=db port=5432")
    assert result is mock_connection


def test_connect_returns_value_from_psycopg_connect(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """connect should return whatever psycopg.connect returns."""
    config = Mock()
    config.get_conn_info.return_value = "host=prod"
    connector = Connector(config)

    expected_connection = object()
    monkeypatch.setattr(
        "training.database.connector.psycopg.connect",
        lambda _: expected_connection,
    )

    assert connector.connect() is expected_connection
