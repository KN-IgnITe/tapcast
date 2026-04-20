import os
from dotenv import load_dotenv


class DatabaseConfig:
    def __init__(self) -> None:
        load_dotenv()
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = os.getenv("DB_PORT", "5432")
        self.db_name = os.getenv("POSTGRES_DB", os.getenv("DB_NAME", "postgres"))
        self.user = os.getenv("POSTGRES_USER", os.getenv("DB_USER", "postgres"))
        self.password = os.getenv(
            "POSTGRES_PASSWORD", os.getenv("DB_PASSWORD", "password")
        )

    def get_conn_info(self) -> str:
        """Returns the Connection String."""
        return (
            f"host={self.host} port={self.port} dbname={self.db_name} "
            f"user={self.user} password={self.password}"
        )
