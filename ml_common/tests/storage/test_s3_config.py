import pytest
from ml_common.storage.s3_config import S3Config


@pytest.fixture
def s3_config() -> S3Config:
    """Create a test S3 config."""

    return S3Config(
        s3_host="localhost",
        s3_port=9000,
        aws_access_key_id="admin",
        aws_secret_access_key="password",
        region_name="eu-central-1",
        bucket_name="tapcast-models",
    )


def test_s3_config_builds_endpoint_url(s3_config: S3Config) -> None:
    assert s3_config.endpoint_url == "http://localhost:9000"


def test_s3_config_returns_boto3_client_config(s3_config: S3Config) -> None:
    client_config = s3_config.get_client_config()

    assert client_config == {
        "endpoint_url": "http://localhost:9000",
        "aws_access_key_id": "admin",
        "aws_secret_access_key": "password",
        "region_name": "eu-central-1",
    }


def test_s3_config_uses_bucket_name(s3_config: S3Config) -> None:
    assert s3_config.bucket_name == "tapcast-models"


def test_s3_config_reads_values_from_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("S3_HOST", "minio")
    monkeypatch.setenv("S3_PORT", "9001")
    monkeypatch.setenv("S3_REGION", "us-east-1")
    monkeypatch.setenv("S3_BUCKET_NAME", "models")
    monkeypatch.setenv("MINIO_ROOT_USER", "user")
    monkeypatch.setenv("MINIO_ROOT_PASSWORD", "secret")

    config = S3Config()

    assert config.endpoint_url == "http://minio:9001"
    assert config.bucket_name == "models"
    assert config.aws_access_key_id == "user"
    assert config.aws_secret_access_key == "secret"
    assert config.region_name == "us-east-1"
