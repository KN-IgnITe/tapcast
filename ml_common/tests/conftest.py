from pathlib import Path
from typing import Any

import pytest
from botocore.exceptions import ClientError


class FakeBody:
    """Minimal response body fake for boto3 get_object."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class FakeS3StorageClient:
    """Fake S3 client used by storage and artifact tests."""

    def __init__(self) -> None:
        self.upload_file_calls: list[dict[str, Any]] = []
        self.download_file_calls: list[dict[str, Any]] = []
        self.uploaded_files: list[tuple[Path, str]] = []
        self.downloaded_files: list[tuple[str, Path]] = []
        self.uploaded_bytes: list[tuple[str, bytes]] = []
        self.put_object_calls: list[dict[str, Any]] = []
        self.get_object_calls: list[dict[str, Any]] = []
        self.head_object_calls: list[dict[str, Any]] = []
        self.objects: dict[str, bytes] = {}
        self.raise_on_download_file = False

    def upload_file(self, **kwargs: Any) -> None:
        if "local_path" in kwargs:
            local_path = Path(str(kwargs["local_path"]))
            key = str(kwargs["key"])
            self.uploaded_files.append((local_path, key))

            if local_path.exists():
                self.objects[key] = local_path.read_bytes()

            return

        self.upload_file_calls.append(kwargs)

        key = str(kwargs["Key"])
        local_path = Path(str(kwargs["Filename"]))

        if local_path.exists():
            self.objects[key] = local_path.read_bytes()

    def download_file(self, **kwargs: Any) -> None:
        if self.raise_on_download_file:
            raise_not_found_error()

        if "local_path" in kwargs:
            key = str(kwargs["key"])
            local_path = Path(str(kwargs["local_path"]))
            self.downloaded_files.append((key, local_path))

            if key not in self.objects:
                raise_not_found_error()

            local_path.write_bytes(self.objects[key])
            return

        self.download_file_calls.append(kwargs)

        key = str(kwargs["Key"])
        local_path = Path(str(kwargs["Filename"]))

        if key in self.objects:
            local_path.write_bytes(self.objects[key])

    def upload_bytes(self, key: str, data: bytes) -> None:
        self.uploaded_bytes.append((key, data))
        self.objects[key] = data

    def download_bytes(self, key: str) -> bytes:
        if key not in self.objects:
            raise_not_found_error()

        return self.objects[key]

    def object_exists(self, key: str) -> bool:
        return key in self.objects

    def put_object(self, **kwargs: Any) -> None:
        self.put_object_calls.append(kwargs)
        self.objects[str(kwargs["Key"])] = kwargs["Body"]

    def get_object(self, **kwargs: Any) -> dict[str, FakeBody]:
        self.get_object_calls.append(kwargs)

        key = str(kwargs["Key"])
        if key not in self.objects:
            raise_not_found_error()

        return {"Body": FakeBody(self.objects[key])}

    def head_object(self, **kwargs: Any) -> None:
        self.head_object_calls.append(kwargs)

        key = str(kwargs["Key"])
        if key not in self.objects:
            raise_not_found_error()


@pytest.fixture
def fake_s3_storage_client() -> FakeS3StorageClient:
    return FakeS3StorageClient()


def raise_not_found_error() -> None:
    raise ClientError(
        error_response={"Error": {"Code": "NoSuchKey"}},
        operation_name="GetObject",
    )
