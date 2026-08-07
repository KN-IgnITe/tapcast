import os
from pathlib import Path

from ml_common.artifacts.s3_model_bundle_store import S3ModelBundleStore
from ml_common.storage.s3_client import S3Client
from ml_common.storage.s3_config import S3Config

DEFAULT_MODEL_BUNDLE_S3_PREFIX = "demand-model/latest"


def download_model_bundle_from_s3(target_dir: Path) -> None:
    """Download production model bundle from S3-compatible storage."""

    prefix = os.getenv(
        "MODEL_BUNDLE_S3_PREFIX",
        DEFAULT_MODEL_BUNDLE_S3_PREFIX,
    )

    with S3Client(S3Config()) as s3_client:
        S3ModelBundleStore(s3_client).download_bundle_to_dir(
            target_dir=target_dir,
            prefix=prefix,
        )
