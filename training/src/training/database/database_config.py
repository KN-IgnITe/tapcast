import os

from dataclasses import dataclass, field


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: str = field(default_factory=lambda: os.getenv("DB_PORT", "5432"))
    db_name: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "postgres"))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", "password"))

    def get_conn_info(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.db_name} "
            f"user={self.user} password={self.password}"
        )
