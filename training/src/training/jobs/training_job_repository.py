from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Protocol
from uuid import UUID


class TrainingJobStatus(StrEnum):
    """Supported states of a model training job."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ClaimedTrainingJob:
    """Training job claimed from persistent storage."""

    job_id: UUID
    bar_id: int
    status: TrainingJobStatus
    model_bundle_prefix: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


class TrainingJobRepository(Protocol):
    """Provide access to persistent training job state."""

    def claim(self, job_id: UUID) -> ClaimedTrainingJob | None:
        """Atomically change a queued job to running and  return its details."""
        ...

    def mark_completed(
        self,
        job_id: UUID,
        model_bundle_prefix: str,
    ) -> None:
        """Mark a job as completed and store its model location."""
        ...

    def mark_failed(
        self,
        job_id: UUID,
        error_message: str,
    ) -> None:
        """Mark a job as failed and store its error description"""
        ...
