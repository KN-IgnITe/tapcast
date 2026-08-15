from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TrainingJobRequest(BaseModel):
    """Request received from RabbitMQ to start model training."""

    model_config = ConfigDict(extra="forbid")

    job_id: UUID

    @classmethod
    def from_bytes(cls, body: bytes) -> "TrainingJobRequest":
        return cls.model_validate_json(body)
