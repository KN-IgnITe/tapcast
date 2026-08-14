from unittest.mock import MagicMock
from uuid import UUID

import pytest

from training.jobs.training_job_repository import (
    ClaimedTrainingJob,
    TrainingJobRepository,
)
from training.jobs.training_job_runner import (
    TrainingJobRunner,
    TrainingPipeline,
)


@pytest.fixture
def repository() -> MagicMock:
    return MagicMock(spec=TrainingJobRepository)


@pytest.fixture
def pipeline() -> MagicMock:
    return MagicMock(spec=TrainingPipeline)


@pytest.fixture
def runner(
    repository: MagicMock,
    pipeline: MagicMock,
) -> TrainingJobRunner:
    return TrainingJobRunner(repository, pipeline)


def test_run_does_not_start_pipeline_when_job_cannot_be_claimed(
    runner: TrainingJobRunner,
    repository: MagicMock,
    pipeline: MagicMock,
    job_id: UUID,
) -> None:
    repository.claim.return_value = None

    runner.run(job_id)

    repository.claim.assert_called_once_with(job_id)
    pipeline.run.assert_not_called()
    repository.mark_completed.assert_not_called()
    repository.mark_failed.assert_not_called()


def test_run_marks_job_as_completed_after_successful_training(
    runner: TrainingJobRunner,
    repository: MagicMock,
    pipeline: MagicMock,
    job_id: UUID,
    claimed_job: ClaimedTrainingJob,
) -> None:
    repository.claim.return_value = claimed_job
    pipeline.run.return_value = "models/bars/17/jobs/test-job"

    runner.run(job_id)

    pipeline.run.assert_called_once_with(claimed_job)
    repository.mark_completed.assert_called_once_with(
        job_id,
        "models/bars/17/jobs/test-job",
    )
    repository.mark_failed.assert_not_called()


def test_run_marks_job_as_failed_when_pipeline_raises(
    runner: TrainingJobRunner,
    repository: MagicMock,
    pipeline: MagicMock,
    job_id: UUID,
    claimed_job: ClaimedTrainingJob,
) -> None:
    repository.claim.return_value = claimed_job
    pipeline.run.side_effect = RuntimeError("Training pipeline failed.")

    runner.run(job_id)

    pipeline.run.assert_called_once_with(claimed_job)
    repository.mark_failed.assert_called_once_with(
        job_id,
        "Training pipeline failed.",
    )
    repository.mark_completed.assert_not_called()
