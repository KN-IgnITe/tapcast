from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from training.jobs.training_job_repository import (
    ClaimedTrainingJob,
    TrainingJobStatus,
)


@pytest.fixture
def job_id() -> UUID:
    return uuid4()


@pytest.fixture
def claimed_job(job_id: UUID) -> ClaimedTrainingJob:
    return ClaimedTrainingJob(
        job_id=job_id,
        bar_id=17,
        status=TrainingJobStatus.RUNNING,
        model_bundle_prefix=None,
        error_message=None,
        created_at=datetime(2026, 8, 12, 10, 0, tzinfo=UTC),
        started_at=datetime(2026, 8, 12, 10, 1, tzinfo=UTC),
        finished_at=None,
    )
