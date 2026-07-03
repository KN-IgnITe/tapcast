import pytest
from pydantic import ValidationError
from inference.database.s3_config import S3Config


def test_s3_config_uses_env_values(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("S3_HOST", "s3.internal")
    monkeypatch.setenv("S3_PORT", "9999")
    monkeypatch.setenv("S3_REGION", "eu-west-1")
    monkeypatch.setenv("MINIO_ROOT_USER", "custom_user")
    monkeypatch.setenv("MINIO_ROOT_PASSWORD", "secret_pass")

    cfg = S3Config()

    assert cfg.s3_host == "s3.internal"
    assert cfg.s3_port == 9999
    assert cfg.region_name == "eu-west-1"
    assert cfg.aws_access_key_id == "custom_user"
    assert cfg.aws_secret_access_key == "secret_pass"
    assert cfg.bucket_name == "custom_user"
    assert cfg.endpoint_url == "http://s3.internal:9999"


def test_s3_config_raises_error_when_required_env_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("MINIO_ROOT_USER", raising=False)
    monkeypatch.delenv("MINIO_ROOT_PASSWORD", raising=False)

    with pytest.raises(ValidationError):
        S3Config()


def test_s3_config_uses_defaults_for_optional_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("S3_HOST", raising=False)
    monkeypatch.delenv("S3_PORT", raising=False)
    monkeypatch.delenv("S3_REGION", raising=False)

    monkeypatch.setenv("MINIO_ROOT_USER", "user")
    monkeypatch.setenv("MINIO_ROOT_PASSWORD", "pass")

    cfg = S3Config()

    assert cfg.s3_host == "localhost"
    assert cfg.s3_port == 9000
    assert cfg.region_name == "us-east-1"


def test_get_client_config_returns_expected_format() -> None:
    cfg = S3Config(
        s3_host="localhost",
        s3_port=9000,
        region_name="us-east-1",
        aws_access_key_id="user",
        aws_secret_access_key="pass",
    )

    expected_dict = {
        "endpoint_url": "http://localhost:9000",
        "aws_access_key_id": "user",
        "aws_secret_access_key": "pass",
        "region_name": "us-east-1",
    }

    assert cfg.get_client_config() == expected_dict
