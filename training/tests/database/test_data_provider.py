from typing import Any, LiteralString, cast
from unittest.mock import MagicMock, Mock

import pytest

from training.database.data_provider import DataProvider


def _build_provider_with_cursor(
    fetch_result: Any = None,
    execute_side_effect: Exception | None = None,
) -> tuple[DataProvider, Mock, Mock]:
    """Create provider with mocked connector/connection/cursor chain."""
    connector = Mock()

    conn_cm = MagicMock()
    conn = MagicMock()
    cursor_cm = MagicMock()
    cursor = MagicMock()

    connector.connect.return_value = conn_cm
    conn_cm.__enter__.return_value = conn
    conn.cursor.return_value = cursor_cm
    cursor_cm.__enter__.return_value = cursor

    if execute_side_effect is not None:
        cursor.execute.side_effect = execute_side_effect

    cursor.fetchall.return_value = fetch_result

    provider = DataProvider(connector)
    return provider, connector, cursor


@pytest.mark.parametrize(
    "query,rows",
    [
        (
            "SELECT * FROM test_samples;",
            [(1, {"feature_1": 0.5}, 0.99), (2, {"feature_1": 0.3}, 0.75)],
        ),
        ("SELECT * FROM test_samples LIMIT 1;", [(1, {"feature_1": 0.5}, 0.99)]),
        ("SELECT * FROM test_samples WHERE 1=0;", []),
    ],
)
def test_fetch_training_data_success_cases(
    query: str, rows: list[tuple[Any, ...]]
) -> None:
    """Provider should return fetched rows for common successful queries."""
    provider, connector, cursor = _build_provider_with_cursor(fetch_result=rows)

    result = provider.fetch_training_data(cast(LiteralString, query))

    assert result == rows
    connector.connect.assert_called_once()
    cursor.execute.assert_called_once_with(query)
    cursor.fetchall.assert_called_once()


def test_fetch_training_data_returns_none_when_connect_fails() -> None:
    """Provider should return None when connector cannot open DB session."""
    connector = Mock()
    connector.connect.side_effect = RuntimeError("connection failed")
    provider = DataProvider(connector)

    result = provider.fetch_training_data("SELECT 1;")

    assert result is None


@pytest.mark.parametrize(
    "query,error",
    [
        ("SELECT * FROM nonexistent_table;", RuntimeError("table does not exist")),
        ("INVALID SQL SYNTAX;", ValueError("syntax error")),
    ],
)
def test_fetch_training_data_returns_none_when_query_fails(
    query: str,
    error: Exception,
) -> None:
    """Provider should return None for query execution errors."""
    provider, _, cursor = _build_provider_with_cursor(execute_side_effect=error)

    result = provider.fetch_training_data(cast(LiteralString, query))

    assert result is None
    cursor.execute.assert_called_once_with(query)
