import json
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from training.jobs.training_job_request import TrainingJobRequest


def test_from_bytes_parses_valid_job_id() -> None:
    job_id = uuid4()
    body = json.dumps({"job_id": str(job_id)}).encode("utf-8")

    request = TrainingJobRequest.from_bytes(body)

    assert request.job_id == job_id


@pytest.mark.parametrize(
    "body",
    [
        b"not-json",
        b"{}",
        b'{"job_id": "not-a-uuid"}',
        b'{"job_id": "d36ca66a-1ca8-47ad-9f02-c3c6b70597bd", "bar_id": 17}',
    ],
)
def test_from_bytes_rejects_invalid_message(body: bytes) -> None:
    with pytest.raises(ValidationError):
        TrainingJobRequest.from_bytes(body)


def test_job_id_is_stored_as_uuid() -> None:
    request = TrainingJobRequest(job_id=UUID("d36ca66a-1ca8-47ad-9f02-c3c6b70597bd"))

    assert isinstance(request.job_id, UUID)
