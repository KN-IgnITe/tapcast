# allow forward references in types without quotes, __enter__ returns DatabaseClient
from __future__ import annotations

import re

import psycopg
from psycopg.rows import dict_row
from types import TracebackType
from typing import List, Optional

from training.database.database_config import DatabaseConfig


class DatabaseClient:
    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._connection: Optional[psycopg.Connection] = None

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
        query: str, params: Optional[tuple] = None
    ) -> tuple[str, Optional[tuple]]:
        """Converts $1, $2... style queries to %s and reorders params accordingly."""
        if params is None:
            return query, params

        matches = re.findall(r"\$(\d+)", query)
        if not matches:
            return query, params

        normalized_params = tuple(params[int(position) - 1] for position in matches)
        normalized_query = re.sub(r"\$\d+", "%s", query)
        return normalized_query, normalized_params

    def fetch(self, query: str, params: Optional[tuple] = None) -> List[dict]:
        if not self._connection or self._connection.closed:
            raise ConnectionError(
                "No connection available. Use 'with DatabaseClient(...) as client'."
            )

        normalized_query, normalized_params = self._normalize_query(query, params)

        with self._connection.cursor(row_factory=dict_row) as cur:
            cur.execute(normalized_query, normalized_params)
            return cur.fetchall()
