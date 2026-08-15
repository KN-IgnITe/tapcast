from datetime import UTC, datetime
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest
from training.database.database_client import DatabaseClient
from training.database.postgres_training_job_repository import (
    PostgresTrainingJobRepository,
)
from training.jobs.training_job_repository import (
    ClaimedTrainingJob,
    TrainingJobStatus,
)


@pytest.fixture
def database_client() -> MagicMock:
    """Create a mocked database client."""

    return MagicMock(spec=DatabaseClient)


@pytest.fixture
def repository(
    database_client: MagicMock,
) -> PostgresTrainingJobRepository:
    """Create a repository using the mocked database client."""

    return PostgresTrainingJobRepository(database_client)


@pytest.fixture
def job_id() -> UUID:
    return uuid4()


@pytest.fixture
def running_job_row(job_id: UUID) -> dict:
    """Create a database row returned after claiming a job."""

    return {
        "job_id": job_id,
        "bar_id": 17,
        "status": TrainingJobStatus.RUNNING.value,
        "model_bundle_prefix": None,
        "error_message": None,
        "created_at": datetime(2026, 8, 12, 10, 0, tzinfo=UTC),
        "started_at": datetime(2026, 8, 12, 10, 1, tzinfo=UTC),
        "finished_at": None,
    }


def test_claim_returns_claimed_training_job(
    repository: PostgresTrainingJobRepository,
    database_client: MagicMock,
    job_id: UUID,
    running_job_row: dict,
) -> None:
    database_client.execute_returning_one.return_value = running_job_row

    result = repository.claim(job_id)

    assert result == ClaimedTrainingJob(
        job_id=job_id,
        bar_id=17,
        status=TrainingJobStatus.RUNNING,
        model_bundle_prefix=None,
        error_message=None,
        created_at=datetime(2026, 8, 12, 10, 0, tzinfo=UTC),
        started_at=datetime(2026, 8, 12, 10, 1, tzinfo=UTC),
        finished_at=None,
    )

    query, params = database_client.execute_returning_one.call_args.args

    assert "UPDATE model_training_job" in query
    assert "RETURNING" in query
    assert params == (
        TrainingJobStatus.RUNNING.value,
        job_id,
        TrainingJobStatus.QUEUED.value,
    )


def test_claim_returns_none_when_job_cannot_be_claimed(
    repository: PostgresTrainingJobRepository,
    database_client: MagicMock,
    job_id: UUID,
) -> None:
    database_client.execute_returning_one.return_value = None

    result = repository.claim(job_id)

    assert result is None


def test_mark_completed_updates_running_job(
    repository: PostgresTrainingJobRepository,
    database_client: MagicMock,
    job_id: UUID,
) -> None:
    database_client.execute.return_value = 1
    model_bundle_prefix = f"models/jobs/{job_id}"

    repository.mark_completed(job_id, model_bundle_prefix)

    query, params = database_client.execute.call_args.args

    assert "UPDATE model_training_job" in query
    assert "model_bundle_prefix = $2" in query
    assert "finished_at = CURRENT_TIMESTAMP" in query
    assert params == (
        TrainingJobStatus.COMPLETED.value,
        model_bundle_prefix,
        job_id,
        TrainingJobStatus.RUNNING.value,
    )


def test_mark_failed_updates_running_job(
    repository: PostgresTrainingJobRepository,
    database_client: MagicMock,
    job_id: UUID,
) -> None:
    database_client.execute.return_value = 1

    repository.mark_failed(job_id, "Training pipeline failed.")

    query, params = database_client.execute.call_args.args

    assert "UPDATE model_training_job" in query
    assert "error_message = $2" in query
    assert "finished_at = CURRENT_TIMESTAMP" in query
    assert params == (
        TrainingJobStatus.FAILED.value,
        "Training pipeline failed.",
        job_id,
        TrainingJobStatus.RUNNING.value,
    )


def test_mark_completed_raises_when_job_is_not_updated(
    repository: PostgresTrainingJobRepository,
    database_client: MagicMock,
    job_id: UUID,
) -> None:
    database_client.execute.return_value = 0

    with pytest.raises(RuntimeError, match=str(job_id)):
        repository.mark_completed(job_id, "models/jobs/test-job")


def test_mark_failed_raises_when_job_is_not_updated(
    repository: PostgresTrainingJobRepository,
    database_client: MagicMock,
    job_id: UUID,
) -> None:
    database_client.execute.return_value = 0

    with pytest.raises(RuntimeError, match=str(job_id)):
        repository.mark_failed(job_id, "Training pipeline failed.")
