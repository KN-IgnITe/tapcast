import boto3
from botocore.exceptions import ClientError
from types import TracebackType
from typing import Optional, Any

from inference.database.s3_config import S3Config


class S3Client:
    def __init__(self, config: S3Config) -> None:
        self._config: S3Config = config
        self._client: Optional[Any] = None

    def connect(self) -> bool:
        """
        Initializes the S3 client if it does not exist yet.
        """
        if self._client is None:
            try:
                self._client = boto3.client("s3", **self._config.get_client_config())
                return True
            except ClientError as e:
                print(f"S3 Connection error: {e}")
                self._client = None
                raise
        return True

    def close(self) -> None:
        """
        Clears the client reference.
        """
        self._client = None

    def __enter__(self) -> "S3Client":
        """Called at the beginning of the 'with' block."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if exc_type:
            print(f"An error occurred during S3 operation: {exc_val}")
        self.close()
