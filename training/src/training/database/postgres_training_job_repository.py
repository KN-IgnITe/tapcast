from datetime import datetime
from typing import cast
from uuid import UUID

from training.database.database_client import DatabaseClient
from training.jobs.training_job_repository import (
    ClaimedTrainingJob,
    TrainingJobRepository,
    TrainingJobStatus,
)


class PostgresTrainingJobRepository(TrainingJobRepository):
    """Store and update training jobs in PostgreSQL."""

    def __init__(self, client: DatabaseClient) -> None:
        self._client = client

    def claim(self, job_id: UUID) -> ClaimedTrainingJob | None:
        """Atomically change a queued job to running."""

        row = self._client.execute_returning_one(
            """
            UPDATE model_training_job
            SET status = $1,
                started_at = CURRENT_TIMESTAMP,
                finished_at = NULL,
                error_message = NULL
            WHERE job_id = $2
              AND status = $3
            RETURNING
                job_id,
                bar_id,
                status,
                model_bundle_prefix,
                error_message,
                created_at,
                started_at,
                finished_at
            """,
            (
                TrainingJobStatus.RUNNING.value,
                job_id,
                TrainingJobStatus.QUEUED.value,
            ),
        )

        if row is None:
            return None

        return self._to_training_job(row)

    def mark_completed(
        self,
        job_id: UUID,
        model_bundle_prefix: str,
    ) -> None:
        """Mark a running job as completed."""

        affected_rows = self._client.execute(
            """
            UPDATE model_training_job
            SET status = $1,
                model_bundle_prefix = $2,
                error_message = NULL,
                finished_at = CURRENT_TIMESTAMP
            WHERE job_id = $3
              AND status = $4
            """,
            (
                TrainingJobStatus.COMPLETED.value,
                model_bundle_prefix,
                job_id,
                TrainingJobStatus.RUNNING.value,
            ),
        )

        self._require_single_update(job_id, affected_rows)

    def mark_failed(self, job_id: UUID, error_message: str) -> None:
        """Mark a running job as failed."""

        affected_rows = self._client.execute(
            """
            UPDATE model_training_job
            SET status = $1,
                error_message = $2,
                finished_at = CURRENT_TIMESTAMP
            WHERE job_id = $3
              AND status = $4
            """,
            (
                TrainingJobStatus.FAILED.value,
                error_message,
                job_id,
                TrainingJobStatus.RUNNING.value,
            ),
        )

        self._require_single_update(job_id, affected_rows)

    @staticmethod
    def _to_training_job(row: dict) -> ClaimedTrainingJob:
        return ClaimedTrainingJob(
            job_id=UUID(str(row["job_id"])),
            bar_id=int(row["bar_id"]),
            status=TrainingJobStatus(str(row["status"])),
            model_bundle_prefix=cast(str | None, row["model_bundle_prefix"]),
            error_message=cast(str | None, row["error_message"]),
            created_at=cast(datetime, row["created_at"]),
            started_at=cast(datetime | None, row["started_at"]),
            finished_at=cast(datetime | None, row["finished_at"]),
        )

    @staticmethod
    def _require_single_update(job_id: UUID, affected_rows: int) -> None:
        if affected_rows != 1:
            raise RuntimeError(f"Training job was not updated: job_id={job_id}")
