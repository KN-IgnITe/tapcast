from pathlib import Path
from types import TracebackType
from typing import TYPE_CHECKING, Any

import boto3
from botocore.exceptions import ClientError

from ml_common.storage.exceptions import (
    StorageError,
    StorageObjectNotFoundError,
)
from ml_common.storage.s3_config import S3Config

if TYPE_CHECKING:
    from mypy_boto3_s3.client import S3Client as BotoS3Client
else:
    BotoS3Client = Any


class S3Client:
    """Small wrapper around boto3 S3 client."""

    def __init__(self, config: S3Config) -> None:
        self._config: S3Config = config
        self._client: BotoS3Client | None = None

    def connect(self) -> None:
        """Initialize the underlying boto3 client."""

        if self._client is None:
            self._client = boto3.client(
                "s3",
                **self._config.get_client_config(),
            )

    def close(self) -> None:
        self._client = None

    def __enter__(self) -> "S3Client":
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def upload_file(self, local_path: Path, key: str) -> None:
        """Upload a local file to the configured bucket."""

        client: BotoS3Client = self._get_client()

        try:
            client.upload_file(
                Filename=str(local_path),
                Bucket=self._config.bucket_name,
                Key=key,
            )
        except ClientError as error:
            raise StorageError(f"Failed to upload file to S3: {key}") from error

    def download_file(self, key: str, local_path: Path) -> None:
        """Download an object from S3 into a local file."""

        client: BotoS3Client = self._get_client()
        local_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            client.download_file(
                Bucket=self._config.bucket_name,
                Key=key,
                Filename=str(local_path),
            )
        except ClientError as error:
            if self._is_not_found(error):
                raise StorageObjectNotFoundError(
                    f"S3 object does not exist: {key}"
                ) from error

            raise StorageError(f"Failed to download file from S3: {key}") from error

    def upload_bytes(
        self,
        key: str,
        data: bytes,
        content_type: str | None = None,
    ) -> None:
        """Upload bytes directly to the configured bucket."""

        client: BotoS3Client = self._get_client()

        extra_args: dict[str, str] = {}

        if content_type is not None:
            extra_args["ContentType"] = content_type

        try:
            client.put_object(
                Bucket=self._config.bucket_name,
                Key=key,
                Body=data,
                **extra_args,
            )
        except ClientError as error:
            raise StorageError(f"Failed to upload bytes to S3: {key}") from error

    def download_bytes(self, key: str) -> bytes:
        """Download an object from S3 as bytes."""

        client: BotoS3Client = self._get_client()

        try:
            response = client.get_object(
                Bucket=self._config.bucket_name,
                Key=key,
            )
        except ClientError as error:
            if self._is_not_found(error):
                raise StorageObjectNotFoundError(
                    f"S3 object does not exist: {key}"
                ) from error

            raise StorageError(f"Failed to download bytes from S3: {key}") from error

        return response["Body"].read()

    def object_exists(self, key: str) -> bool:
        """Check whether an object exists in the configured bucket."""

        client: BotoS3Client = self._get_client()

        try:
            client.head_object(
                Bucket=self._config.bucket_name,
                Key=key,
            )
            return True
        except ClientError as error:
            if self._is_not_found(error):
                return False

            raise StorageError(f"Failed to check S3 object: {key}") from error

    def _get_client(self) -> BotoS3Client:
        self.connect()

        if self._client is None:
            raise StorageError("S3 client is not initialized.")

        return self._client

    def ensure_bucket_exists(self) -> None:
        """Create the configured bucket if it does not exist."""

        client: BotoS3Client = self._get_client()

        try:
            client.head_bucket(Bucket=self._config.bucket_name)
            return
        except ClientError as error:
            if not self._is_not_found(error):
                raise StorageError(
                    f"Failed to check S3 bucket: {self._config.bucket_name}"
                ) from error

        try:
            client.create_bucket(Bucket=self._config.bucket_name)
        except ClientError as error:
            raise StorageError(
                f"Failed to create S3 bucket: {self._config.bucket_name}"
            ) from error

    @staticmethod
    def _is_not_found(error: ClientError) -> bool:
        error_code: str = str(error.response.get("Error", {}).get("Code"))
        return error_code in {"404", "NoSuchKey", "NotFound"}
