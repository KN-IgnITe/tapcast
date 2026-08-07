from pathlib import Path
from typing import Any, cast

import pytest
from ml_common.artifacts.model_bundle_files import (
    CLEANER_ARTIFACTS_FILE,
    METADATA_FILE,
    MODEL_BUNDLE_FILES,
    MODEL_FILE,
    PREPROCESSOR_FILE,
    build_model_bundle_key,
)
from ml_common.artifacts.s3_model_bundle_store import S3ModelBundleStore
from ml_common.storage.s3_client import S3Client


@pytest.fixture
def bundle_dir(tmp_path: Path) -> Path:
    for file_name in MODEL_BUNDLE_FILES:
        (tmp_path / file_name).write_bytes(f"content-{file_name}".encode())

    return tmp_path


def test_upload_bundle_from_dir_uploads_all_bundle_files(
    fake_s3_storage_client: Any,
    bundle_dir: Path,
) -> None:
    store = _create_store(fake_s3_storage_client)

    store.upload_bundle_from_dir(
        source_dir=bundle_dir,
        prefix="demand-model/latest",
    )

    assert fake_s3_storage_client.uploaded_files == [
        (
            bundle_dir / file_name,
            build_model_bundle_key("demand-model/latest", file_name),
        )
        for file_name in MODEL_BUNDLE_FILES
    ]


def test_upload_bundle_from_dir_raises_when_file_is_missing(
    fake_s3_storage_client: Any,
    bundle_dir: Path,
) -> None:
    (bundle_dir / MODEL_FILE).unlink()
    store = _create_store(fake_s3_storage_client)

    with pytest.raises(FileNotFoundError, match=MODEL_FILE):
        store.upload_bundle_from_dir(
            source_dir=bundle_dir,
            prefix="demand-model/latest",
        )


def test_download_bundle_to_dir_downloads_all_bundle_files(
    fake_s3_storage_client: Any,
    tmp_path: Path,
) -> None:
    prefix = "demand-model/latest"

    for file_name in MODEL_BUNDLE_FILES:
        fake_s3_storage_client.objects[build_model_bundle_key(prefix, file_name)] = (
            f"content-{file_name}".encode()
        )

    store = _create_store(fake_s3_storage_client)
    target_dir = tmp_path / "downloaded"

    store.download_bundle_to_dir(
        target_dir=target_dir,
        prefix=prefix,
    )

    assert {path.name for path in target_dir.iterdir()} == set(MODEL_BUNDLE_FILES)
    assert (target_dir / MODEL_FILE).read_bytes() == b"content-xgb_model.json"


def test_upload_bundle_bytes_uploads_all_bundle_files(
    fake_s3_storage_client: Any,
) -> None:
    store = _create_store(fake_s3_storage_client)
    files = _bundle_bytes()

    store.upload_bundle_bytes(
        files=files,
        prefix="demand-model/latest",
    )

    assert fake_s3_storage_client.uploaded_bytes == [
        (
            build_model_bundle_key("demand-model/latest", file_name),
            files[file_name],
        )
        for file_name in MODEL_BUNDLE_FILES
    ]


def test_upload_bundle_bytes_raises_when_file_is_missing(
    fake_s3_storage_client: Any,
) -> None:
    store = _create_store(fake_s3_storage_client)
    files = {
        MODEL_FILE: b"model",
        PREPROCESSOR_FILE: b"preprocessor",
        CLEANER_ARTIFACTS_FILE: b"cleaner",
    }

    with pytest.raises(ValueError, match=METADATA_FILE):
        store.upload_bundle_bytes(
            files=files,
            prefix="demand-model/latest",
        )


def test_download_bundle_bytes_returns_all_bundle_files(
    fake_s3_storage_client: Any,
) -> None:
    prefix = "demand-model/latest"

    for file_name in MODEL_BUNDLE_FILES:
        fake_s3_storage_client.objects[build_model_bundle_key(prefix, file_name)] = (
            f"content-{file_name}".encode()
        )

    store = _create_store(fake_s3_storage_client)

    result = store.download_bundle_bytes(prefix)

    assert result == {
        file_name: f"content-{file_name}".encode() for file_name in MODEL_BUNDLE_FILES
    }


def test_bundle_exists_returns_true_when_all_files_exist(
    fake_s3_storage_client: Any,
) -> None:
    prefix = "demand-model/latest"

    for file_name in MODEL_BUNDLE_FILES:
        fake_s3_storage_client.objects[build_model_bundle_key(prefix, file_name)] = (
            b"data"
        )

    store = _create_store(fake_s3_storage_client)

    assert store.bundle_exists(prefix) is True


def test_bundle_exists_returns_false_when_any_file_is_missing(
    fake_s3_storage_client: Any,
) -> None:
    prefix = "demand-model/latest"

    for file_name in MODEL_BUNDLE_FILES[:-1]:
        fake_s3_storage_client.objects[build_model_bundle_key(prefix, file_name)] = (
            b"data"
        )

    store = _create_store(fake_s3_storage_client)

    assert store.bundle_exists(prefix) is False


def _bundle_bytes() -> dict[str, bytes]:
    return {
        MODEL_FILE: b"model",
        PREPROCESSOR_FILE: b"preprocessor",
        CLEANER_ARTIFACTS_FILE: b"cleaner",
        METADATA_FILE: b"metadata",
    }


def _create_store(fake_s3_storage_client: Any) -> S3ModelBundleStore:
    return S3ModelBundleStore(cast(S3Client, fake_s3_storage_client))
