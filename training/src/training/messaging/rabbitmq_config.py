from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class RabbitMQConfig(BaseSettings):
    """RabbitMQ connection and queue configuration."""

    host: str = Field("localhost", validation_alias="RABBITMQ_HOST")
    port: int = Field(5672, validation_alias="RABBITMQ_PORT")
    username: str = Field(validation_alias="RABBITMQ_DEFAULT_USER")
    password: str = Field(validation_alias="RABBITMQ_DEFAULT_PASS")
    queue_name: str = Field(
        "model-training-jobs",
        validation_alias="TRAINING_QUEUE_NAME",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        frozen=True,
        populate_by_name=True,
    )

    @classmethod
    def from_env(cls) -> "RabbitMQConfig":
        """Load RabbitMQ configuration from environment variables."""
        return cls()  # type: ignore[call-arg]
