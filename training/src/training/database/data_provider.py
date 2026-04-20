from psycopg.rows import TupleRow
from typing import List, LiteralString

from training.database.connector import Connector


class DataProvider:
    def __init__(self, connector: Connector) -> None:
        self._connector = connector

    def fetch_training_data(self, query: LiteralString) -> List[TupleRow] | None:
        """Execute query and return all rows as a list.

        Args:
            query: SQL query to execute.

        Returns:
            List of rows, or None if an error occurs.
        """
        try:
            with self._connector.connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(query)
                    return cur.fetchall()

        except Exception as e:
            print(f"Error connecting to DB: {e}")
            return None
