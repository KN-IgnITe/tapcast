from typing import Any, Generator

import pytest
import psycopg
from training.data.connector import fetch_training_data, get_conn_info


@pytest.fixture
def test_table_setup() -> Generator[None, Any, None]:
    """Fixture that sets up and tears down test table."""
    conn_info = get_conn_info()

    # Setup: Create table
    with psycopg.connect(conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS test_samples CASCADE;")
            cur.execute("""
                CREATE TABLE test_samples (
                    id SERIAL PRIMARY KEY,
                    payload JSONB,
                    label FLOAT
                )
            """)
        conn.commit()

    yield

    # Teardown: Drop table
    with psycopg.connect(conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS test_samples CASCADE;")
        conn.commit()


@pytest.fixture
def populated_table(test_table_setup: Generator[None, Any, None]) -> None:
    """Fixture that creates and populates test table with sample data."""
    conn_info = get_conn_info()

    with psycopg.connect(conn_info) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO test_samples (payload, label) VALUES (%s, %s)",
                ('{"feature_1": 0.5, "feature_2": 1.1}', 0.99),
            )
            cur.execute(
                "INSERT INTO test_samples (payload, label) VALUES (%s, %s)",
                ('{"feature_1": 0.3, "feature_2": 2.5}', 0.75),
            )
        conn.commit()

    return


def test_fetch_training_data_normal(populated_table: None) -> None:
    """Test fetching data from populated table."""
    data = fetch_training_data("SELECT * FROM test_samples;")

    assert data is not None
    assert len(data) == 2
    assert data[0][0] == 1  # id
    assert data[0][2] == 0.99  # label


def test_fetch_training_data_with_limit(populated_table: None) -> None:
    """Test fetching data with LIMIT clause."""
    data = fetch_training_data("SELECT * FROM test_samples LIMIT 1;")

    assert data is not None
    assert len(data) == 1


def test_fetch_training_data_empty_table(
    test_table_setup: Generator[None, Any, None],
) -> None:
    """Test fetching data from empty table."""
    data = fetch_training_data("SELECT * FROM test_samples;")

    assert data is not None
    assert len(data) == 0


def test_fetch_training_data_nonexistent_table() -> None:
    """Test fetching data from table that does not exist."""
    data = fetch_training_data("SELECT * FROM nonexistent_table;")

    assert data is None


def test_fetch_training_data_invalid_query(
    test_table_setup: Generator[None, Any, None],
) -> None:
    """Test with invalid SQL query."""
    data = fetch_training_data("INVALID SQL SYNTAX;")

    assert data is None


def test_get_conn_info() -> None:
    """Test connection string is properly formatted."""
    conn_info = get_conn_info()

    assert "host=" in conn_info
    assert "port=" in conn_info
    assert "dbname=" in conn_info
    assert "user=" in conn_info
    assert "password=" in conn_info
