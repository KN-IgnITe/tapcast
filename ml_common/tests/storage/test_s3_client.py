from pathlib import Path
from typing import Any

import pytest

from ml_common.storage.exceptions import StorageObjectNotFoundError
from ml_common.storage.s3_client import S3Client
from ml_common.storage.s3_config import S3Config


@pytest.fixture
def s3_config() -> S3Config:
    """Create a test S3 config."""

    return S3Config(
        aws_access_key_id="admin",
        aws_secret_access_key="password",
        bucket_name="tapcast-models",
    )


@pytest.fixture
def s3_client(
    s3_config: S3Config,
    fake_s3_storage_client: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> S3Client:
    """Create S3Client with boto3 patched to fake client."""

    monkeypatch.setattr(
        "ml_common.storage.s3_client.boto3.client",
        lambda *args, **kwargs: fake_s3_storage_client,
    )

    return S3Client(s3_config)


def test_upload_file_passes_expected_arguments(
    s3_client: S3Client,
    fake_s3_storage_client: Any,
) -> None:
    s3_client.upload_file(Path("xgb_model.json"), "models/latest/xgb_model.json")

    assert fake_s3_storage_client.upload_file_calls == [
        {
            "Filename": "xgb_model.json",
            "Bucket": "tapcast-models",
            "Key": "models/latest/xgb_model.json",
        }
    ]


def test_download_file_passes_expected_arguments(
    s3_client: S3Client,
    fake_s3_storage_client: Any,
    tmp_path: Path,
) -> None:
    target_path = tmp_path / "nested" / "xgb_model.json"

    s3_client.download_file("models/latest/xgb_model.json", target_path)

    assert fake_s3_storage_client.download_file_calls == [
        {
            "Bucket": "tapcast-models",
            "Key": "models/latest/xgb_model.json",
            "Filename": str(target_path),
        }
    ]


def test_upload_bytes_passes_expected_arguments(
    s3_client: S3Client,
    fake_s3_storage_client: Any,
) -> None:
    s3_client.upload_bytes("models/latest/metadata.json", b"data")

    assert fake_s3_storage_client.put_object_calls == [
        {
            "Bucket": "tapcast-models",
            "Key": "models/latest/metadata.json",
            "Body": b"data",
        }
    ]


def test_download_bytes_returns_object_data(
    s3_client: S3Client,
    fake_s3_storage_client: Any,
) -> None:
    fake_s3_storage_client.objects["models/latest/metadata.json"] = b"data"

    result = s3_client.download_bytes("models/latest/metadata.json")

    assert result == b"data"


def test_object_exists_returns_true_when_object_exists(
    s3_client: S3Client,
    fake_s3_storage_client: Any,
) -> None:
    fake_s3_storage_client.objects["models/latest/metadata.json"] = b"data"

    assert s3_client.object_exists("models/latest/metadata.json") is True


def test_object_exists_returns_false_when_object_is_missing(
    s3_client: S3Client,
) -> None:
    assert s3_client.object_exists("models/latest/missing.json") is False


def test_download_bytes_raises_not_found_for_missing_object(
    s3_client: S3Client,
) -> None:
    with pytest.raises(StorageObjectNotFoundError):
        s3_client.download_bytes("models/latest/missing.json")


def test_download_file_raises_not_found_for_missing_object(
    s3_client: S3Client,
    fake_s3_storage_client: Any,
    tmp_path: Path,
) -> None:
    fake_s3_storage_client.raise_on_download_file = True

    with pytest.raises(StorageObjectNotFoundError):
        s3_client.download_file(
            "models/latest/missing.json",
            tmp_path / "missing.json",
        )
