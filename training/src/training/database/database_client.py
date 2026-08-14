# allow forward references in types without quotes, __enter__ returns DatabaseClient
from __future__ import annotations

import re
from types import TracebackType

import psycopg
from psycopg.rows import dict_row

from training.database.database_config import DatabaseConfig


class DatabaseClient:
    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._connection: psycopg.Connection | None = None

    def connect(self) -> bool:
        """Opens a connection only if it is closed."""
        if self._connection is None or self._connection.closed:
            try:
                self._connection = psycopg.connect(self._config.get_conn_info())
                return True
            except psycopg.Error as e:
                print(f"Connection error: {e}")
                raise
        return True

    def close(self) -> None:
        """Closes the connection."""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None

    # --- Context Manager methods ---
    def __enter__(self) -> DatabaseClient:
        """Called at the beginning of the 'with' block."""
        self.connect()
        return self  # Returns the client instance to the variable after 'as'

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Called at the end of the 'with' block, regardless of errors."""
        if exc_type:
            print(f"An error occurred: {exc_val}")
        self.close()

    @staticmethod
    def _normalize_query(
        query: str, params: tuple | None = None
    ) -> tuple[str, tuple | None]:
        """Converts $1, $2... style queries to %s and reorders params accordingly."""
        if params is None:
            return query, params

        matches = re.findall(r"\$(\d+)", query)
        if not matches:
            return query, params

        normalized_params = tuple(params[int(position) - 1] for position in matches)
        normalized_query = re.sub(r"\$\d+", "%s", query)
        return normalized_query, normalized_params

    def fetch(self, query: str, params: tuple | None = None) -> list[dict]:
        connection = self._require_connection()
        normalized_query, normalized_params = self._normalize_query(query, params)

        with connection.transaction():
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(normalized_query, normalized_params)
                return cursor.fetchall()

    def _require_connection(self) -> psycopg.Connection:
        """Return an open database connection."""

        if self._connection is None or self._connection.closed:
            raise ConnectionError(
                "No connection available. Use 'with DatabaseClient(...) as client'."
            )

        return self._connection

    def execute(
        self,
        query: str,
        params: tuple | None = None,
    ) -> int:
        """Execute a write query and return the number of affected rows."""

        connection = self._require_connection()
        normalized_query, normalized_params = self._normalize_query(query, params)

        with connection.transaction(), connection.cursor() as cursor:
            cursor.execute(normalized_query, normalized_params)
            return cursor.rowcount

    def execute_returning_one(
        self,
        query: str,
        params: tuple | None = None,
    ) -> dict | None:
        """Execute a write query and return its first returned row."""

        connection = self._require_connection()
        normalized_query, normalized_params = self._normalize_query(query, params)

        with connection.transaction():
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(normalized_query, normalized_params)
                return cursor.fetchone()
