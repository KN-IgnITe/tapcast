from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    host: str = Field("localhost", validation_alias="DB_HOST")
    port: int = Field(5432, validation_alias="DB_PORT")

    db_name: str = Field(validation_alias="DB_NAME")
    user: str = Field(validation_alias="POSTGRES_USER")
    password: str = Field(validation_alias="POSTGRES_PASSWORD")

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    def get_conn_info(self) -> str:
        return (
            f"host={self.host} port={self.port} dbname={self.db_name} "
            f"user={self.user} password={self.password}"
        )
