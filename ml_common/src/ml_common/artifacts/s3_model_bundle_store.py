from pathlib import Path
from typing import Iterable, Mapping

from ml_common.artifacts.model_bundle_files import (
    MODEL_BUNDLE_FILES,
    build_model_bundle_key,
)
from ml_common.storage.s3_client import S3Client


class S3ModelBundleStore:
    """Stores model bundle files in S3-compatible storage."""

    def __init__(self, client: S3Client) -> None:
        self._client: S3Client = client

    def upload_bundle_from_dir(self, source_dir: Path, prefix: str) -> None:
        """Upload model bundle files from a local directory."""

        for file_name in MODEL_BUNDLE_FILES:
            local_path: Path = source_dir / file_name

            if not local_path.exists():
                raise FileNotFoundError(f"Missing model bundle file {local_path}")

            self._client.upload_file(
                local_path=local_path,
                key=build_model_bundle_key(prefix, file_name),
            )

    def download_bundle_to_dir(self, target_dir: Path, prefix: str) -> None:
        """Download model bundle files into a local directory."""

        target_dir.mkdir(parents=True, exist_ok=True)

        for file_name in MODEL_BUNDLE_FILES:
            self._client.download_file(
                key=build_model_bundle_key(prefix, file_name),
                local_path=target_dir / file_name,
            )

    def upload_bundle_bytes(
        self,
        files: Mapping[str, bytes],
        prefix: str,
    ) -> None:
        """Upload model bundle files from memory."""

        self._validate_bundle_files(files.keys())

        for file_name in MODEL_BUNDLE_FILES:
            self._client.upload_bytes(
                key=build_model_bundle_key(prefix, file_name),
                data=files[file_name],
            )

    def download_bundle_bytes(self, prefix: str) -> dict[str, bytes]:
        """Download model bundle files into memory."""

        return {
            file_name: self._client.download_bytes(
                build_model_bundle_key(prefix, file_name)
            )
            for file_name in MODEL_BUNDLE_FILES
        }

    def bundle_exists(self, prefix: str) -> bool:
        """Check whether all expected model bundle files exist."""

        return all(
            self._client.object_exists(build_model_bundle_key(prefix, file_name))
            for file_name in MODEL_BUNDLE_FILES
        )

    @staticmethod
    def _validate_bundle_files(file_names: Iterable[str]) -> None:
        missing_files: set[str] = set(MODEL_BUNDLE_FILES) - set(file_names)

        if missing_files:
            raise ValueError(f"Missing model bundle files: {sorted(missing_files)}")
