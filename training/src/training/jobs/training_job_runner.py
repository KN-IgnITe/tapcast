import logging
from typing import Protocol
from uuid import UUID

from training.jobs.training_job_repository import (
    ClaimedTrainingJob,
    TrainingJobRepository,
)

logger = logging.getLogger(__name__)


class TrainingPipeline(Protocol):
    """Execute model training for a claimed job."""

    def run(self, job: ClaimedTrainingJob) -> str:
        """Train and export a model, returning its S3 bundle prefix."""
        ...


class TrainingJobRunner:
    """Coordinate execution and status updates of a training job."""

    def __init__(
        self,
        repository: TrainingJobRepository,
        pipeline: TrainingPipeline,
    ) -> None:
        self._repository = repository
        self._pipeline = pipeline

    def run(self, job_id: UUID) -> None:
        """Claim and execute a training job."""

        job = self._repository.claim(job_id)

        if job is None:
            logger.info(
                "Training job cannot be claimed: job_id=%s",
                job_id,
            )
            return

        try:
            model_bundle_prefix = self._pipeline.run(job)
        except Exception as error:
            logger.exception(
                "Training job failed: job_id=%s",
                job_id,
            )
            self._repository.mark_failed(
                job_id,
                str(error),
            )

            return

        self._repository.mark_completed(
            job_id,
            model_bundle_prefix,
        )
