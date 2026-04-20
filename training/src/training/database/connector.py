from psycopg import Connection
import psycopg

from training.database.database_config import DatabaseConfig


class Connector:
    def __init__(self, config: DatabaseConfig):
        self._conn_info = config.get_conn_info()

    def connect(self) -> Connection:
        """Connect to database using connection info"""
        return psycopg.connect(self._conn_info)
