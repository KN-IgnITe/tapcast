from unittest.mock import MagicMock
import boto3
from botocore.exceptions import ClientError
import pytest

from inference.database.s3_client import S3Client
from inference.database.s3_config import S3Config


@pytest.fixture
def s3_config() -> S3Config:
    return S3Config(
        s3_host="localhost",
        s3_port=9000,
        region_name="us-east-1",
        aws_access_key_id="minio_user",
        aws_secret_access_key="minio_pass",
    )


def test_connect_opens_connection_when_missing(
    monkeypatch: pytest.MonkeyPatch, s3_config: S3Config
) -> None:
    client_mock_instance = MagicMock()

    boto_client_mock = MagicMock(return_value=client_mock_instance)
    monkeypatch.setattr(boto3, "client", boto_client_mock)

    client = S3Client(s3_config)
    result = client.connect()

    assert result is True
    boto_client_mock.assert_called_once_with("s3", **s3_config.get_client_config())


def test_connect_reraises_client_errors(
    monkeypatch: pytest.MonkeyPatch, s3_config: S3Config
) -> None:
    # Simulating connection error using ClientError structure
    error_response = {"Error": {"Code": "ConnectionError", "Message": "boom"}}
    boto_client_mock = MagicMock(
        side_effect=ClientError(error_response, "list_buckets")
    )
    monkeypatch.setattr(boto3, "client", boto_client_mock)

    client = S3Client(s3_config)

    with pytest.raises(ClientError):
        client.connect()


def test_close_clears_open_connection(s3_config: S3Config) -> None:
    client = S3Client(s3_config)
    client._client = MagicMock()

    client.close()

    assert client._client is None


def test_enter_connects_and_returns_client(
    monkeypatch: pytest.MonkeyPatch, s3_config: S3Config
) -> None:
    client = S3Client(s3_config)

    connect_mock = MagicMock(return_value=True)
    monkeypatch.setattr(client, "connect", connect_mock)

    returned = client.__enter__()

    connect_mock.assert_called_once_with()
    assert returned is client


def test_exit_closes_connection(
    monkeypatch: pytest.MonkeyPatch, s3_config: S3Config
) -> None:
    client = S3Client(s3_config)

    close_mock = MagicMock()
    monkeypatch.setattr(client, "close", close_mock)

    client.__exit__(None, None, None)

    close_mock.assert_called_once_with()
